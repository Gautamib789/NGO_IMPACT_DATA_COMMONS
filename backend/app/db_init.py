import os
from sqlalchemy import inspect, text
from app.database import engine, Base
# Import all models to ensure metadata is populated
from app.models import User, NGODetail, NGODocument, Donation, LedgerBlock, FraudFlag, GovernmentRegistry, Project, Beneficiary, Expense, AuditLog

def init_db_schema():
    """
    Safely initializes and migrates the SQLite database schema without data loss.
    Adds new columns to existing tables if missing and creates new tables.
    """
    # 1. First run SQLAlchemy create_all to create new tables
    Base.metadata.create_all(bind=engine)

    # 2. Inspect existing columns in sqlite DB and add any missing columns safely
    inspector = inspect(engine)
    
    # NGO Details missing columns
    existing_ngo_cols = {col['name'] for col in inspector.get_columns('ngo_details')}
    ngo_new_cols = {
        "established_date": "DATETIME",
        "organization_type": "VARCHAR DEFAULT 'Trust'",
        "city": "VARCHAR",
        "state": "VARCHAR",
        "district": "VARCHAR",
        "pin_code": "VARCHAR",
        "phone": "VARCHAR",
        "vision": "TEXT",
        "operating_areas": "TEXT",
        "pan": "VARCHAR",
        "eighty_g_info": "VARCHAR",
        "fcra_info": "VARCHAR",
        "gst_number": "VARCHAR",
        "government_verification_status": "VARCHAR DEFAULT 'NOT_VERIFIED'",
        "risk_level": "VARCHAR DEFAULT 'LOW'"
    }

    with engine.begin() as conn:
        for col_name, col_type in ngo_new_cols.items():
            if col_name not in existing_ngo_cols:
                try:
                    conn.execute(text(f"ALTER TABLE ngo_details ADD COLUMN {col_name} {col_type}"))
                    print(f"Added column {col_name} to ngo_details")
                except Exception as e:
                    print(f"Note on adding column {col_name} to ngo_details: {e}")

        # NGO Documents missing columns
        existing_doc_cols = {col['name'] for col in inspector.get_columns('ngo_documents')}
        doc_new_cols = {
            "sha256_hash": "VARCHAR",
            "mime_type": "VARCHAR",
            "file_size": "INTEGER",
            "verification_status": "VARCHAR DEFAULT 'PROCESSING'",
            "verification_message": "TEXT",
            "tamper_risk_score": "FLOAT DEFAULT 0.0",
            "tamper_risk_level": "VARCHAR DEFAULT 'LOW'",
            "ocr_text": "TEXT",
            "exif_metadata": "TEXT",
            "gps_latitude": "FLOAT",
            "gps_longitude": "FLOAT",
            "capture_timestamp": "DATETIME",
            "reviewed_by": "INTEGER REFERENCES users(id)",
            "reviewed_at": "DATETIME",
            "review_notes": "TEXT"
        }

        for col_name, col_type in doc_new_cols.items():
            if col_name not in existing_doc_cols:
                try:
                    conn.execute(text(f"ALTER TABLE ngo_documents ADD COLUMN {col_name} {col_type}"))
                    print(f"Added column {col_name} to ngo_documents")
                except Exception as e:
                    print(f"Note on adding column {col_name} to ngo_documents: {e}")

        # Projects missing columns
        if 'projects' in inspector.get_table_names():
            existing_proj_cols = {col['name'] for col in inspector.get_columns('projects')}
            proj_new_cols = {
                "objective": "TEXT",
                "target_beneficiaries": "VARCHAR",
                "number_of_beneficiaries": "INTEGER DEFAULT 0",
                "total_budget": "FLOAT DEFAULT 0.0",
                "funding_received": "FLOAT DEFAULT 0.0",
                "amount_spent": "FLOAT DEFAULT 0.0",
                "remaining_amount": "FLOAT DEFAULT 0.0",
                "ngo_contribution": "FLOAT DEFAULT 0.0",
                "donor_funding": "FLOAT DEFAULT 0.0",
                "government_funding": "FLOAT DEFAULT 0.0",
                "contact_person": "VARCHAR",
                "integrity_status": "VARCHAR DEFAULT 'VERIFIED'",
                "risk_score": "FLOAT DEFAULT 0.0",
                "risk_level": "VARCHAR DEFAULT 'LOW'"
            }
            for col_name, col_type in proj_new_cols.items():
                if col_name not in existing_proj_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE projects ADD COLUMN {col_name} {col_type}"))
                        print(f"Added column {col_name} to projects")
                    except Exception as e:
                        print(f"Note on adding column {col_name} to projects: {e}")


    # Seed demo government registry
    try:
        from app.database import SessionLocal
        from app.services.government_verification import GovernmentVerificationService
        db = SessionLocal()
        try:
            count = GovernmentVerificationService.seed_demo_registry(db)
            print(f"Demo Government Registry verified/seeded ({count} records).")
        finally:
            db.close()
    except Exception as e:
        print(f"Note on demo registry seed: {e}")

if __name__ == "__main__":
    init_db_schema()
    print("Database schema migration & initialization completed successfully.")
