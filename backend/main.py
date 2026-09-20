import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.database import engine, Base, SessionLocal
from app.db_init import init_db_schema
from app.models import User, UserRole, NGODetail, NGODocument, NGOStatus, Donation, LedgerBlock, FraudFlag, GovernmentRegistry, Project, Beneficiary, Expense, AuditLog
from app.core.security import get_password_hash
from app.services.ledger_engine import LedgerEngine

from app.routers import auth, ngo, admin, donation, ledger, fraud, chatbot, public, project_tracking, projects

# Create database tables and execute safe column migrations
init_db_schema()

app = FastAPI(
    title="NGO Impact Data Commons API",
    description="Production-Ready API for NGO Transparency, AI Fraud Detection, and SHA-256 Blockchain Ledger",
    version="1.0.0",
)

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://localhost:3000/",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3000/",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?/?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file uploads directory
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Include Routers
app.include_router(auth.router)
app.include_router(ngo.router)
app.include_router(admin.router)
app.include_router(donation.router)
app.include_router(ledger.router)
app.include_router(fraud.router)
app.include_router(chatbot.router)
app.include_router(public.router)
app.include_router(projects.router)
app.include_router(project_tracking.router)



def seed_database():
    db: Session = SessionLocal()
    try:
        # 1. Seed Admin User
        admin_user = db.query(User).filter(User.email == "admin@ngoimpact.org").first()
        if not admin_user:
            admin_user = User(
                email="admin@ngoimpact.org",
                hashed_password=get_password_hash("AdminPassword123!"),
                full_name="Platform Chief Auditor",
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

        # 2. Seed Donor User
        donor_user = db.query(User).filter(User.email == "donor@example.com").first()
        if not donor_user:
            donor_user = User(
                email="donor@example.com",
                hashed_password=get_password_hash("DonorPassword123!"),
                full_name="Global Philanthropist",
                role=UserRole.DONOR,
                is_active=True
            )
            db.add(donor_user)
            db.commit()

        # Seeded NGOs Data Specs
        ngos_to_seed = [
            {
                "email": "contact@ruralhealth.org",
                "full_name": "Rural Health Lead",
                "org_name": "Rural Health Trust",
                "registration_number": "REG-2024-11029",
                "tax_id": "TAX-88123-EXEMPT",
                "category": "Medical Support",
                "mission_statement": "Mobile medical vans bringing check-ups, medicines and maternal care to remote villages in Karnataka.",
                "website": "https://ruralhealth-trust.org",
                "address": "Bengaluru, Karnataka",
                "status": NGOStatus.APPROVED,
                "doc_completeness_score": 90.0,
                "transparency_score": 92.0,
                "total_expenses": 31000.0,
                "total_donations_received": 54000.0,
                "beneficiary_count": 4800
            },
            {
                "email": "contact@hopefoundation.org",
                "full_name": "Hope Foundation Director",
                "org_name": "Hope Foundation India",
                "registration_number": "REG-2024-55912",
                "tax_id": "TAX-44129-EXEMPT",
                "category": "Free Education",
                "mission_statement": "We run after-school learning centres and daily meal programmes for children of daily-wage workers across Delhi.",
                "website": "https://hopefoundation-india.org",
                "address": "New Delhi, Delhi",
                "status": NGOStatus.APPROVED,
                "doc_completeness_score": 95.0,
                "transparency_score": 86.0,
                "total_expenses": 42000.0,
                "total_donations_received": 68000.0,
                "beneficiary_count": 6200
            },
            {
                "email": "contact@greenearth.org",
                "full_name": "GreenEarth Lead",
                "org_name": "GreenEarth Environmental Alliance",
                "registration_number": "REG-2024-88912",
                "tax_id": "TAX-998234-EXEMPT",
                "category": "Environment & Conservation",
                "mission_statement": "Dedicated to reforestation, carbon neutrality, and ocean cleanup operations worldwide.",
                "website": "https://greenearth-alliance.org",
                "address": "San Francisco, California",
                "status": NGOStatus.APPROVED,
                "doc_completeness_score": 100.0,
                "transparency_score": 95.5,
                "total_expenses": 18500.0,
                "total_donations_received": 25000.0,
                "beneficiary_count": 1200
            },
            {
                "email": "info@cleanwater.org",
                "full_name": "CleanWater Director",
                "org_name": "CleanWater Global Initiative",
                "registration_number": "REG-2023-44109",
                "tax_id": "TAX-774120-EXEMPT",
                "category": "Clean Water & Sanitation",
                "mission_statement": "Building sustainable deep-borehole water filtration systems for rural schools and clinics.",
                "website": "https://cleanwater-initiative.org",
                "address": "Austin, Texas",
                "status": NGOStatus.APPROVED,
                "doc_completeness_score": 85.0,
                "transparency_score": 88.0,
                "total_expenses": 32000.0,
                "total_donations_received": 42500.0,
                "beneficiary_count": 3400
            }
        ]

        for seed in ngos_to_seed:
            user = db.query(User).filter(User.email == seed["email"]).first()
            if not user:
                user = User(
                    email=seed["email"],
                    hashed_password=get_password_hash("NgoPassword123!"),
                    full_name=seed["full_name"],
                    role=UserRole.NGO,
                    is_active=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)

            ngo_detail = db.query(NGODetail).filter(NGODetail.user_id == user.id).first()
            if not ngo_detail:
                ngo_detail = NGODetail(
                    user_id=user.id,
                    org_name=seed["org_name"],
                    registration_number=seed["registration_number"],
                    tax_id=seed["tax_id"],
                    category=seed["category"],
                    mission_statement=seed["mission_statement"],
                    website=seed["website"],
                    address=seed["address"],
                    status=seed["status"],
                    doc_completeness_score=seed["doc_completeness_score"],
                    transparency_score=seed["transparency_score"],
                    total_expenses=seed["total_expenses"],
                    total_donations_received=seed["total_donations_received"],
                    beneficiary_count=seed["beneficiary_count"]
                )
                db.add(ngo_detail)
                db.commit()

        # Initialize Genesis Block in Blockchain Ledger if empty
        LedgerEngine.verify_chain(db)

    except Exception as e:
        print(f"Error during database seed: {e}")
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    seed_database()


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ngo-impact-data-commons-backend",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "database": "sqlite/postgresql connected"
    }


@app.get("/")
def root():
    return {
        "message": "NGO Impact Data Commons API is active",
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
