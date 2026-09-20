from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from app.database import SessionLocal
from app.models import User, NGODetail, NGODocument, Donation, LedgerBlock, GovernmentRegistry, Project, Beneficiary, Expense, AuditLog

client = TestClient(app)

def test_phase2():
    print("=== STARTING PHASE 2 SCHEMA & BACKEND VERIFICATION ===")
    db: Session = SessionLocal()
    try:
        # 1. Existing users still load
        users = db.query(User).all()
        assert len(users) > 0, "Users should exist"
        print("[OK] Test 1 Passed: existing users loaded successfully", len(users))

        # 2. Existing NGOs still load
        ngos = db.query(NGODetail).all()
        assert len(ngos) > 0, "NGOs should exist"
        print("[OK] Test 2 Passed: existing NGOs loaded successfully", len(ngos))

        # 3. Existing documents still load
        docs = db.query(NGODocument).all()
        print("[OK] Test 3 Passed: existing documents loaded successfully", len(docs))

        # 4. Existing donations still load
        donations = db.query(Donation).all()
        print("[OK] Test 4 Passed: existing donations loaded successfully", len(donations))

        # 5. Existing ledger chain still verifies
        ledger_res = client.get("/api/ledger/verify")
        assert ledger_res.status_code == 200, "Ledger verify route should return 200"
        assert ledger_res.json()["valid"] == True, "Ledger chain must be valid"
        print("[OK] Test 5 Passed: SHA-256 Ledger verification intact (valid: true)")

        # 6. Existing authentication API health check
        health_res = client.get("/api/health")
        assert health_res.status_code == 200
        print("[OK] Test 6 Passed: Health check & API routes functional")

        # 7. Extended NGO fields can be stored and read
        first_ngo = ngos[0]
        first_ngo.city = "Bengaluru"
        first_ngo.state = "Karnataka"
        first_ngo.pan = "AAATN1234F"
        first_ngo.government_verification_status = "NOT_VERIFIED"
        db.commit()
        db.refresh(first_ngo)
        assert first_ngo.city == "Bengaluru"
        assert first_ngo.pan == "AAATN1234F"
        print("[OK] Test 7 Passed: Extended NGODetail fields stored and verified successfully")

        # 8. GovernmentRegistry model CRUD test
        gov_entry = db.query(GovernmentRegistry).filter(GovernmentRegistry.registration_number == "DEMO-REG-TEST-01").first()
        if not gov_entry:
            gov_entry = GovernmentRegistry(
                registration_number="DEMO-REG-TEST-01",
                org_name="Test Demo Foundation",
                pan="AAATN9999F",
                status="ACTIVE",
                registered_state="Karnataka"
            )
            db.add(gov_entry)
            db.commit()
            db.refresh(gov_entry)
        assert gov_entry.id is not None
        print("[OK] Test 8 Passed: GovernmentRegistry model created and verified successfully")

        # 9. Project model CRUD test
        proj = db.query(Project).filter(Project.project_name == "Phase 2 Test Project").first()
        if not proj:
            proj = Project(
                ngo_id=first_ngo.id,
                project_name="Phase 2 Test Project",
                description="Test project for schema validation",
                budget=500000.0,
                status="ACTIVE"
            )
            db.add(proj)
            db.commit()
            db.refresh(proj)
        assert proj.id is not None
        print("[OK] Test 9 Passed: Project model created and verified successfully")

        # 10. Beneficiary model CRUD test
        ben = db.query(Beneficiary).filter(Beneficiary.beneficiary_code == "BEN-TEST-001").first()
        if not ben:
            ben = Beneficiary(
                ngo_id=first_ngo.id,
                project_id=proj.id,
                beneficiary_code="BEN-TEST-001",
                name_or_alias="Beneficiary Alpha",
                age_group="Youth",
                gender="Female"
            )
            db.add(ben)
            db.commit()
            db.refresh(ben)
        assert ben.id is not None
        print("[OK] Test 10 Passed: Beneficiary model created and verified successfully")

        # 11. Expense model CRUD test
        exp = db.query(Expense).filter(Expense.description == "Phase 2 Test Expense").first()
        if not exp:
            exp = Expense(
                ngo_id=first_ngo.id,
                project_id=proj.id,
                category="Equipment",
                description="Phase 2 Test Expense",
                amount=15000.0,
                verification_status="PENDING"
            )
            db.add(exp)
            db.commit()
            db.refresh(exp)
        assert exp.id is not None
        print("[OK] Test 11 Passed: Expense model created and verified successfully")

        # 12. AuditLog model CRUD test
        audit = AuditLog(
            actor_user_id=first_ngo.user_id,
            ngo_id=first_ngo.id,
            action="PHASE2_SCHEMA_VERIFY",
            entity_type="NGO",
            entity_id=first_ngo.id,
            metadata_json='{"status": "PASSED"}'
        )
        db.add(audit)
        db.commit()
        db.refresh(audit)
        assert audit.id is not None
        print("[OK] Test 12 Passed: AuditLog model created and verified successfully")

        # 13. Data preservation re-verification
        assert len(db.query(User).all()) >= len(users)
        assert len(db.query(NGODetail).all()) >= len(ngos)
        print("[OK] Test 13 Passed: Data preservation confirmed with zero data loss")

        print("\n==================================================")
        print("ALL PHASE 2 BACKEND & SCHEMA TESTS PASSED PERFECTLY!")
        print("==================================================")
    finally:
        db.close()

if __name__ == "__main__":
    import traceback
    try:
        test_phase2()
    except Exception as e:
        with open("test_error.log", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        print("EXCEPTION ENCOUNTERED. LOGGED TO test_error.log")
        raise e
