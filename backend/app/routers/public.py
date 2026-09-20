from typing import List, Optional, Any, Union
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.ngo import NGODetail, NGOStatus
from app.models.donation import Donation
from app.models.ledger import LedgerBlock
from app.models.project import Project
from app.models.expense import Expense
from app.schemas.ngo import PublicNGOOut, NGOOut

router = APIRouter(prefix="/api/public", tags=["Public Transparency Portal"])


@router.get("/ngos", response_model=Union[List[PublicNGOOut], Any])
def list_public_approved_ngos(
    category: Optional[str] = None,
    cause: Optional[str] = None,
    search: Optional[str] = None,
    state: Optional[str] = None,
    sort: Optional[str] = "recent",
    page: int = 1,
    limit: int = 12,
    meta: bool = False,
    db: Session = Depends(get_db)
):
    query = db.query(NGODetail).filter(NGODetail.status == NGOStatus.APPROVED)

    # Cause / Category Filter
    cause_val = cause or category
    if cause_val and cause_val not in ["All", "All causes"]:
        query = query.filter(NGODetail.category.ilike(f"%{cause_val}%"))

    # Search Filter (matches org_name OR address/city)
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                NGODetail.org_name.ilike(pattern),
                NGODetail.address.ilike(pattern)
            )
        )

    # State Filter (matches address location)
    if state and state not in ["All", "All states"]:
        query = query.filter(NGODetail.address.ilike(f"%{state}%"))

    # Sorting Logic
    if sort in ["recent", "Recently registered"]:
        query = query.order_by(NGODetail.created_at.desc())
    elif sort in ["oldest", "Oldest registered"]:
        query = query.order_by(NGODetail.created_at.asc())
    elif sort in ["name_asc", "Name A-Z"]:
        query = query.order_by(NGODetail.org_name.asc())
    elif sort in ["name_desc", "Name Z-A"]:
        query = query.order_by(NGODetail.org_name.desc())
    elif sort in ["transparency_high", "Highest transparency score"]:
        query = query.order_by(NGODetail.transparency_score.desc())
    elif sort in ["transparency_low", "Lowest transparency score"]:
        query = query.order_by(NGODetail.transparency_score.asc())
    else:
        query = query.order_by(NGODetail.created_at.desc())

    total = query.count()
    page_num = max(1, page)
    limit_num = max(1, limit)
    offset = (page_num - 1) * limit_num
    items = query.offset(offset).limit(limit_num).all()

    if meta:
        total_pages = (total + limit_num - 1) // limit_num if limit_num > 0 else 1
        return {
            "items": [PublicNGOOut.from_orm(item) for item in items],
            "total": total,
            "page": page_num,
            "limit": limit_num,
            "total_pages": total_pages
        }

    return items


@router.get("/ngos/{ngo_id}", response_model=PublicNGOOut)
def get_public_ngo_detail(
    ngo_id: int,
    db: Session = Depends(get_db)
):
    ngo = db.query(NGODetail).filter(NGODetail.id == ngo_id, NGODetail.status == NGOStatus.APPROVED).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="Approved NGO profile not found")
    return ngo


@router.get("/ngos/{ngo_id}/projects")
def get_public_ngo_projects(
    ngo_id: int,
    db: Session = Depends(get_db)
):
    ngo = db.query(NGODetail).filter(NGODetail.id == ngo_id, NGODetail.status == NGOStatus.APPROVED).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="Approved NGO profile not found")

    projects = db.query(Project).filter(Project.ngo_id == ngo_id, Project.status == "ACTIVE").all()
    res = []
    for p in projects:
        expenses = db.query(Expense).filter(Expense.project_id == p.id).all()
        spent = sum(e.amount for e in expenses) if expenses else 0.0
        res.append({
            "id": p.id,
            "project_name": p.project_name,
            "description": p.description,
            "category": p.category,
            "location": p.location,
            "latitude": p.latitude,
            "longitude": p.longitude,
            "budget": p.budget,
            "total_expenses_claimed": spent,
            "fund_utilization_ratio": round((spent / p.budget) * 100.0, 2) if p.budget > 0 else 0.0,
            "target_beneficiaries": p.target_beneficiaries,
            "outcomes": p.outcomes,
            "status": p.status
        })
    return res


@router.get("/stats")
def get_public_platform_stats(db: Session = Depends(get_db)):
    approved_ngos = db.query(NGODetail).filter(NGODetail.status == NGOStatus.APPROVED).count()
    donations = db.query(Donation).all()
    total_raised = sum([d.amount for d in donations]) if donations else 0.0
    total_donations_count = len(donations)

    beneficiaries = db.query(NGODetail).filter(NGODetail.status == NGOStatus.APPROVED).all()
    total_beneficiaries = sum([b.beneficiary_count for b in beneficiaries]) if beneficiaries else 0

    block_count = db.query(LedgerBlock).count()

    return {
        "approved_ngos_count": approved_ngos,
        "total_funds_raised": round(total_raised, 2),
        "total_donations_count": total_donations_count,
        "total_beneficiaries_impacted": total_beneficiaries,
        "blockchain_ledger_blocks": block_count
    }
