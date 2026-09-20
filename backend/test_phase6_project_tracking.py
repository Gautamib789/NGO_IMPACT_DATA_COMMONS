import io
import json
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from app.database import SessionLocal
from app.models import User, UserRole, NGODetail, Project, Beneficiary, Expense, AuditLog
from app.core.security import create_access_token

client = TestClient(app)

def test_phase6():
    print("=== STARTING PHASE 6 PROJECT, BENEFICIARY & EXPENSE TRACKING TESTS ===")
    db: Session = SessionLocal()
    try:
        # 1. Setup Test NGO A and Test NGO B users
        ngo_user_a = db.query(User).filter(User.email == "phase6_ngo_a@example.com").first()
        if not ngo_user_a:
            ngo_user_a = User(
                email="phase6_ngo_a@example.com",
                hashed_password="fakehashedpassword",
                full_name="NGO A Admin",
                role=UserRole.NGO,
                is_active=True
            )
            db.add(ngo_user_a)
            db.commit()
            db.refresh(ngo_user_a)

        ngo_detail_a = db.query(NGODetail).filter(NGODetail.user_id == ngo_user_a.id).first()
        if not ngo_detail_a:
            ngo_detail_a = NGODetail(
                user_id=ngo_user_a.id,
                org_name="Clean Oceans Alliance",
                registration_number="REG-PH6-NGO-A",
                tax_id="TAX-PH6-NGO-A",
                category="Environment"
            )
            db.add(ngo_detail_a)
            db.commit()
            db.refresh(ngo_detail_a)

        ngo_user_b = db.query(User).filter(User.email == "phase6_ngo_b@example.com").first()
        if not ngo_user_b:
            ngo_user_b = User(
                email="phase6_ngo_b@example.com",
                hashed_password="fakehashedpassword",
                full_name="NGO B Admin",
                role=UserRole.NGO,
                is_active=True
            )
            db.add(ngo_user_b)
            db.commit()
            db.refresh(ngo_user_b)

        ngo_detail_b = db.query(NGODetail).filter(NGODetail.user_id == ngo_user_b.id).first()
        if not ngo_detail_b:
            ngo_detail_b = NGODetail(
                user_id=ngo_user_b.id,
                org_name="Urban Education Initiative",
                registration_number="REG-PH6-NGO-B",
                tax_id="TAX-PH6-NGO-B",
                category="Education"
            )
            db.add(ngo_detail_b)
            db.commit()
            db.refresh(ngo_detail_b)

        token_a = create_access_token(subject=str(ngo_user_a.id), role=UserRole.NGO.value, otp_verified=True)
        token_b = create_access_token(subject=str(ngo_user_b.id), role=UserRole.NGO.value, otp_verified=True)

        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # 2. Test Project CRUD (NGO A)
        invalid_p_res = client.post(
            "/api/ngo/projects",
            headers=headers_a,
            json={"project_name": "Coastal Cleanup", "budget": -500.0, "category": "Environment"}
        )
        assert invalid_p_res.status_code in [400, 422], "Negative budget must be rejected"
        print("[OK] Test 1 Passed: Invalid project budget rejected (400/422 Bad Request)")

        p1_res = client.post(
            "/api/ngo/projects",
            headers=headers_a,
            json={
                "project_name": "Coastal Plastic Cleanup Project",
                "description": "Deploying floating collection booms.",
                "category": "Environment",
                "budget": 50000.0,
                "target_beneficiaries": 1000,
                "latitude": 13.0827,
                "longitude": 80.2707
            }
        )
        assert p1_res.status_code == 200, f"Failed: {p1_res.json()}"
        p1 = p1_res.json()
        assert p1["project_name"] == "Coastal Plastic Cleanup Project"
        assert p1["budget"] == 50000.0
        assert p1["ngo_id"] == ngo_detail_a.id
        project_a_id = p1["id"]
        print(f"[OK] Test 2 Passed: NGO A created Project ID {project_a_id} successfully")

        # 3. Test Ownership Isolation: NGO B trying to update NGO A's project
        stolen_p_res = client.put(
            f"/api/ngo/projects/{project_a_id}",
            headers=headers_b,
            json={"project_name": "Hijacked Project"}
        )
        assert stolen_p_res.status_code == 403, "NGO B must not modify NGO A's project"
        print("[OK] Test 3 Passed: Cross-NGO project modification denied (403 Forbidden)")

        # 4. Test Beneficiary CRUD & Privacy Protection (NGO A)
        b1_res = client.post(
            "/api/ngo/beneficiaries",
            headers=headers_a,
            json={
                "project_id": project_a_id,
                "name_or_alias": "Fisherman Cooperative #4",
                "age_group": "Adults",
                "gender": "Male",
                "location": "Chennai Coast"
            }
        )
        assert b1_res.status_code == 200, f"Failed: {b1_res.json()}"
        b1 = b1_res.json()
        assert b1["beneficiary_code"].startswith("BEN-")
        assert b1["ngo_id"] == ngo_detail_a.id
        b1_id = b1["id"]
        print(f"[OK] Test 4 Passed: Beneficiary created with masked code {b1['beneficiary_code']}")

        # 5. Test Ownership Isolation: NGO B trying to access/delete NGO A's beneficiary
        cross_b_res = client.get(f"/api/ngo/beneficiaries/{b1_id}", headers=headers_b)
        assert cross_b_res.status_code == 403, "NGO B must not access NGO A's beneficiary details"
        print("[OK] Test 5 Passed: Cross-NGO beneficiary inspection denied (403 Forbidden)")

        # 6. Test Expense CRUD & Receipt Upload (NGO A)
        invalid_exp_res = client.post(
            "/api/ngo/expenses",
            headers=headers_a,
            json={"project_id": project_a_id, "category": "Equipment", "amount": 0.0}
        )
        assert invalid_exp_res.status_code in [400, 422], "Zero amount expense must be rejected"
        print("[OK] Test 6 Passed: Invalid zero/negative expense amount rejected (400/422 Bad Request)")

        exp1_res = client.post(
            "/api/ngo/expenses",
            headers=headers_a,
            json={
                "project_id": project_a_id,
                "category": "Equipment",
                "description": "Purchased 2 floating debris containment barriers",
                "amount": 12500.0
            }
        )
        assert exp1_res.status_code == 200, f"Failed: {exp1_res.json()}"
        exp1 = exp1_res.json()
        assert exp1["amount"] == 12500.0
        exp1_id = exp1["id"]
        print(f"[OK] Test 7 Passed: Expense claim created for ${exp1['amount']}")

        # Receipt upload
        dummy_receipt = b"%PDF-1.5 Receipt for 2 Containment Barriers Amount $12,500 %%EOF"
        upload_res = client.post(
            f"/api/ngo/expenses/{exp1_id}/upload-receipt",
            headers=headers_a,
            files={"file": ("barrier_invoice.pdf", io.BytesIO(dummy_receipt), "application/pdf")}
        )
        assert upload_res.status_code == 200, f"Failed: {upload_res.json()}"
        receipt_out = upload_res.json()
        assert receipt_out["receipt_sha256"] is not None
        assert receipt_out["verification_status"] == "VERIFIED"
        print(f"[OK] Test 8 Passed: Receipt file uploaded, SHA-256 calculated ({receipt_out['receipt_sha256'][:16]}...)")

        # 7. Test Fund-Flow Utilization Calculations
        p_check_res = client.get(f"/api/ngo/projects/{project_a_id}", headers=headers_a)
        assert p_check_res.status_code == 200
        p_data = p_check_res.json()
        assert p_data["total_expenses_claimed"] == 12500.0
        assert p_data["fund_utilization_ratio"] == 25.0 # (12500 / 50000) * 100
        print(f"[OK] Test 9 Passed: Fund utilization calculation verified (Ratio: {p_data['fund_utilization_ratio']}%)")

        # 8. Test Public Transparency Endpoint
        ngo_detail_a.status = "APPROVED"
        db.commit()

        pub_p_res = client.get(f"/api/public/ngos/{ngo_detail_a.id}/projects")
        assert pub_p_res.status_code == 200
        pub_list = pub_p_res.json()
        assert len(pub_list) >= 1
        assert pub_list[0]["fund_utilization_ratio"] == 25.0
        print("[OK] Test 10 Passed: Public transparency project API verified")

        # 9. Test Audit Logs Created
        audits = db.query(AuditLog).filter(AuditLog.ngo_id == ngo_detail_a.id).all()
        actions = [a.action for a in audits]
        assert "CREATE_PROJECT" in actions
        assert "CREATE_BENEFICIARY" in actions
        assert "CREATE_EXPENSE" in actions
        assert "UPLOAD_EXPENSE_RECEIPT" in actions
        print(f"[OK] Test 11 Passed: AuditLog entries verified ({len(audits)} audit records)")

        # 10. Test Ledger Verification
        ledger_res = client.get("/api/ledger/verify")
        assert ledger_res.status_code == 200
        assert ledger_res.json()["valid"] == True
        print("[OK] Test 12 Passed: SHA-256 Blockchain Ledger integrity verified (valid: true)")

        print("\n==================================================")
        print("ALL PHASE 6 PROJECT & EXPENSE TRACKING TESTS PASSED PERFECTLY!")
        print("==================================================")

    finally:
        db.close()

if __name__ == "__main__":
    import traceback
    try:
        test_phase6()
    except Exception as e:
        with open("test_phase6_error.log", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        print("EXCEPTION ENCOUNTERED IN PHASE 6. LOGGED TO test_phase6_error.log")
        raise e
