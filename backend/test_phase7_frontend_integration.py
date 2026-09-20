import io
import os
import sys
import traceback
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from app.database import SessionLocal
from app.models import User, UserRole, NGODetail, Project, Beneficiary, Expense, AuditLog
from app.models.otp import OtpCode, OTPPurpose
from app.models.ngo import NGOStatus
from app.core.security import create_access_token, get_password_hash

client = TestClient(app)

def test_phase7():
    print("=== STARTING PHASE 7 FRONTEND API INTEGRATION & NGO DASHBOARD TESTS ===")
    db: Session = SessionLocal()
    try:
        # 1. Setup Test NGO User
        ngo_email = "phase7_ngo@example.com"
        password = "NgoPass123!"

        ngo_user = db.query(User).filter(User.email == ngo_email).first()
        if not ngo_user:
            ngo_user = User(
                email=ngo_email,
                hashed_password=get_password_hash(password),
                full_name="Phase 7 Test NGO Admin",
                role=UserRole.NGO,
                is_active=True
            )
            db.add(ngo_user)
            db.commit()
            db.refresh(ngo_user)

        ngo_detail = db.query(NGODetail).filter(NGODetail.user_id == ngo_user.id).first()
        if not ngo_detail:
            ngo_detail = NGODetail(
                user_id=ngo_user.id,
                org_name="Phase 7 Impact Foundation",
                registration_number="REG-2026-PHASE7",
                tax_id="PAN7777777",
                category="Healthcare",
                mission_statement="Providing healthcare and medical relief.",
                website="https://phase7ngo.org",
                address="77 Phase 7 Ave, Mysuru",
                status=NGOStatus.APPROVED,
                transparency_score=88.5,
                doc_completeness_score=90.0
            )
            db.add(ngo_detail)
            db.commit()
            db.refresh(ngo_detail)

        login_res = client.post("/api/auth/login", json={"email": ngo_email, "password": password})
        assert login_res.status_code == 200, f"Login failed: {login_res.json()}"
        login_data = login_res.json()
        
        jwt_token = create_access_token(subject=str(ngo_user.id), role=UserRole.NGO.value, otp_verified=True)
        headers = {"Authorization": f"Bearer {jwt_token}"}
        print("[OK] Test 1 Passed: NGO Authentication & JWT Token verified")

        # 3. Test NGO Profile GET and PUT endpoints (NGO Profile Tab)
        prof_res = client.get("/api/ngos/profile", headers=headers)
        assert prof_res.status_code == 200, f"GET profile failed: {prof_res.json()}"
        print("[OK] Test 2 Passed: GET /api/ngos/profile loaded organization dossier")

        put_res = client.put("/api/ngos/profile", headers=headers, json={
            "org_name": "Phase 7 Impact Foundation Updated",
            "registration_number": "REG-2026-PHASE7",
            "tax_id": "PAN7777777",
            "category": "Healthcare",
            "mission_statement": "Providing verified medical relief and clean water.",
            "website": "https://phase7ngo.org",
            "address": "77 Phase 7 Ave, Mysuru"
        })
        assert put_res.status_code == 200, f"PUT profile failed: {put_res.json()}"
        assert put_res.json()["org_name"] == "Phase 7 Impact Foundation Updated"
        print("[OK] Test 3 Passed: PUT /api/ngos/me updated organization profile")

        # 4. Test Government Registry Verification Endpoints (Gov Verification Tab)
        gov_res = client.post("/api/ngos/government-verification", headers=headers)
        assert gov_res.status_code == 200, f"Gov verification failed: {gov_res.json()}"
        gov_data = gov_res.json()
        assert "verification_status" in gov_data
        assert "field_matches" in gov_data
        print(f"[OK] Test 4 Passed: POST /api/ngo/verify-government returned status '{gov_data['verification_status']}'")

        # 5. Test Compliance Document Upload & Hash Calculation (Documents Tab)
        sample_doc = b"%PDF-1.4 80G Tax Exemption Certificate 2026 Phase 7 %%EOF"
        doc_res = client.post(
            "/api/ngos/upload-document",
            headers=headers,
            data={"document_type": "80G_CERTIFICATE"},
            files={"file": ("80G_cert_p7.pdf", io.BytesIO(sample_doc), "application/pdf")}
        )
        assert doc_res.status_code == 200, f"Document upload failed: {doc_res.json()}"
        doc_out = doc_res.json()
        assert doc_out.get("sha256_hash") is not None
        print(f"[OK] Test 5 Passed: Compliance document uploaded and hashed (SHA-256: {doc_out['sha256_hash'][:16]}...)")

        # 6. Test Project Management CRUD (Projects Tab)
        proj_res = client.post(
            "/api/ngo/projects",
            headers=headers,
            json={
                "project_name": "Phase 7 Rural Health Clinic",
                "description": "Mobile health unit servicing rural areas.",
                "category": "Healthcare",
                "budget": 75000.0,
                "location": "Mysuru District",
                "latitude": 12.2958,
                "longitude": 76.6394,
                "target_beneficiaries": 800,
                "status": "ACTIVE"
            }
        )
        assert proj_res.status_code == 200, f"Project create failed: {proj_res.json()}"
        proj = proj_res.json()
        project_id = proj["id"]
        print(f"[OK] Test 6 Passed: Created project ID {project_id} (Budget: ₹{proj['budget']})")

        # 7. Test Beneficiary Registration with Masked ID (Beneficiaries Tab)
        ben_res = client.post(
            "/api/ngo/beneficiaries",
            headers=headers,
            json={
                "project_id": project_id,
                "name_or_alias": "Village Resident Cooperative #7",
                "age_group": "Adults",
                "gender": "Female",
                "location": "Mysuru Rural"
            }
        )
        assert ben_res.status_code == 200, f"Beneficiary create failed: {ben_res.json()}"
        ben = ben_res.json()
        assert ben["beneficiary_code"].startswith("BEN-")
        print(f"[OK] Test 7 Passed: Registered beneficiary with masked identifier code {ben['beneficiary_code']}")

        # 8. Test Expense Claim & Receipt Upload (Expenses Tab)
        exp_res = client.post(
            "/api/ngo/expenses",
            headers=headers,
            json={
                "project_id": project_id,
                "category": "Medical Supplies",
                "description": "Vaccines and medical diagnostic kits",
                "amount": 15000.0
            }
        )
        assert exp_res.status_code == 200, f"Expense create failed: {exp_res.json()}"
        exp = exp_res.json()
        expense_id = exp["id"]

        sample_receipt = b"%PDF-1.5 Medical Diagnostic Invoice #8899 Amount $15,000 %%EOF"
        rec_res = client.post(
            f"/api/ngo/expenses/{expense_id}/upload-receipt",
            headers=headers,
            files={"file": ("med_invoice.pdf", io.BytesIO(sample_receipt), "application/pdf")}
        )
        assert rec_res.status_code == 200, f"Receipt upload failed: {rec_res.json()}"
        rec_out = rec_res.json()
        assert rec_out["receipt_sha256"] is not None
        assert rec_out["verification_status"] == "VERIFIED"
        print(f"[OK] Test 8 Passed: Expense claim created & receipt SHA-256 hash verified ({rec_out['receipt_sha256'][:16]}...)")

        # 9. Test Fund Utilization Ratio Calculation (Fund Utilization Tab)
        p_check = client.get(f"/api/ngo/projects/{project_id}", headers=headers)
        assert p_check.status_code == 200
        p_data = p_check.json()
        assert p_data["total_expenses_claimed"] == 15000.0
        assert p_data["fund_utilization_ratio"] == 20.0 # (15000 / 75000) * 100
        print(f"[OK] Test 9 Passed: Fund utilization calculation verified (Ratio: {p_data['fund_utilization_ratio']}%)")

        # 10. Test Public Transparency Integration Endpoint
        ngo_detail.status = NGOStatus.APPROVED
        db.commit()

        pub_res = client.get(f"/api/public/ngos/{ngo_detail.id}/projects")
        assert pub_res.status_code == 200
        pub_list = pub_res.json()
        assert len(pub_list) > 0
        assert pub_list[0]["fund_utilization_ratio"] == 20.0
        print("[OK] Test 10 Passed: Public transparency portal integration verified")

        # 11. Test Ledger Integrity Verification
        ledger_res = client.get("/api/ledger/verify")
        assert ledger_res.status_code == 200
        assert ledger_res.json()["valid"] == True
        print("[OK] Test 11 Passed: Blockchain SHA-256 Ledger integrity verified (valid: true)")

        print("\n==================================================")
        print("ALL PHASE 7 NGO FRONTEND DASHBOARD INTEGRATION TESTS PASSED PERFECTLY!")
        print("==================================================")

    finally:
        db.close()

if __name__ == "__main__":
    try:
        test_phase7()
    except Exception as e:
        with open("test_phase7_error.log", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        print("EXCEPTION ENCOUNTERED IN PHASE 7. LOGGED TO test_phase7_error.log")
        raise e
