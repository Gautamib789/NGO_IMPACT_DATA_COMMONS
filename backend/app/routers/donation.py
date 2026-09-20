import json
import hashlib
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.models.ngo import NGODetail, NGOStatus
from app.models.donation import Donation
from app.models.audit import AuditLog
from app.schemas.donation import DonationCreate, DonationOut
from app.dependencies import require_roles, get_current_user
from app.services.ledger_engine import LedgerEngine
from app.services.fraud_engine import FraudDetectionEngine

router = APIRouter(prefix="/api/donations", tags=["Donations Engine"])


@router.post("/create", response_model=DonationOut)
def log_donation(
    donation_in: DonationCreate,
    current_user: User = Depends(require_roles([UserRole.DONOR, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    ngo = db.query(NGODetail).filter(NGODetail.id == donation_in.ngo_id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO not found")
    if ngo.status != NGOStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Cannot donate to an unapproved or pending NGO")
    if donation_in.amount <= 0:
        raise HTTPException(status_code=400, detail="Donation amount must be greater than 0")

    # Generate unique transaction hash
    tx_raw = f"{current_user.id}-{ngo.id}-{donation_in.amount}-{datetime.utcnow().timestamp()}"
    tx_hash = "0x" + hashlib.sha256(tx_raw.encode('utf-8')).hexdigest()

    donation = Donation(
        donor_id=current_user.id,
        ngo_id=ngo.id,
        amount=donation_in.amount,
        currency=donation_in.currency,
        donor_name=donation_in.donor_name or current_user.full_name,
        message=donation_in.message,
        transaction_hash=tx_hash,
        status="COMPLETED"
    )
    db.add(donation)

    # Update NGO financials
    ngo.total_donations_received += donation_in.amount
    db.commit()
    db.refresh(donation)

    # Re-evaluate AI Fraud Scan & Transparency Score
    FraudDetectionEngine.scan_ngo(db, ngo.id)

    # Append block to SHA-256 Blockchain Ledger
    LedgerEngine.append_block(
        db,
        event_type="DONATION_LOGGED",
        payload={
            "donation_id": donation.id,
            "tx_hash": tx_hash,
            "donor_name": donation_in.donor_name or current_user.full_name or "Verified Donor",
            "ngo_id": ngo.id,
            "ngo_name": ngo.org_name,
            "amount": donation.amount,
            "currency": donation.currency
        }
    )

    # Record Audit Log
    audit = AuditLog(
        actor_user_id=current_user.id,
        ngo_id=ngo.id,
        action="DONATION_CREATED",
        entity_type="DONATION",
        entity_id=donation.id,
        metadata_json=json.dumps({
            "amount": donation.amount,
            "currency": donation.currency,
            "tx_hash": tx_hash
        })
    )
    db.add(audit)
    db.commit()

    # Attach ngo_name for response
    donation_dict = DonationOut.from_orm(donation)
    donation_dict.ngo_name = ngo.org_name
    return donation_dict


@router.get("/my-donations", response_model=List[DonationOut])
def get_my_donations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    donations = db.query(Donation).filter(Donation.donor_id == current_user.id).order_by(Donation.created_at.desc()).all()
    results = []
    for d in donations:
        d_out = DonationOut.from_orm(d)
        d_out.ngo_name = d.ngo.org_name if d.ngo else "Unknown NGO"
        results.append(d_out)
    return results
