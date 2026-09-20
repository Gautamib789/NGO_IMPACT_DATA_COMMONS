import os
import uuid
import json
import hashlib
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.models.ngo import NGODetail
from app.models.project import Project
from app.models.beneficiary import Beneficiary
from app.models.expense import Expense
from app.models.audit import AuditLog
from app.schemas.project_tracking import (
    ProjectCreate, ProjectUpdate, ProjectOut,
    BeneficiaryCreate, BeneficiaryOut,
    ExpenseCreate, ExpenseOut
)
from app.dependencies import require_roles
from app.services.fraud_engine import FraudDetectionEngine

router = APIRouter(prefix="/api/ngo", tags=["NGO Project & Expense Tracking"])

UPLOAD_DIR = r"E:\NGO\uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _get_authenticated_ngo(current_user: User, db: Session) -> NGODetail:
    ngo = db.query(NGODetail).filter(NGODetail.user_id == current_user.id).first()
    if not ngo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NGO profile not found for the authenticated user."
        )
    return ngo


def _build_project_out(project: Project, db: Session) -> ProjectOut:
    total_expenses = db.query(Expense).filter(Expense.project_id == project.id).all()
    claimed_sum = sum(e.amount for e in total_expenses) if total_expenses else 0.0
    utilization_ratio = round((claimed_sum / project.budget) * 100.0, 2) if project.budget > 0 else 0.0
    b_count = db.query(Beneficiary).filter(Beneficiary.project_id == project.id).count()

    return ProjectOut(
        id=project.id,
        ngo_id=project.ngo_id,
        project_name=project.project_name,
        description=project.description,
        category=project.category,
        location=project.location,
        latitude=project.latitude,
        longitude=project.longitude,
        start_date=project.start_date,
        end_date=project.end_date,
        budget=project.budget,
        target_beneficiaries=project.target_beneficiaries,
        total_expenses_claimed=claimed_sum,
        fund_utilization_ratio=utilization_ratio,
        beneficiary_count=b_count,
        outcomes=project.outcomes,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at
    )


# ==========================================
# 1. PROJECT MANAGEMENT ENDPOINTS
# ==========================================

@router.post("/projects", response_model=ProjectOut)
def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(require_roles([UserRole.NGO])),
    db: Session = Depends(get_db)
):
    ngo = _get_authenticated_ngo(current_user, db)

    if project_in.budget <= 0:
        raise HTTPException(status_code=400, detail="Project budget must be greater than zero.")

    new_project = Project(
        ngo_id=ngo.id,
        project_name=project_in.project_name.strip(),
        description=project_in.description,
        category=project_in.category.strip(),
        location=project_in.location,
        latitude=project_in.latitude,
        longitude=project_in.longitude,
        start_date=project_in.start_date,
        end_date=project_in.end_date,
        budget=project_in.budget,
        target_beneficiaries=project_in.target_beneficiaries,
        outcomes=project_in.outcomes,
        status="ACTIVE"
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    # Record Audit Log
    audit = AuditLog(
        actor_user_id=current_user.id,
        ngo_id=ngo.id,
        action="CREATE_PROJECT",
        entity_type="PROJECT",
        entity_id=new_project.id,
        metadata_json=json.dumps({"project_name": new_project.project_name, "budget": new_project.budget})
    )
    db.add(audit)
    db.commit()

    return _build_project_out(new_project, db)


@router.get("/projects", response_model=List[ProjectOut])
def list_ngo_projects(
    current_user: User = Depends(require_roles([UserRole.NGO])),
    db: Session = Depends(get_db)
):
    ngo = _get_authenticated_ngo(current_user, db)
    projects = db.query(Project).filter(Project.ngo_id == ngo.id).order_by(Project.created_at.desc()).all()
    return [_build_project_out(p, db) for p in projects]


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project_details(
    project_id: int,
    current_user: User = Depends(require_roles([UserRole.NGO])),
    db: Session = Depends(get_db)
):
    ngo = _get_authenticated_ngo(current_user, db)
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.ngo_id != ngo.id:
        raise HTTPException(status_code=403, detail="Access denied. Project belongs to another NGO.")

    return _build_project_out(project, db)


@router.put("/projects/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    current_user: User = Depends(require_roles([UserRole.NGO])),
    db: Session = Depends(get_db)
):
    ngo = _get_authenticated_ngo(current_user, db)
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.ngo_id != ngo.id:
        raise HTTPException(status_code=403, detail="Access denied. Project belongs to another NGO.")

    if project_in.budget is not None:
        if project_in.budget <= 0:
            raise HTTPException(status_code=400, detail="Project budget must be greater than zero.")
        project.budget = project_in.budget

    if project_in.project_name is not None:
        project.project_name = project_in.project_name.strip()
    if project_in.description is not None:
        project.description = project_in.description
    if project_in.category is not None:
        project.category = project_in.category.strip()
    if project_in.location is not None:
        project.location = project_in.location
    if project_in.latitude is not None:
        project.latitude = project_in.latitude
    if project_in.longitude is not None:
        project.longitude = project_in.longitude
    if project_in.target_beneficiaries is not None:
        project.target_beneficiaries = project_in.target_beneficiaries
    if project_in.outcomes is not None:
        project.outcomes = project_in.outcomes
    if project_in.status is not None:
        project.status = project_in.status.upper()

    project.updated_at = datetime.utcnow()
    db.commit()

    # Record Audit Log
    audit = AuditLog(
        actor_user_id=current_user.id,
        ngo_id=ngo.id,
        action="UPDATE_PROJECT",
        entity_type="PROJECT",
        entity_id=project.id,
        metadata_json=json.dumps({"project_name": project.project_name, "updated_fields": list(project_in.dict(exclude_unset=True).keys())})
    )
    db.add(audit)
    db.commit()

    db.refresh(project)
    return _build_project_out(project, db)


@router.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    current_user: User = Depends(require_roles([UserRole.NGO])),
    db: Session = Depends(get_db)
):
    ngo = _get_authenticated_ngo(current_user, db)
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.ngo_id != ngo.id:
        raise HTTPException(status_code=403, detail="Access denied. Project belongs to another NGO.")

    p_name = project.project_name
    db.delete(project)
    db.commit()

    # Record Audit Log
    audit = AuditLog(
        actor_user_id=current_user.id,
        ngo_id=ngo.id,
        action="DELETE_PROJECT",
        entity_type="PROJECT",
        entity_id=project_id,
        metadata_json=json.dumps({"project_name": p_name})
    )
    db.add(audit)
    db.commit()

    return {"message": f"Project '{p_name}' deleted successfully."}


# ==========================================
# 2. BENEFICIARY MANAGEMENT ENDPOINTS
# ==========================================

@router.post("/beneficiaries", response_model=BeneficiaryOut)
def create_beneficiary(
    b_in: BeneficiaryCreate,
    current_user: User = Depends(require_roles([UserRole.NGO])),
    db: Session = Depends(get_db)
):
    ngo = _get_authenticated_ngo(current_user, db)

    # Validate project ownership if provided
    project_name = None
    if b_in.project_id:
        proj = db.query(Project).filter(Project.id == b_in.project_id).first()
        if not proj or proj.ngo_id != ngo.id:
            raise HTTPException(status_code=403, detail="Access denied. Project does not belong to your NGO.")
        project_name = proj.project_name

    # Generate masked fictional identifier if omitted
    code = b_in.beneficiary_code
    if not code:
        rand_str = uuid.uuid4().hex[:6].upper()
        code = f"BEN-{datetime.utcnow().year}-{rand_str}"

    new_b = Beneficiary(
        ngo_id=ngo.id,
        project_id=b_in.project_id,
        beneficiary_code=code,
        name_or_alias=b_in.name_or_alias.strip(),
        age_group=b_in.age_group,
        gender=b_in.gender,
        location=b_in.location
    )
    db.add(new_b)
    
    # Update NGO beneficiary count
    ngo.beneficiary_count = (ngo.beneficiary_count or 0) + 1
    db.commit()
    db.refresh(new_b)

    # Record Audit Log
    audit = AuditLog(
        actor_user_id=current_user.id,
        ngo_id=ngo.id,
        action="CREATE_BENEFICIARY",
        entity_type="BENEFICIARY",
        entity_id=new_b.id,
        metadata_json=json.dumps({"code": new_b.beneficiary_code, "alias": new_b.name_or_alias})
    )
    db.add(audit)
    db.commit()

    return BeneficiaryOut(
        id=new_b.id,
        ngo_id=new_b.ngo_id,
        project_id=new_b.project_id,
        project_name=project_name,
        beneficiary_code=new_b.beneficiary_code,
        name_or_alias=new_b.name_or_alias,
        age_group=new_b.age_group,
        gender=new_b.gender,
        location=new_b.location,
        created_at=new_b.created_at
    )


@router.get("/beneficiaries", response_model=List[BeneficiaryOut])
def list_beneficiaries(
    project_id: Optional[int] = Query(None),
    current_user: User = Depends(require_roles([UserRole.NGO])),
    db: Session = Depends(get_db)
):
    ngo = _get_authenticated_ngo(current_user, db)
    query = db.query(Beneficiary).filter(Beneficiary.ngo_id == ngo.id)
    if project_id:
        query = query.filter(Beneficiary.project_id == project_id)

    b_list = query.order_by(Beneficiary.created_at.desc()).all()
    res = []
    for b in b_list:
        proj_name = b.project.project_name if b.project else None
        res.append(BeneficiaryOut(
            id=b.id,
            ngo_id=b.ngo_id,
            project_id=b.project_id,
            project_name=proj_name,
            beneficiary_code=b.beneficiary_code,
            name_or_alias=b.name_or_alias,
            age_group=b.age_group,
            gender=b.gender,
            location=b.location,
            created_at=b.created_at
        ))
    return res


@router.get("/beneficiaries/{beneficiary_id}", response_model=BeneficiaryOut)
def get_beneficiary_details(
    beneficiary_id: int,
    current_user: User = Depends(require_roles([UserRole.NGO])),
    db: Session = Depends(get_db)
):
    ngo = _get_authenticated_ngo(current_user, db)
    b = db.query(Beneficiary).filter(Beneficiary.id == beneficiary_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Beneficiary record not found")

    if b.ngo_id != ngo.id:
        raise HTTPException(status_code=403, detail="Access denied. Beneficiary belongs to another NGO.")

    proj_name = b.project.project_name if b.project else None
    return BeneficiaryOut(
        id=b.id,
        ngo_id=b.ngo_id,
        project_id=b.project_id,
        project_name=proj_name,
        beneficiary_code=b.beneficiary_code,
        name_or_alias=b.name_or_alias,
        age_group=b.age_group,
        gender=b.gender,
        location=b.location,
        created_at=b.created_at
    )


@router.delete("/beneficiaries/{beneficiary_id}")
def delete_beneficiary(
    beneficiary_id: int,
    current_user: User = Depends(require_roles([UserRole.NGO])),
    db: Session = Depends(get_db)
):
    ngo = _get_authenticated_ngo(current_user, db)
    b = db.query(Beneficiary).filter(Beneficiary.id == beneficiary_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Beneficiary record not found")

    if b.ngo_id != ngo.id:
        raise HTTPException(status_code=403, detail="Access denied. Beneficiary belongs to another NGO.")

    b_code = b.beneficiary_code
    db.delete(b)
    ngo.beneficiary_count = max(0, (ngo.beneficiary_count or 1) - 1)
    db.commit()

    # Record Audit Log
    audit = AuditLog(
        actor_user_id=current_user.id,
        ngo_id=ngo.id,
        action="DELETE_BENEFICIARY",
        entity_type="BENEFICIARY",
        entity_id=beneficiary_id,
        metadata_json=json.dumps({"code": b_code})
    )
    db.add(audit)
    db.commit()

    return {"message": f"Beneficiary record '{b_code}' deleted successfully."}


# ==========================================
# 3. EXPENSE & RECEIPT MANAGEMENT ENDPOINTS
# ==========================================

@router.post("/expenses", response_model=ExpenseOut)
def create_expense(
    expense_in: ExpenseCreate,
    current_user: User = Depends(require_roles([UserRole.NGO])),
    db: Session = Depends(get_db)
):
    ngo = _get_authenticated_ngo(current_user, db)

    if expense_in.amount <= 0:
        raise HTTPException(status_code=400, detail="Expense amount must be greater than zero.")

    proj_name = None
    if expense_in.project_id:
        proj = db.query(Project).filter(Project.id == expense_in.project_id).first()
        if not proj or proj.ngo_id != ngo.id:
            raise HTTPException(status_code=403, detail="Access denied. Project does not belong to your NGO.")
        proj_name = proj.project_name

    new_exp = Expense(
        ngo_id=ngo.id,
        project_id=expense_in.project_id,
        category=expense_in.category.strip(),
        description=expense_in.description,
        amount=expense_in.amount,
        verification_status="PENDING"
    )
    db.add(new_exp)

    # Recalculate NGO total expenses
    all_ngo_expenses = db.query(Expense).filter(Expense.ngo_id == ngo.id).all()
    ngo.total_expenses = sum(e.amount for e in all_ngo_expenses) + expense_in.amount
    db.commit()
    db.refresh(new_exp)

    # Re-scan fraud engine for updated metrics
    FraudDetectionEngine.scan_ngo(db, ngo.id)

    # Record Audit Log
    audit = AuditLog(
        actor_user_id=current_user.id,
        ngo_id=ngo.id,
        action="CREATE_EXPENSE",
        entity_type="EXPENSE",
        entity_id=new_exp.id,
        metadata_json=json.dumps({"amount": new_exp.amount, "category": new_exp.category})
    )
    db.add(audit)
    db.commit()

    return ExpenseOut(
        id=new_exp.id,
        ngo_id=new_exp.ngo_id,
        project_id=new_exp.project_id,
        project_name=proj_name,
        category=new_exp.category,
        description=new_exp.description,
        amount=new_exp.amount,
        expense_date=new_exp.expense_date,
        receipt_file_name=new_exp.receipt_file_name,
        receipt_file_path=new_exp.receipt_file_path,
        receipt_sha256=new_exp.receipt_sha256,
        verification_status=new_exp.verification_status,
        created_at=new_exp.created_at
    )


@router.post("/expenses/{expense_id}/upload-receipt", response_model=ExpenseOut)
def upload_expense_receipt(
    expense_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles([UserRole.NGO])),
    db: Session = Depends(get_db)
):
    ngo = _get_authenticated_ngo(current_user, db)
    exp = db.query(Expense).filter(Expense.id == expense_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense record not found")

    if exp.ngo_id != ngo.id:
        raise HTTPException(status_code=403, detail="Access denied. Expense belongs to another NGO.")

    contents = file.file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded receipt file is empty.")

    sha256_hash = hashlib.sha256(contents).hexdigest()
    file_ext = os.path.splitext(file.filename)[1] or ".bin"
    unique_filename = f"receipt_ngo{ngo.id}_exp{exp.id}_{uuid.uuid4().hex[:8]}{file_ext}"
    dest_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(dest_path, "wb") as f:
        f.write(contents)

    exp.receipt_file_name = file.filename
    exp.receipt_file_path = f"/uploads/{unique_filename}"
    exp.receipt_sha256 = sha256_hash
    exp.verification_status = "VERIFIED"
    exp.updated_at = datetime.utcnow()
    db.commit()

    # Record Audit Log
    audit = AuditLog(
        actor_user_id=current_user.id,
        ngo_id=ngo.id,
        action="UPLOAD_EXPENSE_RECEIPT",
        entity_type="EXPENSE",
        entity_id=exp.id,
        metadata_json=json.dumps({"sha256": sha256_hash, "file_name": file.filename})
    )
    db.add(audit)
    db.commit()

    db.refresh(exp)
    proj_name = exp.project.project_name if exp.project else None
    return ExpenseOut(
        id=exp.id,
        ngo_id=exp.ngo_id,
        project_id=exp.project_id,
        project_name=proj_name,
        category=exp.category,
        description=exp.description,
        amount=exp.amount,
        expense_date=exp.expense_date,
        receipt_file_name=exp.receipt_file_name,
        receipt_file_path=exp.receipt_file_path,
        receipt_sha256=exp.receipt_sha256,
        verification_status=exp.verification_status,
        created_at=exp.created_at
    )


@router.get("/expenses", response_model=List[ExpenseOut])
def list_expenses(
    project_id: Optional[int] = Query(None),
    current_user: User = Depends(require_roles([UserRole.NGO])),
    db: Session = Depends(get_db)
):
    ngo = _get_authenticated_ngo(current_user, db)
    query = db.query(Expense).filter(Expense.ngo_id == ngo.id)
    if project_id:
        query = query.filter(Expense.project_id == project_id)

    expenses = query.order_by(Expense.expense_date.desc()).all()
    res = []
    for exp in expenses:
        proj_name = exp.project.project_name if exp.project else None
        res.append(ExpenseOut(
            id=exp.id,
            ngo_id=exp.ngo_id,
            project_id=exp.project_id,
            project_name=proj_name,
            category=exp.category,
            description=exp.description,
            amount=exp.amount,
            expense_date=exp.expense_date,
            receipt_file_name=exp.receipt_file_name,
            receipt_file_path=exp.receipt_file_path,
            receipt_sha256=exp.receipt_sha256,
            verification_status=exp.verification_status,
            created_at=exp.created_at
        ))
    return res


@router.get("/expenses/{expense_id}", response_model=ExpenseOut)
def get_expense_details(
    expense_id: int,
    current_user: User = Depends(require_roles([UserRole.NGO])),
    db: Session = Depends(get_db)
):
    ngo = _get_authenticated_ngo(current_user, db)
    exp = db.query(Expense).filter(Expense.id == expense_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense record not found")

    if exp.ngo_id != ngo.id:
        raise HTTPException(status_code=403, detail="Access denied. Expense belongs to another NGO.")

    proj_name = exp.project.project_name if exp.project else None
    return ExpenseOut(
        id=exp.id,
        ngo_id=exp.ngo_id,
        project_id=exp.project_id,
        project_name=proj_name,
        category=exp.category,
        description=exp.description,
        amount=exp.amount,
        expense_date=exp.expense_date,
        receipt_file_name=exp.receipt_file_name,
        receipt_file_path=exp.receipt_file_path,
        receipt_sha256=exp.receipt_sha256,
        verification_status=exp.verification_status,
        created_at=exp.created_at
    )


@router.delete("/expenses/{expense_id}")
def delete_expense(
    expense_id: int,
    current_user: User = Depends(require_roles([UserRole.NGO])),
    db: Session = Depends(get_db)
):
    ngo = _get_authenticated_ngo(current_user, db)
    exp = db.query(Expense).filter(Expense.id == expense_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense record not found")

    if exp.ngo_id != ngo.id:
        raise HTTPException(status_code=403, detail="Access denied. Expense belongs to another NGO.")

    exp_amt = exp.amount
    db.delete(exp)
    
    # Recalculate NGO total expenses
    all_ngo_expenses = db.query(Expense).filter(Expense.ngo_id == ngo.id).all()
    ngo.total_expenses = sum(e.amount for e in all_ngo_expenses)
    db.commit()

    # Record Audit Log
    audit = AuditLog(
        actor_user_id=current_user.id,
        ngo_id=ngo.id,
        action="DELETE_EXPENSE",
        entity_type="EXPENSE",
        entity_id=expense_id,
        metadata_json=json.dumps({"amount": exp_amt})
    )
    db.add(audit)
    db.commit()

    return {"message": "Expense record deleted successfully."}
