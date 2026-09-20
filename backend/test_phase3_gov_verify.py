import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from app.database import SessionLocal
from app.models import User, UserRole, NGODetail, GovernmentRegistry, AuditLog
from app.services.government_verification import GovernmentVerificationService, DEMO_REGISTRY_DISCLAIMER

client = TestClient(app)

def test_phase3():
    print("=== STARTING PHASE 3 DEMO GOVERNMENT REGISTRY & VERIFICATION TESTS ===")
    db: Session = SessionLocal()
    try:
        # 1. Test Demo Registry Seeding
        seeded_count = GovernmentVerificationService.seed_demo_registry(db)
        assert seeded_count >= 4, "Demo registry must seed at least 4 test records"
        records = db.query(GovernmentRegistry).all()
        print(f"[OK] Test 1 Passed: Demo registry successfully seeded with {len(records)} records")

        # Get or create test user and NGO
        test_user = db.query(User).filter(User.email == "phase3_ngo_test@example.com").first()
        if not test_user:
            test_user = User(
                email="phase3_ngo_test@example.com",
                hashed_password="fakehashedpassword",
                full_name="Phase 3 Test NGO",
                role=UserRole.NGO,
                is_active=True
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)

        test_ngo = db.query(NGODetail).filter(NGODetail.user_id == test_user.id).first()
        if not test_ngo:
            test_ngo = NGODetail(
                user_id=test_user.id,
                org_name="Green Earth Foundation",
                registration_number="REG-2024-001",
                tax_id="TAX-2024-001",
                category="Environment",
                pan="AAATG1234F",
                eighty_g_info="80G-VALID-2024",
                fcra_info="FCRA-VALID-2024",
                gst_number="29AAATG1234F1Z5"
            )
            db.add(test_ngo)
            db.commit()
            db.refresh(test_ngo)

        # 2. Test VERIFIED match scenario (100% match)
        test_ngo.registration_number = "REG-2024-001"
        test_ngo.org_name = "Green Earth Foundation"
        test_ngo.pan = "AAATG1234F"
        test_ngo.eighty_g_info = "80G-VALID-2024"
        test_ngo.fcra_info = "FCRA-VALID-2024"
        test_ngo.gst_number = "29AAATG1234F1Z5"
        db.commit()

        res1 = GovernmentVerificationService.verify_ngo(db, test_ngo)
        assert res1["verification_status"] == "VERIFIED", f"Expected VERIFIED, got {res1['verification_status']}"
        assert res1["government_match_score"] == 100.0, f"Expected 100.0 match score, got {res1['government_match_score']}"
        assert res1["disclaimer"] == DEMO_REGISTRY_DISCLAIMER
        assert test_ngo.government_verification_status == "VERIFIED"
        print("[OK] Test 2 Passed: 100% Match VERIFIED scenario successful")

        # 3. Test PARTIALLY_MATCHED scenario
        test_ngo.registration_number = "REG-2024-002"
        test_ngo.org_name = "Hope Care International"
        test_ngo.pan = "AAATH5678K"
        test_ngo.eighty_g_info = "WRONG-80G-CODE"
        test_ngo.fcra_info = "WRONG-FCRA-CODE"
        db.commit()

        res2 = GovernmentVerificationService.verify_ngo(db, test_ngo)
        assert res2["verification_status"] == "PARTIALLY_MATCHED", f"Expected PARTIALLY_MATCHED, got {res2['verification_status']}"
        assert 50.0 <= res2["government_match_score"] < 90.0
        assert test_ngo.government_verification_status == "PARTIALLY_MATCHED"
        print(f"[OK] Test 3 Passed: PARTIALLY_MATCHED scenario successful (score: {res2['government_match_score']}%)")

        # 4. Test INACTIVE scenario
        test_ngo.registration_number = "REG-2024-003"
        test_ngo.org_name = "Rural Education Upliftment Trust"
        db.commit()

        res3 = GovernmentVerificationService.verify_ngo(db, test_ngo)
        assert res3["verification_status"] == "INACTIVE", f"Expected INACTIVE, got {res3['verification_status']}"
        assert test_ngo.government_verification_status == "INACTIVE"
        print("[OK] Test 4 Passed: INACTIVE registry status scenario successful")

        # 5. Test NOT_VERIFIED scenario (Invalid Reg Number)
        test_ngo.registration_number = "INVALID-REG-99999"
        db.commit()

        res4 = GovernmentVerificationService.verify_ngo(db, test_ngo)
        assert res4["verification_status"] == "NOT_VERIFIED", f"Expected NOT_VERIFIED, got {res4['verification_status']}"
        assert res4["government_match_score"] == 0.0
        assert test_ngo.government_verification_status == "NOT_VERIFIED"
        print("[OK] Test 5 Passed: NOT_VERIFIED scenario for unlisted registration number successful")

        # 6. Test Audit Log Entry
        audit_entry = db.query(AuditLog).filter(
            AuditLog.ngo_id == test_ngo.id,
            AuditLog.action == "GOVERNMENT_VERIFICATION"
        ).order_by(AuditLog.id.desc()).first()
        assert audit_entry is not None, "Audit Log entry must be recorded for verification action"
        print("[OK] Test 6 Passed: Government verification audit log recorded successfully")

        # 7. Test SHA-256 Ledger intact
        ledger_res = client.get("/api/ledger/verify")
        assert ledger_res.status_code == 200
        assert ledger_res.json()["valid"] == True
        print("[OK] Test 7 Passed: SHA-256 Ledger chain intact (valid: true)")

        # 8. Test Demo Public Registry API Endpoint
        records_res = client.get("/api/ngos/demo-government-registry/records")
        assert records_res.status_code == 200
        assert len(records_res.json()) >= 4
        print(f"[OK] Test 8 Passed: GET /api/ngos/demo-government-registry/records endpoint working ({len(records_res.json())} records returned)")

        print("\n==================================================")
        print("ALL PHASE 3 GOVERNMENT VERIFICATION TESTS PASSED PERFECTLY!")
        print("==================================================")

    finally:
        db.close()

if __name__ == "__main__":
    import traceback
    try:
        test_phase3()
    except Exception as e:
        with open("test_phase3_error.log", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        print("EXCEPTION ENCOUNTERED IN PHASE 3. LOGGED TO test_phase3_error.log")
        raise e
