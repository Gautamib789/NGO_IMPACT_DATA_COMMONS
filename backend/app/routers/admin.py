import json
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.models.ngo import NGODetail, NGODocument, NGOStatus
from app.models.donation import Donation
from app.models.fraud import FraudFlag
from app.models.audit import AuditLog
from app.schemas.ngo import NGOOut
from app.schemas.admin_doc import AdminDocReviewIn, AdminDocInspectionOut
from app.schemas.audit import AuditLogOut
from app.dependencies import require_roles
from app.services.ledger_engine import LedgerEngine
from app.services.fraud_engine import FraudDetectionEngine

router = APIRouter(prefix="/api/admin", tags=["Admin Workflow"])


class RejectReasonIn(BaseModel):
    reason: str


def _build_doc_inspection_response(doc: NGODocument, db: Session) -> AdminDocInspectionOut:
    ngo = db.query(NGODetail).filter(NGODetail.id == doc.ngo_id).first()
    reviewer = db.query(User).filter(User.id == doc.reviewed_by).first() if doc.reviewed_by else None
    
    audits = db.query(AuditLog).filter(
        AuditLog.ngo_id == doc.ngo_id
    ).order_by(AuditLog.created_at.desc()).all()

    audit_list = []
    for a in audits:
        meta = {}
        try:
            meta = json.loads(a.metadata_json) if a.metadata_json else {}
        except Exception:
            meta = {"raw": a.metadata_json}

        audit_list.append({
            "id": a.id,
            "actor_user_id": a.actor_user_id,
            "action": a.action,
            "entity_type": a.entity_type,
            "entity_id": a.entity_id,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "metadata": meta
        })

    return AdminDocInspectionOut(
        id=doc.id,
        ngo_id=doc.ngo_id,
        ngo_org_name=ngo.org_name if ngo else None,
        ngo_registration_number=ngo.registration_number if ngo else None,
        document_type=doc.document_type,
        file_name=doc.file_name,
        file_path=doc.file_path,
        file_size=doc.file_size,
        mime_type=doc.mime_type,
        sha256_hash=doc.sha256_hash,
        verification_status=doc.verification_status,
        verification_message=doc.verification_message,
        tamper_risk_score=doc.tamper_risk_score,
        tamper_risk_level=doc.tamper_risk_level,
        ocr_text=doc.ocr_text,
        exif_metadata=doc.exif_metadata,
        upload_date=doc.upload_date,
        reviewed_by=doc.reviewed_by,
        reviewed_by_email=reviewer.email if reviewer else None,
        reviewed_at=doc.reviewed_at,
        review_notes=doc.review_notes,
        audit_history=audit_list
    )


@router.get("/ngos/pending", response_model=List[NGOOut])
def get_pending_ngos(
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    return db.query(NGODetail).filter(NGODetail.status == NGOStatus.PENDING).all()


@router.get("/ngos/all", response_model=List[NGOOut])
def get_all_ngos(
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    return db.query(NGODetail).order_by(NGODetail.created_at.desc()).all()


@router.post("/ngos/{ngo_id}/approve", response_model=NGOOut)
def approve_ngo(
    ngo_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    ngo = db.query(NGODetail).filter(NGODetail.id == ngo_id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO not found")

    ngo.status = NGOStatus.APPROVED
    ngo.rejection_reason = None
    db.commit()

    # Re-evaluate fraud & transparency score
    FraudDetectionEngine.scan_ngo(db, ngo.id)

    # Append to Blockchain Ledger
    LedgerEngine.append_block(
        db,
        event_type="NGO_APPROVED",
        payload={
            "ngo_id": ngo.id,
            "org_name": ngo.org_name,
            "registration_number": ngo.registration_number,
            "approved_by_admin": current_user.email,
            "transparency_score": ngo.transparency_score
        }
    )

    # Record Audit Log
    audit = AuditLog(
        actor_user_id=current_user.id,
        ngo_id=ngo.id,
        action="NGO_APPROVAL",
        entity_type="NGO",
        entity_id=ngo.id,
        metadata_json=json.dumps({"approved_by": current_user.email})
    )
    db.add(audit)
    db.commit()

    db.refresh(ngo)
    return ngo


@router.post("/ngos/{ngo_id}/reject", response_model=NGOOut)
def reject_ngo(
    ngo_id: int,
    reject_in: RejectReasonIn,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    ngo = db.query(NGODetail).filter(NGODetail.id == ngo_id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO not found")

    ngo.status = NGOStatus.REJECTED
    ngo.rejection_reason = reject_in.reason
    db.commit()

    # Append to Blockchain Ledger
    LedgerEngine.append_block(
        db,
        event_type="NGO_REJECTED",
        payload={
            "ngo_id": ngo.id,
            "org_name": ngo.org_name,
            "reason": reject_in.reason,
            "rejected_by_admin": current_user.email
        }
    )

    # Record Audit Log
    audit = AuditLog(
        actor_user_id=current_user.id,
        ngo_id=ngo.id,
        action="NGO_REJECTION",
        entity_type="NGO",
        entity_id=ngo.id,
        metadata_json=json.dumps({"rejected_by": current_user.email, "reason": reject_in.reason})
    )
    db.add(audit)
    db.commit()

    db.refresh(ngo)
    return ngo


@router.get("/documents/pending", response_model=List[AdminDocInspectionOut])
def get_pending_documents(
    status_filter: Optional[str] = Query(None, description="Optional status filter"),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """
    Returns uploaded NGO documents pending admin inspection and review.
    """
    query = db.query(NGODocument)
    if status_filter:
        query = query.filter(NGODocument.verification_status == status_filter.upper())
    else:
        query = query.filter(NGODocument.verification_status.in_(["NEEDS_ADMIN_REVIEW", "PROCESSING", "REQUEST_CLARIFICATION"]))

    docs = query.order_by(NGODocument.upload_date.desc()).all()
    return [_build_doc_inspection_response(d, db) for d in docs]


@router.get("/documents/all", response_model=List[AdminDocInspectionOut])
def get_all_documents(
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """
    Returns all NGO documents across the platform for administrative audit.
    """
    docs = db.query(NGODocument).order_by(NGODocument.upload_date.desc()).all()
    return [_build_doc_inspection_response(d, db) for d in docs]


@router.get("/documents/{doc_id}", response_model=AdminDocInspectionOut)
def inspect_document(
    doc_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """
    Detailed inspection endpoint for a single document.
    Includes file metadata, tamper risk score, OCR text, EXIF findings, and audit log history.
    """
    doc = db.query(NGODocument).filter(NGODocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return _build_doc_inspection_response(doc, db)


@router.post("/documents/{doc_id}/review", response_model=AdminDocInspectionOut)
def review_document(
    doc_id: int,
    review_in: AdminDocReviewIn,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """
    Submits admin review decision for an NGO document: APPROVE, REJECT, or REQUEST_CLARIFICATION.
    Updates status, logs AuditLog, and re-scans NGO transparency score.
    """
    doc = db.query(NGODocument).filter(NGODocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    decision = review_in.decision.upper().strip()
    if decision not in ["APPROVE", "REJECT", "REQUEST_CLARIFICATION"]:
        raise HTTPException(status_code=400, detail="Invalid decision. Must be one of APPROVE, REJECT, REQUEST_CLARIFICATION")

    prev_status = doc.verification_status

    if decision == "APPROVE":
        doc.verification_status = "VERIFIED"
        doc.verification_message = f"Approved by Admin ({current_user.email}): {review_in.notes or 'Document verified.'}"
    elif decision == "REJECT":
        doc.verification_status = "REJECTED"
        doc.verification_message = f"Rejected by Admin ({current_user.email}): {review_in.notes or 'Document rejected.'}"
    elif decision == "REQUEST_CLARIFICATION":
        doc.verification_status = "REQUEST_CLARIFICATION"
        doc.verification_message = f"Clarification Requested by Admin ({current_user.email}): {review_in.notes or 'Further clarification required.'}"

    doc.reviewed_by = current_user.id
    doc.reviewed_at = datetime.utcnow()
    doc.review_notes = review_in.notes

    db.commit()

    # Record Audit Log
    audit = AuditLog(
        actor_user_id=current_user.id,
        ngo_id=doc.ngo_id,
        action="ADMIN_DOCUMENT_REVIEW",
        entity_type="DOCUMENT",
        entity_id=doc.id,
        metadata_json=json.dumps({
            "decision": decision,
            "notes": review_in.notes,
            "previous_status": prev_status,
            "new_status": doc.verification_status,
            "admin_email": current_user.email
        })
    )
    db.add(audit)
    db.commit()

    # Re-scan NGO fraud & transparency score
    FraudDetectionEngine.scan_ngo(db, doc.ngo_id)

    db.refresh(doc)
    return _build_doc_inspection_response(doc, db)


@router.get("/stats")
def get_admin_dashboard_stats(
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    total_users = db.query(User).count()
    total_ngos = db.query(NGODetail).count()
    pending_ngos = db.query(NGODetail).filter(NGODetail.status == NGOStatus.PENDING).count()
    approved_ngos = db.query(NGODetail).filter(NGODetail.status == NGOStatus.APPROVED).count()
    total_donations = db.query(Donation).count()
    total_funds = db.query(Donation).with_entities(Donation.amount).all()
    sum_raised = sum([d[0] for d in total_funds]) if total_funds else 0.0
    open_fraud_flags = db.query(FraudFlag).filter(FraudFlag.status == "OPEN").count()

    pending_docs = db.query(NGODocument).filter(
        NGODocument.verification_status.in_(["NEEDS_ADMIN_REVIEW", "PROCESSING", "REQUEST_CLARIFICATION"])
    ).count()

    return {
        "total_users": total_users,
        "total_ngos": total_ngos,
        "pending_ngos": pending_ngos,
        "approved_ngos": approved_ngos,
        "total_donations": total_donations,
        "total_funds_raised": round(sum_raised, 2),
        "open_fraud_flags": open_fraud_flags,
        "pending_documents_for_review": pending_docs
    }


@router.get("/audit-logs", response_model=List[AuditLogOut])
def get_admin_audit_logs(
    ngo_id: Optional[int] = Query(None, description="Optional NGO ID filter"),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """
    Returns audit trail records for system-wide operations, optionally filtered by NGO ID.
    Access restricted to ADMIN role.
    """
    query = db.query(AuditLog)
    if ngo_id:
        query = query.filter(AuditLog.ngo_id == ngo_id)
    return query.order_by(AuditLog.created_at.desc()).all()


# ==================================================
# ADMIN PROJECT INTEGRITY & FRAUD REVIEW ENDPOINTS
# ==================================================

class AdminProjectReviewIn(BaseModel):
    decision: str  # APPROVE, REJECT, REQUEST_CLARIFICATION
    notes: Optional[str] = None


@router.get("/projects/pending")
def get_pending_projects_for_review(
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """
    Returns all projects flagged for admin review (integrity_status in NEEDS_ADMIN_REVIEW, REJECTED).
    """
    from app.models.project import Project, ProjectEvidence, ProjectExpense, ProjectFinding, ProjectRiskAnalysis

    projects = db.query(Project).filter(
        Project.integrity_status.in_(["NEEDS_ADMIN_REVIEW", "REJECTED"])
    ).order_by(Project.created_at.desc()).all()

    results = []
    for p in projects:
        ngo = db.query(NGODetail).filter(NGODetail.id == p.ngo_id).first()
        evidence_count = db.query(ProjectEvidence).filter(ProjectEvidence.project_id == p.id).count()
        expense_count = db.query(ProjectExpense).filter(ProjectExpense.project_id == p.id).count()
        findings = db.query(ProjectFinding).filter(ProjectFinding.project_id == p.id).all()
        risk_analysis = db.query(ProjectRiskAnalysis).filter(ProjectRiskAnalysis.project_id == p.id).first()

        results.append({
            "project_id": p.id,
            "project_name": p.project_name,
            "ngo_id": p.ngo_id,
            "ngo_org_name": ngo.org_name if ngo else "Unknown",
            "category": p.category,
            "total_budget": p.total_budget,
            "amount_spent": p.amount_spent,
            "integrity_status": p.integrity_status,
            "risk_score": p.risk_score,
            "risk_level": p.risk_level,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "evidence_count": evidence_count,
            "expense_count": expense_count,
            "findings": [{"category": f.category, "risk_level": f.risk_level, "message": f.message} for f in findings],
            "risk_analysis": {
                "document_identity_risk": risk_analysis.document_identity_risk if risk_analysis else 0.0,
                "photo_integrity_risk": risk_analysis.photo_integrity_risk if risk_analysis else 0.0,
                "financial_integrity_risk": risk_analysis.financial_integrity_risk if risk_analysis else 0.0,
                "evidence_consistency_risk": risk_analysis.evidence_consistency_risk if risk_analysis else 0.0,
                "recommendation": risk_analysis.recommendation if risk_analysis else None
            } if risk_analysis else None
        })

    return results


@router.get("/projects/all")
def get_all_projects_admin(
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """
    Returns all projects across all NGOs for administrative audit.
    """
    from app.models.project import Project, ProjectFinding, ProjectRiskAnalysis

    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    results = []
    for p in projects:
        ngo = db.query(NGODetail).filter(NGODetail.id == p.ngo_id).first()
        findings = db.query(ProjectFinding).filter(ProjectFinding.project_id == p.id).all()
        risk_analysis = db.query(ProjectRiskAnalysis).filter(ProjectRiskAnalysis.project_id == p.id).first()
        results.append({
            "project_id": p.id,
            "project_name": p.project_name,
            "ngo_id": p.ngo_id,
            "ngo_org_name": ngo.org_name if ngo else "Unknown",
            "category": p.category,
            "total_budget": p.total_budget,
            "amount_spent": p.amount_spent,
            "integrity_status": p.integrity_status,
            "risk_score": p.risk_score,
            "risk_level": p.risk_level,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "findings_count": len(findings),
            "recommendation": risk_analysis.recommendation if risk_analysis else None
        })
    return results


@router.get("/projects/{project_id}")
def inspect_project_admin(
    project_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """
    Detailed admin inspection endpoint for a single project.
    """
    from app.models.project import (
        Project, ProjectEvidence, ProjectExpense, ProjectFinding,
        ProjectRiskAnalysis, AdminProjectReview
    )

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    ngo = db.query(NGODetail).filter(NGODetail.id == project.ngo_id).first()
    evidence = db.query(ProjectEvidence).filter(ProjectEvidence.project_id == project_id).all()
    expenses = db.query(ProjectExpense).filter(ProjectExpense.project_id == project_id).all()
    findings = db.query(ProjectFinding).filter(ProjectFinding.project_id == project_id).all()
    risk_analysis = db.query(ProjectRiskAnalysis).filter(ProjectRiskAnalysis.project_id == project_id).first()
    reviews = db.query(AdminProjectReview).filter(AdminProjectReview.project_id == project_id).order_by(AdminProjectReview.created_at.desc()).all()

    return {
        "project": project,
        "ngo_org_name": ngo.org_name if ngo else "Unknown",
        "evidence_files": evidence,
        "expenses": expenses,
        "findings": findings,
        "risk_analysis": risk_analysis,
        "reviews": reviews
    }


@router.post("/projects/{project_id}/review")
def review_project_admin(
    project_id: int,
    review_in: AdminProjectReviewIn,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """
    Submits admin decision for a project: APPROVE, REJECT, or REQUEST_CLARIFICATION.
    Updates project status, records AdminProjectReview, and logs AuditLog.
    """
    from app.models.project import Project, AdminProjectReview

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    decision = review_in.decision.upper().strip()
    if decision not in ["APPROVE", "REJECT", "REQUEST_CLARIFICATION"]:
        raise HTTPException(status_code=400, detail="Invalid decision. Must be one of APPROVE, REJECT, REQUEST_CLARIFICATION")

    if decision == "APPROVE":
        project.integrity_status = "VERIFIED"
        project.status = "ACTIVE"
    elif decision == "REJECT":
        project.integrity_status = "REJECTED"
        project.status = "REJECTED"
    elif decision == "REQUEST_CLARIFICATION":
        project.integrity_status = "NEEDS_ADMIN_REVIEW"

    # Log Admin Project Review
    review_rec = AdminProjectReview(
        project_id=project_id,
        admin_user_id=current_user.id,
        decision=decision,
        review_notes=review_in.notes
    )
    db.add(review_rec)

    # Append block to Ledger
    LedgerEngine.append_block(
        db,
        event_type="PROJECT_REVIEWED",
        payload={
            "project_id": project_id,
            "project_name": project.project_name,
            "decision": decision,
            "notes": review_in.notes,
            "reviewed_by": current_user.email
        }
    )

    # Record Audit Log
    audit = AuditLog(
        actor_user_id=current_user.id,
        ngo_id=project.ngo_id,
        action="ADMIN_PROJECT_REVIEW",
        entity_type="PROJECT",
        entity_id=project.id,
        metadata_json=json.dumps({
            "decision": decision,
            "notes": review_in.notes,
            "admin_email": current_user.email
        })
    )
    db.add(audit)
    db.commit()
    db.refresh(project)

    return {
        "message": f"Project successfully reviewed. Decision: {decision}",
        "project": project
    }


@router.get("/notifications")
def get_admin_notifications(
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """
    Returns unread admin notifications for integrity alerts.
    """
    from app.models.project import AdminNotification
    notifications = db.query(AdminNotification).order_by(AdminNotification.created_at.desc()).all()
    return notifications


