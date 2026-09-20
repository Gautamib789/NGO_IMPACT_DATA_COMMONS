import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.models.ngo import NGODetail, NGODocument, NGOStatus
from app.schemas.ngo import NGOCreate, NGOOut, NGOFinancialUpdate, NGOUpdate
from app.dependencies import get_current_user, require_roles
from app.services.fraud_engine import FraudDetectionEngine
import json
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogOut

router = APIRouter(prefix="/api/ngos", tags=["NGO Operations"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/register", response_model=NGOOut)
def register_ngo(
    ngo_in: NGOCreate,
    current_user: User = Depends(require_roles([UserRole.NGO])),
    db: Session = Depends(get_db)
):
    existing = db.query(NGODetail).filter(NGODetail.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="NGO profile already created for this account")

    existing_reg = db.query(NGODetail).filter(NGODetail.registration_number == ngo_in.registration_number).first()
    if existing_reg:
        raise HTTPException(status_code=400, detail="Registration number already in use")

    ngo = NGODetail(
        user_id=current_user.id,
        org_name=ngo_in.org_name,
        registration_number=ngo_in.registration_number,
        tax_id=ngo_in.tax_id,
        category=ngo_in.category,
        mission_statement=ngo_in.mission_statement,
        website=ngo_in.website,
        address=ngo_in.address,
        status=NGOStatus.PENDING,
        doc_completeness_score=30.0,
        transparency_score=50.0
    )
    db.add(ngo)
    db.commit()
    db.refresh(ngo)

    # Initial fraud scan for duplicate registration
    FraudDetectionEngine.scan_ngo(db, ngo.id)

    # Record Audit Log
    audit = AuditLog(
        actor_user_id=current_user.id,
        ngo_id=ngo.id,
        action="PROFILE_CREATE",
        entity_type="NGO",
        entity_id=ngo.id,
        metadata_json=json.dumps({"org_name": ngo.org_name, "registration_number": ngo.registration_number})
    )
    db.add(audit)
    db.commit()

    return ngo


@router.get("/profile", response_model=NGOOut)
def get_my_ngo_profile(
    current_user: User = Depends(require_roles([UserRole.NGO])),
    db: Session = Depends(get_db)
):
    ngo = db.query(NGODetail).filter(NGODetail.user_id == current_user.id).first()
    if not ngo:
        ngo = NGODetail(
            user_id=current_user.id,
            org_name=current_user.full_name or "NGO Organization",
            registration_number=f"REG-{current_user.id:04d}",
            tax_id=f"TAX-{current_user.id:04d}",
            category="General Social Welfare",
            status=NGOStatus.PENDING,
            doc_completeness_score=30.0,
            transparency_score=50.0
        )
        db.add(ngo)
        db.commit()
        db.refresh(ngo)
    return ngo


@router.put("/profile", response_model=NGOOut)
def update_my_ngo_profile(
    ngo_in: NGOUpdate,
    current_user: User = Depends(require_roles([UserRole.NGO])),
    db: Session = Depends(get_db)
):
    ngo = db.query(NGODetail).filter(NGODetail.user_id == current_user.id).first()
    if not ngo:
        org_name = ngo_in.org_name or current_user.full_name or "NGO Organization"
        reg_number = ngo_in.registration_number or f"REG-{current_user.id:04d}"
        tax_id = ngo_in.tax_id or f"TAX-{current_user.id:04d}"
        category = ngo_in.category or "General Social Welfare"
        ngo = NGODetail(
            user_id=current_user.id,
            org_name=org_name,
            registration_number=reg_number,
            tax_id=tax_id,
            category=category,
            mission_statement=ngo_in.mission_statement,
            website=ngo_in.website,
            address=ngo_in.address,
            organization_type=ngo_in.organization_type or "Trust",
            city=ngo_in.city,
            state=ngo_in.state,
            district=ngo_in.district,
            pin_code=ngo_in.pin_code,
            phone=ngo_in.phone,
            vision=ngo_in.vision,
            operating_areas=ngo_in.operating_areas,
            pan=ngo_in.pan,
            eighty_g_info=ngo_in.eighty_g_info,
            fcra_info=ngo_in.fcra_info,
            gst_number=ngo_in.gst_number,
            status=NGOStatus.PENDING,
            doc_completeness_score=30.0,
            transparency_score=50.0
        )
        db.add(ngo)
        db.commit()
        db.refresh(ngo)
    else:
        update_data = ngo_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(ngo, field, value)
        db.commit()
        db.refresh(ngo)

    # Record Audit Log
    audit = AuditLog(
        actor_user_id=current_user.id,
        ngo_id=ngo.id,
        action="PROFILE_UPDATE",
        entity_type="NGO",
        entity_id=ngo.id,
        metadata_json=json.dumps({"updated_fields": list(ngo_in.dict(exclude_unset=True).keys())})
    )
    db.add(audit)
    db.commit()

    db.refresh(ngo)

    # Re-scan fraud engine
    FraudDetectionEngine.scan_ngo(db, ngo.id)

    return ngo


from app.services.document_tamper_engine import DocumentTamperEngine
from app.models.audit import AuditLog


@router.post("/upload-document")
async def upload_ngo_document(
    document_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles([UserRole.NGO])),
    db: Session = Depends(get_db)
):
    ngo = db.query(NGODetail).filter(NGODetail.user_id == current_user.id).first()
    if not ngo:
        raise HTTPException(status_code=400, detail="Please create an NGO profile first")

    # Read raw file bytes for analysis
    file_bytes = await file.read()

    # Look for an existing verified reference document of the same document_type for this NGO
    reference_bytes = None
    ref_doc = db.query(NGODocument).filter(
        NGODocument.ngo_id == ngo.id,
        NGODocument.document_type == document_type,
        NGODocument.verification_status == "VERIFIED"
    ).first()
    if ref_doc and ref_doc.file_path:
        local_ref_name = os.path.basename(ref_doc.file_path)
        full_ref_path = os.path.join(UPLOAD_DIR, local_ref_name)
        if os.path.exists(full_ref_path):
            try:
                with open(full_ref_path, "rb") as rf:
                    reference_bytes = rf.read()
            except Exception:
                reference_bytes = None

    # Perform SHA-256 calculation, magic byte check, tamper detection, image forensics, and OCR extraction
    analysis = DocumentTamperEngine.analyze_document(
        file_bytes=file_bytes,
        filename=file.filename,
        document_type=document_type,
        ngo_profile=ngo,
        reference_bytes=reference_bytes,
        db_session=db
    )

    file_extension = os.path.splitext(file.filename)[1]
    safe_filename = f"ngo_{ngo.id}_{int(os.path.getmtime(__file__))}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as buffer:
        buffer.write(file_bytes)

    relative_path = f"/uploads/{safe_filename}"
    doc = NGODocument(
        ngo_id=ngo.id,
        document_type=document_type,
        file_name=file.filename,
        file_path=relative_path,
        sha256_hash=analysis["sha256_hash"],
        mime_type=analysis["mime_type"],
        file_size=analysis["file_size"],
        verification_status=analysis["verification_status"],
        verification_message=analysis["verification_message"],
        tamper_risk_score=analysis["tamper_risk_score"],
        tamper_risk_level=analysis["tamper_risk_level"],
        ocr_text=analysis["ocr_text"],
        exif_metadata=analysis["exif_metadata"]
    )
    db.add(doc)

    # Update completeness score
    ngo.doc_completeness_score = min(100.0, ngo.doc_completeness_score + 25.0)
    db.commit()
    db.refresh(doc)
    db.refresh(ngo)

    # Record Audit Log
    audit = AuditLog(
        actor_user_id=current_user.id,
        ngo_id=ngo.id,
        action="DOCUMENT_UPLOAD",
        entity_type="DOCUMENT",
        entity_id=doc.id,
        metadata_json=f'{{"document_type": "{document_type}", "sha256": "{doc.sha256_hash}", "tamper_score": {doc.tamper_risk_score}, "status": "{doc.verification_status}"}}'
    )
    db.add(audit)
    db.commit()

    # Re-scan fraud engine
    FraudDetectionEngine.scan_ngo(db, ngo.id)

    return {
        "message": "Document uploaded and analyzed successfully",
        "doc_id": doc.id,
        "file_path": relative_path,
        "sha256_hash": doc.sha256_hash,
        "verification_status": doc.verification_status,
        "tamper_risk_score": doc.tamper_risk_score,
        "tamper_risk_level": doc.tamper_risk_level,
        "verification_message": doc.verification_message
    }


from app.models.government import GovernmentRegistry
from app.services.government_verification import GovernmentVerificationService
from app.schemas.government import GovernmentVerificationResponse, GovernmentRegistryOut


@router.post("/financials", response_model=NGOOut)
def update_financials(
    fin_in: NGOFinancialUpdate,
    current_user: User = Depends(require_roles([UserRole.NGO])),
    db: Session = Depends(get_db)
):
    ngo = db.query(NGODetail).filter(NGODetail.user_id == current_user.id).first()
    if not ngo:
        raise HTTPException(status_code=400, detail="NGO profile not found")

    ngo.total_expenses = fin_in.total_expenses
    ngo.total_donations_received = fin_in.total_donations_received
    ngo.beneficiary_count = fin_in.beneficiary_count
    db.commit()
    db.refresh(ngo)

    # Record Audit Log
    audit = AuditLog(
        actor_user_id=current_user.id,
        ngo_id=ngo.id,
        action="FINANCIALS_UPDATE",
        entity_type="NGO",
        entity_id=ngo.id,
        metadata_json=json.dumps({
            "total_expenses": ngo.total_expenses,
            "total_donations": ngo.total_donations_received,
            "beneficiary_count": ngo.beneficiary_count
        })
    )
    db.add(audit)
    db.commit()

    # Run AI Fraud Detection Scan
    FraudDetectionEngine.scan_ngo(db, ngo.id)

    return ngo


@router.get("/government-verification", response_model=GovernmentVerificationResponse)
def get_government_verification_status(
    current_user: User = Depends(require_roles([UserRole.NGO])),
    db: Session = Depends(get_db)
):
    """
    Returns current automated government registry verification status for the authenticated NGO.
    """
    ngo = db.query(NGODetail).filter(NGODetail.user_id == current_user.id).first()
    if not ngo:
        raise HTTPException(status_code=400, detail="Please create an NGO profile first before attempting government verification.")

    result = GovernmentVerificationService.verify_ngo(db, ngo)
    return result


@router.post("/government-verification", response_model=GovernmentVerificationResponse)
def run_government_verification(
    current_user: User = Depends(require_roles([UserRole.NGO])),
    db: Session = Depends(get_db)
):
    """
    Triggers automated verification of NGO registration and tax parameters against
    the simulated Demo Government Registry.
    """
    ngo = db.query(NGODetail).filter(NGODetail.user_id == current_user.id).first()
    if not ngo:
        raise HTTPException(status_code=400, detail="Please create an NGO profile first before attempting government verification.")

    result = GovernmentVerificationService.verify_ngo(db, ngo)
    
    # Re-run AI Fraud engine scan to sync transparency score & flags
    FraudDetectionEngine.scan_ngo(db, ngo.id)

    return result


@router.get("/demo-government-registry/records", response_model=List[GovernmentRegistryOut])
def get_demo_government_registry_records(
    db: Session = Depends(get_db)
):
    """
    Returns simulated government registry records for academic/project demonstration purposes.
    """
    GovernmentVerificationService.seed_demo_registry(db)
    records = db.query(GovernmentRegistry).all()
    return records


@router.get("/audit-logs", response_model=List[AuditLogOut])
def get_my_ngo_audit_logs(
    current_user: User = Depends(require_roles([UserRole.NGO])),
    db: Session = Depends(get_db)
):
    """
    Returns audit trail records for the authenticated NGO account.
    """
    ngo = db.query(NGODetail).filter(NGODetail.user_id == current_user.id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO profile not found for current user")

    audits = db.query(AuditLog).filter(
        AuditLog.ngo_id == ngo.id
    ).order_by(AuditLog.created_at.desc()).all()
    return audits


