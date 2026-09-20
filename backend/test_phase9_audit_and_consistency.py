import unittest
import json
import os
import sys
from fastapi.testclient import TestClient

# Add backend root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from main import app
from app.database import Base, engine, SessionLocal
from app.models.user import User, UserRole
from app.models.ngo import NGODetail, NGODocument, NGOStatus
from app.models.audit import AuditLog
from app.models.project import Project
from app.models.fraud import FraudFlag
from app.services.ledger_engine import LedgerEngine
from app.services.fraud_engine import FraudDetectionEngine


class TestPhase9AuditAndConsistency(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)
        db = SessionLocal()
        test_emails = [
            "ngo_audit_test@example.com",
            "ngo_unauth_audit@example.com",
            "admin_audit_master@example.com",
            "transparency_consistency@example.com",
            "ngo_owner_a@example.com",
            "ngo_owner_b@example.com"
        ]
        test_users = db.query(User).filter(User.email.in_(test_emails)).all()
        for u in test_users:
            ngo = db.query(NGODetail).filter(NGODetail.user_id == u.id).first()
            if ngo:
                db.query(AuditLog).filter(AuditLog.ngo_id == ngo.id).delete()
                db.query(NGODocument).filter(NGODocument.ngo_id == ngo.id).delete()
                db.query(Project).filter(Project.ngo_id == ngo.id).delete()
                db.query(NGODetail).filter(NGODetail.id == ngo.id).delete()
            db.delete(u)
        db.commit()
        db.close()

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        # Create fresh session for each test
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def _get_auth_header(self, email, password, role_str="NGO"):
        from app.core.security import create_access_token, get_password_hash
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            role_enum = UserRole.ADMIN if role_str == "ADMIN" else (UserRole.NGO if role_str == "NGO" else UserRole.DONOR)
            user = User(
                email=email,
                hashed_password=get_password_hash(password),
                full_name=f"Test User {email}",
                role=role_enum,
                is_active=True
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

        token = create_access_token(subject=str(user.id), role=user.role.value, otp_verified=True)
        return {"Authorization": f"Bearer {token}"}

    def test_01_audit_log_coverage_for_ngo_and_admin_actions(self):
        """
        Tests that critical NGO and Admin actions generate valid AuditLog records with safe metadata.
        """
        ngo_headers = self._get_auth_header("ngo_audit_test@example.com", "Password123!", "NGO")

        # 1. Register NGO Profile -> Should trigger PROFILE_CREATE audit
        reg_ngo_res = self.client.post("/api/ngos/register", json={
            "org_name": "Audit Test Foundation",
            "registration_number": "REG-AUDIT-999",
            "tax_id": "TAX-AUDIT-999",
            "category": "Education",
            "mission_statement": "Empowering communities through education.",
            "website": "https://audittest.org",
            "address": "123 Audit Way, Green City"
        }, headers=ngo_headers)
        self.assertEqual(reg_ngo_res.status_code, 200)
        ngo_id = reg_ngo_res.json()["id"]

        # Check AuditLog table for PROFILE_CREATE
        self.db.commit()
        profile_audit = self.db.query(AuditLog).filter(
            AuditLog.ngo_id == ngo_id,
            AuditLog.action == "PROFILE_CREATE"
        ).first()
        self.assertIsNotNone(profile_audit, "PROFILE_CREATE audit log missing")
        meta = json.loads(profile_audit.metadata_json)
        self.assertEqual(meta.get("org_name"), "Audit Test Foundation")
        # Ensure no sensitive credentials/tokens in metadata
        self.assertNotIn("password", profile_audit.metadata_json.lower())
        self.assertNotIn("access_token", profile_audit.metadata_json.lower())

        # 2. Upload Document -> Should trigger DOCUMENT_UPLOAD audit
        sample_file_content = b"Simulated 12A Tax Exemption Certificate for Audit Test"
        files = {
            "file": ("tax_cert.pdf", sample_file_content, "application/pdf")
        }
        doc_res = self.client.post(
            "/api/ngos/upload-document",
            data={"document_type": "12A"},
            files=files,
            headers=ngo_headers
        )
        self.assertEqual(doc_res.status_code, 200)

        self.db.commit()
        doc_audit = self.db.query(AuditLog).filter(
            AuditLog.ngo_id == ngo_id,
            AuditLog.action == "DOCUMENT_UPLOAD"
        ).first()
        self.assertIsNotNone(doc_audit, "DOCUMENT_UPLOAD audit log missing")
        doc_meta = json.loads(doc_audit.metadata_json)
        self.assertEqual(doc_meta.get("document_type"), "12A")
        self.assertIn("sha256", doc_meta)

        # 3. Create Project -> Should trigger PROJECT_CREATE audit
        proj_res = self.client.post("/api/ngo/projects", json={
            "project_name": "Clean Water Initiative",
            "description": "Providing clean water to remote villages.",
            "category": "Environment",
            "budget": 50000.0,
            "target_beneficiaries": 100
        }, headers=ngo_headers)
        self.assertEqual(proj_res.status_code, 200)
        proj_id = proj_res.json()["id"]

        self.db.commit()
        proj_audit = self.db.query(AuditLog).filter(
            AuditLog.ngo_id == ngo_id,
            AuditLog.action == "CREATE_PROJECT"
        ).first()
        self.assertIsNotNone(proj_audit, "CREATE_PROJECT audit log missing")
        self.assertEqual(proj_audit.entity_id, proj_id)

        # 4. Create Expense -> Should trigger CREATE_EXPENSE audit
        exp_res = self.client.post("/api/ngo/expenses", json={
            "project_id": proj_id,
            "category": "Equipment",
            "description": "Water Pipe Procurement",
            "amount": 12000.0
        }, headers=ngo_headers)
        self.assertEqual(exp_res.status_code, 200)
        exp_id = exp_res.json()["id"]

        self.db.commit()
        exp_audit = self.db.query(AuditLog).filter(
            AuditLog.ngo_id == ngo_id,
            AuditLog.action == "CREATE_EXPENSE"
        ).first()
        self.assertIsNotNone(exp_audit, "CREATE_EXPENSE audit log missing")
        self.assertEqual(exp_audit.entity_id, exp_id)

        # 5. NGO Audit Log Endpoint Verification
        ngo_logs_res = self.client.get("/api/ngos/audit-logs", headers=ngo_headers)
        self.assertEqual(ngo_logs_res.status_code, 200)
        ngo_logs = ngo_logs_res.json()
        self.assertGreaterEqual(len(ngo_logs), 4)

    def test_02_admin_audit_logs_access_control(self):
        """
        Tests access control on the Admin Audit Log endpoint.
        - NGO users must be rejected with 403 Forbidden.
        - Admin users must receive full system audit logs.
        """
        ngo_headers = self._get_auth_header("ngo_unauth_audit@example.com", "Password123!", "NGO")
        admin_headers = self._get_auth_header("admin_audit_master@example.com", "AdminPass123!", "ADMIN")

        # NGO attempts to access admin audit logs -> 403
        ngo_req = self.client.get("/api/admin/audit-logs", headers=ngo_headers)
        self.assertEqual(ngo_req.status_code, 403)

        # Admin accesses admin audit logs -> 200 OK
        admin_req = self.client.get("/api/admin/audit-logs", headers=admin_headers)
        self.assertEqual(admin_req.status_code, 200)
        logs = admin_req.json()
        self.assertIsInstance(logs, list)

    def test_03_authoritative_transparency_score_consistency(self):
        """
        Verifies that transparency score is strictly deterministic and identical across:
        - Internal NGODetail DB record
        - NGO Dashboard Profile Endpoint
        - Public NGO Dossier Endpoint (/api/public/ngos/{id})
        """
        ngo_headers = self._get_auth_header("transparency_consistency@example.com", "Password123!", "NGO")
        reg_ngo_res = self.client.post("/api/ngos/register", json={
            "org_name": "Consistency Verification Org",
            "registration_number": "REG-CONSISTENCY-888",
            "tax_id": "TAX-CONSISTENCY-888",
            "category": "Health",
            "mission_statement": "Consistent transparency metrics.",
            "website": "https://consistency.org",
            "address": "456 Consistency Blvd"
        }, headers=ngo_headers)
        self.assertEqual(reg_ngo_res.status_code, 200)
        ngo_id = reg_ngo_res.json()["id"]

        # Fetch score from DB
        ngo_db = self.db.query(NGODetail).filter(NGODetail.id == ngo_id).first()
        ngo_db.status = NGOStatus.APPROVED
        self.db.commit()
        self.db.refresh(ngo_db)
        db_score = ngo_db.transparency_score

        # Fetch score from authenticated profile
        profile_res = self.client.get("/api/ngos/profile", headers=ngo_headers)
        profile_score = profile_res.json()["transparency_score"]

        # Fetch score from public endpoint
        public_res = self.client.get(f"/api/public/ngos/{ngo_id}")
        self.assertEqual(public_res.status_code, 200)
        public_score = public_res.json()["transparency_score"]

        # Verify all three match exactly
        self.assertEqual(db_score, profile_score)
        self.assertEqual(db_score, public_score)

        # Re-trigger Fraud scan and verify consistency holds
        FraudDetectionEngine.scan_ngo(self.db, ngo_id)
        self.db.refresh(ngo_db)

        profile_res_updated = self.client.get("/api/ngos/profile", headers=ngo_headers)
        public_res_updated = self.client.get(f"/api/public/ngos/{ngo_id}")

        self.assertEqual(ngo_db.transparency_score, profile_res_updated.json()["transparency_score"])
        self.assertEqual(ngo_db.transparency_score, public_res_updated.json()["transparency_score"])

    def test_04_ownership_isolation(self):
        """
        Verifies that NGO B cannot create projects or expenses under NGO A.
        """
        ngo_a_headers = self._get_auth_header("ngo_owner_a@example.com", "Password123!", "NGO")
        ngo_b_headers = self._get_auth_header("ngo_owner_b@example.com", "Password123!", "NGO")

        # Create NGO A and Project A
        reg_a = self.client.post("/api/ngos/register", json={
            "org_name": "NGO Alpha",
            "registration_number": "REG-ALPHA-101",
            "tax_id": "TAX-ALPHA-101",
            "category": "Environment",
            "mission_statement": "Alpha mission",
            "website": "https://alpha.org",
            "address": "Alpha Street"
        }, headers=ngo_a_headers)
        self.assertEqual(reg_a.status_code, 200)
        ngo_a_id = reg_a.json()["id"]

        proj_a_res = self.client.post("/api/ngo/projects", json={
            "project_name": "Alpha Forest Planting",
            "description": "Planting trees",
            "category": "Environment",
            "budget": 10000.0,
            "target_beneficiaries": 500
        }, headers=ngo_a_headers)
        self.assertEqual(proj_a_res.status_code, 200)
        proj_a_id = proj_a_res.json()["id"]

        # Register NGO B
        self.client.post("/api/ngos/register", json={
            "org_name": "NGO Beta",
            "registration_number": "REG-BETA-202",
            "tax_id": "TAX-BETA-202",
            "category": "Health",
            "mission_statement": "Beta mission",
            "website": "https://beta.org",
            "address": "Beta Street"
        }, headers=ngo_b_headers)

        # NGO B attempts to add expense to Project A -> Should be rejected with 403
        exp_b_res = self.client.post("/api/ngo/expenses", json={
            "project_id": proj_a_id,
            "category": "Travel",
            "description": "Unauthorized Expense",
            "amount": 500.0
        }, headers=ngo_b_headers)
        self.assertEqual(exp_b_res.status_code, 403)

    def test_05_blockchain_ledger_integrity(self):
        """
        Verifies that all logged events (donations, approvals, document hashes) preserve SHA-256 chain integrity.
        """
        res = LedgerEngine.verify_chain(self.db)
        self.assertTrue(res.get("valid"), f"Ledger verification failed: {res}")


if __name__ == "__main__":
    unittest.main()
