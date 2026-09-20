from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.models.fraud import FraudFlag
from app.models.ngo import NGODetail
from app.dependencies import require_roles
from app.services.fraud_engine import FraudDetectionEngine

router = APIRouter(prefix="/api/fraud", tags=["AI Fraud Detection"])


@router.get("/flags")
def get_all_fraud_flags(
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    flags = db.query(FraudFlag).order_by(FraudFlag.created_at.desc()).all()
    results = []
    for f in flags:
        ngo = db.query(NGODetail).filter(NGODetail.id == f.ngo_id).first()
        results.append({
            "id": f.id,
            "ngo_id": f.ngo_id,
            "ngo_name": ngo.org_name if ngo else "Unknown NGO",
            "severity": f.severity,
            "rule_code": f.rule_code,
            "description": f.description,
            "status": f.status,
            "created_at": f.created_at
        })
    return results


@router.post("/scan/{ngo_id}")
def trigger_ngo_fraud_scan(
    ngo_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.NGO])),
    db: Session = Depends(get_db)
):
    flags = FraudDetectionEngine.scan_ngo(db, ngo_id)
    return {"message": f"Fraud scan complete. {len(flags)} new flags generated.", "new_flags": flags}


@router.post("/resolve/{flag_id}")
def resolve_fraud_flag(
    flag_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    flag = db.query(FraudFlag).filter(FraudFlag.id == flag_id).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")

    flag.status = "RESOLVED"
    db.commit()

    # Recalculate transparency score
    ngo = db.query(NGODetail).filter(NGODetail.id == flag.ngo_id).first()
    if ngo:
        FraudDetectionEngine._recalculate_transparency_score(db, ngo)

    return {"message": "Flag resolved successfully"}
