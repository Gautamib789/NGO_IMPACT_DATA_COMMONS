import json
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.ledger import LedgerBlock
from app.models.donation import Donation
from app.models.ngo import NGODetail, NGOStatus
from app.services.ledger_engine import LedgerEngine

router = APIRouter(prefix="/api/ledger", tags=["Blockchain Hash-Chain Ledger"])


def sanitize_payload(payload_str: str) -> Dict[str, Any]:
    """
    Parses payload JSON string into a dict and strips any donor_email field
    so it is NEVER exposed in public API responses.
    Does NOT modify the database or invalidate SHA-256 block hashes.
    """
    try:
        data = json.loads(payload_str) if isinstance(payload_str, str) else payload_str
        if isinstance(data, dict):
            # Strip email — non-destructive (original payload_json in DB untouched)
            data.pop("donor_email", None)
            # Ensure donor_name has a safe public fallback
            if not data.get("donor_name"):
                data["donor_name"] = "Verified donor"
        return data
    except Exception:
        return {}


def build_block_dict(b: LedgerBlock) -> Dict[str, Any]:
    """Converts a LedgerBlock ORM object to a public-safe serialisable dict."""
    payload = sanitize_payload(b.payload_json)
    return {
        "index": b.index,
        "timestamp": b.timestamp.isoformat() if isinstance(b.timestamp, datetime) else str(b.timestamp),
        "event_type": b.event_type,
        "payload": payload,                    # parsed dict — frontend reads this
        "payload_json": json.dumps(payload),   # re-serialised WITHOUT email
        "previous_hash": b.previous_hash,
        "block_hash": b.block_hash,
        "nonce": b.nonce,
    }


@router.get("/blocks")
def get_ledger_blocks(
    search: Optional[str] = Query(None, description="Search NGO name, donor, or hash"),
    ngo_id: Optional[int] = Query(None, description="Filter by NGO ID"),
    sort: Optional[str] = Query("newest", description="newest | oldest | highest_amount | lowest_amount"),
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db),
):
    # ── 1. Fetch & order raw blocks ──────────────────────────────────────────
    order = LedgerBlock.index.asc() if sort == "oldest" else LedgerBlock.index.desc()
    raw_blocks = db.query(LedgerBlock).order_by(order).all()

    # ── 2. Build sanitised block dicts ───────────────────────────────────────
    processed: list[Dict[str, Any]] = [build_block_dict(b) for b in raw_blocks]

    # ── 3. In-memory search (on sanitised data) ──────────────────────────────
    if search:
        term = search.lower().strip()
        processed = [
            b for b in processed
            if (
                term in str(b["payload"].get("ngo_name", "")).lower()
                or term in str(b["payload"].get("donor_name", "")).lower()
                or term in str(b["payload"].get("tx_hash", "")).lower()
                or term in str(b["block_hash"]).lower()
                or term in str(b["event_type"]).lower()
            )
        ]

    # ── 4. NGO ID filter ─────────────────────────────────────────────────────
    if ngo_id:
        processed = [b for b in processed if b["payload"].get("ngo_id") == ngo_id]

    # ── 5. Amount sort (applied after initial DB ordering) ───────────────────
    if sort == "highest_amount":
        processed.sort(key=lambda b: float(b["payload"].get("amount") or 0), reverse=True)
    elif sort == "lowest_amount":
        processed.sort(key=lambda b: float(b["payload"].get("amount") or 0), reverse=False)

    # ── 6. Pagination ─────────────────────────────────────────────────────────
    total_items = len(processed)
    total_pages = max(1, (total_items + limit - 1) // limit)
    offset = (page - 1) * limit
    page_items = processed[offset: offset + limit]

    # ── 7. Summary statistics from database & ledger payloads ─────────────────
    total_donations_db = db.query(func.count(Donation.id)).scalar() or 0
    total_blocks_db = db.query(func.count(LedgerBlock.index)).scalar() or 0
    supported_ngos_db = (
        db.query(func.count(NGODetail.id))
        .filter(NGODetail.status == NGOStatus.APPROVED)
        .scalar() or 0
    )

    # Active INR donations total from donations table
    inr_funds = float(db.query(func.sum(Donation.amount)).filter(Donation.currency == "INR").scalar() or 0.0)
    
    # Calculate historical USD total directly from raw ledger payload JSONs
    usd_funds = 0.0
    usd_count = 0
    inr_block_count = 0
    for b in raw_blocks:
        payload = sanitize_payload(b.payload_json)
        if payload.get("currency") == "USD":
            usd_funds += float(payload.get("amount") or 0.0)
            usd_count += 1
        elif payload.get("currency") == "INR":
            inr_block_count += 1

    stats = {
        "total_blocks": total_blocks_db,
        "total_donations": total_donations_db,
        "total_funds_inr": inr_funds,          # Active INR donations
        "total_funds_usd": usd_funds,          # Historical USD ledger total ($5,110)
        "usd_blocks_count": usd_count,        # Historical USD blocks count (21)
        "inr_blocks_count": inr_block_count,  # INR ledger blocks count (1)
        "supported_ngos": supported_ngos_db,
        "last_verified": datetime.utcnow().strftime("%d %B %Y, %I:%M %p UTC"),
    }

    # ── 8. Always return structured response ──────────────────────────────────
    return {
        "items": page_items,
        "total": total_items,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "stats": stats,
    }


@router.get("/verify")
def verify_ledger_integrity(db: Session = Depends(get_db)):
    result = LedgerEngine.verify_chain(db)
    result["verified_at"] = datetime.utcnow().strftime("%d %b %Y, %I:%M:%S %p UTC")
    return result
