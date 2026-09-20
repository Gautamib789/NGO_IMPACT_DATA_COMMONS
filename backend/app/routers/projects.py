import os
import json
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.ngo import NGODetail
from app.models.project import (
    Project, ProjectEvidence, ProjectExpense, ProjectRiskAnalysis,
    ProjectFinding, AdminNotification
)
from app.models.audit import AuditLog
from app.services.document_tamper_engine import DocumentTamperEngine
from app.services.project_integrity_engine import ProjectIntegrityEngine

from app.schemas.project import ProjectCreateSchema, ExpenseCreateSchema, ProjectOutSchema

router = APIRouter(prefix="/api/ngo/projects", tags=["NGO Projects"])

UPLOAD_DIR = "uploads/projects"
os.makedirs(UPLOAD_DIR, exist_ok=True)



def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        try:
            return datetime.fromisoformat(date_str)
        except ValueError:
            return None


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ProjectOutSchema)
def create_project(
    project_in: ProjectCreateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.ngo_detail:
        raise HTTPException(status_code=400, detail="User must have an associated NGO profile")
    
    ngo = current_user.ngo_detail

    # 1. Budget validation
    req_budget = project_in.budget if project_in.budget is not None else project_in.total_budget
    if req_budget is not None and req_budget <= 0:
        raise HTTPException(status_code=422, detail="Budget must be greater than 0")
    final_budget = float(req_budget or 0.0)

    # 2. Date range validation
    s_date = parse_date(project_in.start_date)
    e_date = parse_date(project_in.end_date)
    if s_date and e_date and e_date < s_date:
        raise HTTPException(status_code=422, detail="End date cannot be before start date")

    # 3. Beneficiaries calculation
    num_ben = project_in.number_of_beneficiaries
    if num_ben is None and project_in.target_beneficiaries is not None:
        try:
            num_ben = int(project_in.target_beneficiaries)
        except (ValueError, TypeError):
            num_ben = 0
    num_ben = num_ben or 0
    if num_ben < 0:
        raise HTTPException(status_code=422, detail="Beneficiary count cannot be negative")

    target_ben_str = str(project_in.target_beneficiaries) if project_in.target_beneficiaries is not None else str(num_ben)
    objective_text = project_in.objective or project_in.outcomes

    project = Project(
        ngo_id=ngo.id,
        project_name=project_in.project_name.strip(),
        description=project_in.description,
        category=project_in.category or "General",
        location=project_in.location,
        latitude=project_in.latitude,
        longitude=project_in.longitude,
        start_date=s_date,
        end_date=e_date,
        objective=objective_text,
        target_beneficiaries=target_ben_str,
        number_of_beneficiaries=num_ben,
        total_budget=final_budget,
        funding_received=project_in.funding_received or 0.0,
        amount_spent=0.0,
        remaining_amount=final_budget,
        ngo_contribution=project_in.ngo_contribution or 0.0,
        donor_funding=project_in.donor_funding or 0.0,
        government_funding=project_in.government_funding or 0.0,
        contact_person=project_in.contact_person,
        status=project_in.status or "ACTIVE",
        integrity_status="VERIFIED",
        risk_score=0.0,
        risk_level="LOW"
    )

    db.add(project)
    db.commit()
    db.refresh(project)
    
    # Audit log
    audit = AuditLog(
        actor_user_id=current_user.id,
        ngo_id=ngo.id,
        action="PROJECT_CREATE",
        entity_type="PROJECT",
        entity_id=project.id,
        metadata_json=f'{{"project_name": "{project.project_name}", "budget": {project.total_budget}}}'
    )
    db.add(audit)
    db.commit()

    return project


@router.get("", response_model=List[ProjectOutSchema])
def list_ngo_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.ngo_detail:
        raise HTTPException(status_code=400, detail="User must have an associated NGO profile")
    
    projects = db.query(Project).filter(Project.ngo_id == current_user.ngo_detail.id).order_by(Project.created_at.desc()).all()
    return projects


@router.put("/{project_id}", response_model=ProjectOutSchema)
def update_project(
    project_id: int,
    project_in: ProjectCreateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.ngo_detail:
        raise HTTPException(status_code=400, detail="User must have an associated NGO profile")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.ngo_id != current_user.ngo_detail.id:
        raise HTTPException(status_code=403, detail="Access denied: You cannot edit another NGO's project")

    req_budget = project_in.budget if project_in.budget is not None else project_in.total_budget
    if req_budget is not None and req_budget <= 0:
        raise HTTPException(status_code=422, detail="Budget must be greater than 0")
    
    s_date = parse_date(project_in.start_date)
    e_date = parse_date(project_in.end_date)
    if s_date and e_date and e_date < s_date:
        raise HTTPException(status_code=422, detail="End date cannot be before start date")

    if req_budget is not None:
        project.total_budget = float(req_budget)
        project.remaining_amount = float(req_budget) - (project.amount_spent or 0.0)

    project.project_name = project_in.project_name.strip()
    if project_in.description is not None:
        project.description = project_in.description
    if project_in.category:
        project.category = project_in.category
    if project_in.location is not None:
        project.location = project_in.location
    if project_in.latitude is not None:
        project.latitude = project_in.latitude
    if project_in.longitude is not None:
        project.longitude = project_in.longitude
    if s_date:
        project.start_date = s_date
    if e_date:
        project.end_date = e_date
    if project_in.objective or project_in.outcomes:
        project.objective = project_in.objective or project_in.outcomes
    if project_in.status:
        project.status = project_in.status
    if project_in.number_of_beneficiaries is not None:
        project.number_of_beneficiaries = project_in.number_of_beneficiaries
    elif project_in.target_beneficiaries is not None:
        try:
            project.number_of_beneficiaries = int(project_in.target_beneficiaries)
        except (ValueError, TypeError):
            pass

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.ngo_detail:
        raise HTTPException(status_code=400, detail="User must have an associated NGO profile")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.ngo_id != current_user.ngo_detail.id:
        raise HTTPException(status_code=403, detail="Access denied: You cannot delete another NGO's project")

    db.delete(project)
    db.commit()
    return {"message": "Project deleted successfully"}



@router.get("/{project_id}")
def get_project_detail(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.ngo_detail:
        raise HTTPException(status_code=400, detail="User must have an associated NGO profile")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.ngo_id != current_user.ngo_detail.id:
        raise HTTPException(status_code=403, detail="Access denied: You cannot view another NGO's project")

    evidence = db.query(ProjectEvidence).filter(ProjectEvidence.project_id == project_id).all()
    expenses = db.query(ProjectExpense).filter(ProjectExpense.project_id == project_id).all()
    findings = db.query(ProjectFinding).filter(ProjectFinding.project_id == project_id).all()
    risk_analysis = db.query(ProjectRiskAnalysis).filter(ProjectRiskAnalysis.project_id == project_id).first()

    return {
        "project": ProjectOutSchema.model_validate(project),
        "evidence_files": evidence,
        "expenses": expenses,
        "findings": findings,
        "risk_analysis": risk_analysis
    }


@router.post("/{project_id}/evidence")
async def upload_project_evidence(
    project_id: int,
    file: UploadFile = File(...),
    evidence_type: str = Form("SITE_PHOTO"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.ngo_detail:
        raise HTTPException(status_code=400, detail="User must have an associated NGO profile")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.ngo_id != current_user.ngo_detail.id:
        raise HTTPException(status_code=403, detail="Access denied: You cannot upload evidence for another NGO's project")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="File is empty")

    ngo = current_user.ngo_detail
    
    # Forensic & pHash Analysis
    analysis = DocumentTamperEngine.analyze_project_evidence(
        file_bytes=file_bytes,
        filename=file.filename,
        evidence_type=evidence_type,
        project_id=project_id,
        ngo_profile=ngo,
        db_session=db
    )

    # Save file locally
    safe_filename = f"p{project_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    evidence_entry = ProjectEvidence(
        project_id=project_id,
        ngo_id=ngo.id,
        evidence_type=evidence_type,
        file_name=file.filename,
        file_path=file_path,
        sha256_hash=analysis["sha256_hash"],
        p_hash=analysis["p_hash"],
        mime_type=analysis["mime_type"],
        file_size=analysis["file_size"],
        image_width=analysis["image_width"],
        image_height=analysis["image_height"],
        ocr_text=analysis["ocr_text"],
        exif_metadata=analysis["exif_metadata"],
        tamper_risk_score=analysis["tamper_risk_score"],
        tamper_risk_level=analysis["tamper_risk_level"],
        verification_status=analysis["verification_status"],
        evidence_findings=analysis["evidence_findings"]
    )

    db.add(evidence_entry)
    db.commit()
    db.refresh(evidence_entry)

    # Trigger full project integrity evaluation
    integrity_result = ProjectIntegrityEngine.analyze_project(db, project_id)

    # Audit Log
    audit = AuditLog(
        actor_user_id=current_user.id,
        ngo_id=ngo.id,
        action="EVIDENCE_UPLOAD",
        entity_type="PROJECT_EVIDENCE",
        entity_id=evidence_entry.id,
        metadata_json=f'{{"file_name": "{file.filename}", "tamper_score": {analysis["tamper_risk_score"]}}}'
    )
    db.add(audit)
    db.commit()

    return {
        "evidence": {
            "id": evidence_entry.id,
            "project_id": evidence_entry.project_id,
            "ngo_id": evidence_entry.ngo_id,
            "evidence_type": evidence_entry.evidence_type,
            "file_name": evidence_entry.file_name,
            "file_path": evidence_entry.file_path,
            "sha256_hash": evidence_entry.sha256_hash,
            "p_hash": evidence_entry.p_hash,
            "mime_type": evidence_entry.mime_type,
            "file_size": evidence_entry.file_size,
            "upload_timestamp": evidence_entry.upload_timestamp.isoformat() if evidence_entry.upload_timestamp else None,
            "ocr_text": evidence_entry.ocr_text,
            "exif_metadata": evidence_entry.exif_metadata,
            "image_width": evidence_entry.image_width,
            "image_height": evidence_entry.image_height,
            "tamper_risk_score": evidence_entry.tamper_risk_score,
            "tamper_risk_level": evidence_entry.tamper_risk_level,
            "verification_status": evidence_entry.verification_status,
            "evidence_findings": evidence_entry.evidence_findings
        },
        "integrity_result": integrity_result
    }



@router.post("/{project_id}/expenses")
def add_project_expense(
    expense_in: ExpenseCreateSchema,
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):


    if not current_user.ngo_detail:
        raise HTTPException(status_code=400, detail="User must have an associated NGO profile")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.ngo_id != current_user.ngo_detail.id:
        raise HTTPException(status_code=403, detail="Access denied: You cannot log expenses for another NGO's project")

    expense = ProjectExpense(
        project_id=project_id,
        ngo_id=current_user.ngo_detail.id,
        evidence_id=expense_in.evidence_id,
        invoice_number=expense_in.invoice_number,
        vendor_name=expense_in.vendor_name,
        amount=expense_in.amount,
        expense_date=parse_date(expense_in.expense_date) or datetime.utcnow(),
        description=expense_in.description
    )


    db.add(expense)
    db.commit()
    db.refresh(expense)

    # Trigger project integrity re-analysis
    integrity_result = ProjectIntegrityEngine.analyze_project(db, project_id)

    return {
        "expense": expense,
        "integrity_result": integrity_result
    }


@router.get("/{project_id}/integrity-analysis")
def get_project_integrity_analysis(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.ngo_detail:
        raise HTTPException(status_code=400, detail="User must have an associated NGO profile")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.ngo_id != current_user.ngo_detail.id:
        raise HTTPException(status_code=403, detail="Access denied")

    result = ProjectIntegrityEngine.analyze_project(db, project_id)
    return result
