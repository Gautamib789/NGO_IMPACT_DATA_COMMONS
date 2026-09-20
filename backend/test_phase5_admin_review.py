import json
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from app.database import SessionLocal
from app.models import User, UserRole, NGODetail, NGODocument, AuditLog
from app.core.security import create_access_token

client = TestClient(app)

def test_phase5():
    print("=== STARTING PHASE 5 ADMIN DOCUMENT REVIEW WORKFLOW & RBAC TESTS ===")
    db: Session = SessionLocal()
    try:
        # 1. Setup Test Users: Admin, NGO, Donor
        admin_user = db.query(User).filter(User.email == "phase5_admin@example.com").first()
        if not admin_user:
            admin_user = User(
                email="phase5_admin@example.com",
                hashed_password="fakehashedpassword",
                full_name="Phase 5 Admin",
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

        ngo_user = db.query(User).filter(User.email == "phase5_ngo@example.com").first()
        if not ngo_user:
            ngo_user = User(
                email="phase5_ngo@example.com",
                hashed_password="fakehashedpassword",
                full_name="Phase 5 NGO User",
                role=UserRole.NGO,
                is_active=True
            )
            db.add(ngo_user)
            db.commit()
            db.refresh(ngo_user)

        donor_user = db.query(User).filter(User.email == "phase5_donor@example.com").first()
        if not donor_user:
            donor_user = User(
                email="phase5_donor@example.com",
                hashed_password="fakehashedpassword",
                full_name="Phase 5 Donor User",
                role=UserRole.DONOR,
                is_active=True
            )
            db.add(donor_user)
            db.commit()
            db.refresh(donor_user)

        # Setup Test NGO and Document
        test_ngo = db.query(NGODetail).filter(NGODetail.user_id == ngo_user.id).first()
        if not test_ngo:
            test_ngo = NGODetail(
                user_id=ngo_user.id,
                org_name="Phase 5 Admin Inspection Trust",
                registration_number="REG-PH5-500",
                tax_id="TAX-PH5-500",
                category="Health"
            )
            db.add(test_ngo)
            db.commit()
            db.refresh(test_ngo)

        test_doc = db.query(NGODocument).filter(NGODocument.ngo_id == test_ngo.id).first()
        if not test_doc:
            test_doc = NGODocument(
                ngo_id=test_ngo.id,
                document_type="80G_CERTIFICATE",
                file_name="80g_certificate.pdf",
                file_path="/uploads/80g_certificate.pdf",
                sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                mime_type="application/pdf",
                file_size=1024,
                verification_status="NEEDS_ADMIN_REVIEW",
                verification_message="Flagged for manual review due to software editing tag.",
                tamper_risk_score=35.0,
                tamper_risk_level="MEDIUM",
                ocr_text="80G Certificate for Phase 5 Admin Inspection Trust",
                exif_metadata="Software tag: Photoshop found"
            )
            db.add(test_doc)
            db.commit()
            db.refresh(test_doc)
        else:
            test_doc.verification_status = "NEEDS_ADMIN_REVIEW"
            db.commit()

        # Generate JWT Tokens with user.id as sub
        admin_token = create_access_token(
            subject=str(admin_user.id),
            role=admin_user.role.value,
            otp_verified=True
        )
        ngo_token = create_access_token(
            subject=str(ngo_user.id),
            role=ngo_user.role.value,
            otp_verified=True
        )
        donor_token = create_access_token(
            subject=str(donor_user.id),
            role=donor_user.role.value,
            otp_verified=True
        )

        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        ngo_headers = {"Authorization": f"Bearer {ngo_token}"}
        donor_headers = {"Authorization": f"Bearer {donor_token}"}

        # 2. Test RBAC Access Restrictions
        ngo_res = client.get("/api/admin/documents/pending", headers=ngo_headers)
        assert ngo_res.status_code == 403, f"NGO user must be denied admin endpoints (got {ngo_res.status_code})"
        print("[OK] Test 1 Passed: NGO user correctly denied admin access (403 Forbidden)")

        donor_res = client.get("/api/admin/documents/pending", headers=donor_headers)
        assert donor_res.status_code == 403, f"Donor user must be denied admin endpoints (got {donor_res.status_code})"
        print("[OK] Test 2 Passed: Donor user correctly denied admin access (403 Forbidden)")

        unauth_res = client.get("/api/admin/documents/pending")
        assert unauth_res.status_code in [401, 403], f"Unauthenticated request denied (got {unauth_res.status_code})"
        print("[OK] Test 3 Passed: Unauthenticated request correctly denied (401/403)")

        # 3. Test Admin Inspection Endpoint
        admin_list_res = client.get("/api/admin/documents/pending", headers=admin_headers)
        assert admin_list_res.status_code == 200, f"Failed: {admin_list_res.json()}"
        docs_list = admin_list_res.json()
        assert len(docs_list) >= 1
        print(f"[OK] Test 4 Passed: Admin pending document list retrieved successfully ({len(docs_list)} pending docs)")

        inspect_res = client.get(f"/api/admin/documents/{test_doc.id}", headers=admin_headers)
        assert inspect_res.status_code == 200, f"Failed: {inspect_res.json()}"
        doc_details = inspect_res.json()
        assert doc_details["id"] == test_doc.id
        assert doc_details["sha256_hash"] == test_doc.sha256_hash
        assert doc_details["tamper_risk_score"] == 35.0
        assert "Photoshop" in doc_details["exif_metadata"]
        print("[OK] Test 5 Passed: Detailed admin document inspection API verified")

        # 4. Test Admin Review Decision: APPROVE
        approve_res = client.post(
            f"/api/admin/documents/{test_doc.id}/review",
            headers=admin_headers,
            json={"decision": "APPROVE", "notes": "Verified authentic seal after manual inspection."}
        )
        assert approve_res.status_code == 200, f"Failed: {approve_res.json()}"
        approved_doc = approve_res.json()
        assert approved_doc["verification_status"] == "VERIFIED"
        assert approved_doc["reviewed_by_email"] == admin_user.email
        assert "Verified authentic" in approved_doc["review_notes"]
        print("[OK] Test 6 Passed: Admin APPROVE decision recorded and status updated to VERIFIED")

        # 5. Test Admin Review Decision: REQUEST_CLARIFICATION
        clarify_res = client.post(
            f"/api/admin/documents/{test_doc.id}/review",
            headers=admin_headers,
            json={"decision": "REQUEST_CLARIFICATION", "notes": "Scan resolution is low. Please upload high-res PDF."}
        )
        assert clarify_res.status_code == 200, f"Failed: {clarify_res.json()}"
        clarified_doc = clarify_res.json()
        assert clarified_doc["verification_status"] == "REQUEST_CLARIFICATION"
        print("[OK] Test 7 Passed: Admin REQUEST_CLARIFICATION decision recorded")

        # 6. Test Admin Review Decision: REJECT
        reject_res = client.post(
            f"/api/admin/documents/{test_doc.id}/review",
            headers=admin_headers,
            json={"decision": "REJECT", "notes": "Document rejected due to non-matching tax parameters."}
        )
        assert reject_res.status_code == 200, f"Failed: {reject_res.json()}"
        rejected_doc = reject_res.json()
        assert rejected_doc["verification_status"] == "REJECTED"
        print("[OK] Test 8 Passed: Admin REJECT decision recorded")

        # 7. Test Audit Log Entry
        audit_entry = db.query(AuditLog).filter(
            AuditLog.ngo_id == test_ngo.id,
            AuditLog.action == "ADMIN_DOCUMENT_REVIEW"
        ).order_by(AuditLog.id.desc()).first()
        assert audit_entry is not None, "Audit Log entry must be recorded for admin document review"
        audit_meta = json.loads(audit_entry.metadata_json)
        assert audit_meta["decision"] == "REJECT"
        assert audit_meta["admin_email"] == admin_user.email
        print("[OK] Test 9 Passed: Admin document review AuditLog recorded successfully")

        # 8. Test Admin Dashboard Stats Update
        stats_res = client.get("/api/admin/stats", headers=admin_headers)
        assert stats_res.status_code == 200, f"Failed: {stats_res.json()}"
        assert "pending_documents_for_review" in stats_res.json()
        print("[OK] Test 10 Passed: Admin dashboard stats updated with pending document metrics")

        # 9. Test Blockchain Ledger Integrity
        ledger_res = client.get("/api/ledger/verify")
        assert ledger_res.status_code == 200
        assert ledger_res.json()["valid"] == True
        print("[OK] Test 11 Passed: SHA-256 Blockchain Ledger verification intact (valid: true)")

        print("\n==================================================")
        print("ALL PHASE 5 ADMIN DOCUMENT REVIEW TESTS PASSED PERFECTLY!")
        print("==================================================")

    finally:
        db.close()

if __name__ == "__main__":
    import traceback
    try:
        test_phase5()
    except Exception as e:
        with open("test_phase5_error.log", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        print("EXCEPTION ENCOUNTERED IN PHASE 5. LOGGED TO test_phase5_error.log")
        raise e
