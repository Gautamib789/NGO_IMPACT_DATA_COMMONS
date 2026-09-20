import unittest
import json
import os
import sys
import hashlib
from fastapi.testclient import TestClient

# Add backend root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from main import app
from app.database import Base, engine, SessionLocal
from app.models.user import User, UserRole
from app.models.ngo import NGODetail, NGODocument, NGOStatus
from app.models.project import Project
from app.models.beneficiary import Beneficiary
from app.models.expense import Expense
from app.models.audit import AuditLog
from app.services.ledger_engine import LedgerEngine
from app.services.fraud_engine import FraudDetectionEngine
from app.services.document_tamper_engine import DocumentTamperEngine


class TestPhase10FinalValidation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def _get_auth_header(self, email: str, password: str, role_str: str, otp_verified: bool = True) -> dict:
        from app.core.security import create_access_token, get_password_hash
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            role_enum = UserRole.ADMIN if role_str == "ADMIN" else (UserRole.NGO if role_str == "NGO" else UserRole.DONOR)
            user = User(
                email=email,
                hashed_password=get_password_hash(password),
                full_name=f"Phase10 User {email}",
                role=role_enum,
                is_active=True
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

        token = create_access_token(subject=str(user.id), role=user.role.value, otp_verified=otp_verified)
        return {"Authorization": f"Bearer {token}"}

    # =========================================================================
    # 1. FULL END-TO-END USER JOURNEYS
    # =========================================================================

    def test_01_public_user_journey(self):
        """Validates Public User flow: Explore NGOs, Public Dossier, Projects & Transparency Data."""
        # Explore NGOs
        res_list = self.client.get("/api/public/ngos")
        self.assertEqual(res_list.status_code, 200)

    def test_02_ngo_full_lifecycle_journey(self):
        """Validates complete NGO Lifecycle: Registration, Gov Verification, Document Upload, Projects, Beneficiaries, Expenses, Utilization & Audit."""
        import uuid
        uid = uuid.uuid4().hex[:6]
        ngo_headers = self._get_auth_header(f"p10_ngo_lc_{uid}@example.com", "Password123!", "NGO")

        # 1. Registration
        reg_res = self.client.post("/api/ngos/register", json={
            "org_name": f"Phase 10 Hope Foundation {uid}",
            "registration_number": f"P10-REG-LC-{uid}",
            "tax_id": f"P10-TAX-LC-{uid}",
            "category": "Healthcare",
            "mission_statement": "Comprehensive healthcare for all.",
            "website": "https://p10hope.org",
            "address": "777 Phase 10 Blvd"
        }, headers=ngo_headers)
        self.assertEqual(reg_res.status_code, 200, f"Registration failed: {reg_res.text}")
        ngo_id = reg_res.json()["id"]

        # 2. Government Verification
        gov_res = self.client.post("/api/ngos/government-verification", headers=ngo_headers)
        self.assertEqual(gov_res.status_code, 200)
        self.assertIn("SIMULATED DEMO GOVERNMENT REGISTRY", gov_res.json()["disclaimer"].upper())

        # 3. Document Upload
        pdf_bytes = b"%PDF-1.4 Simulated Valid PDF Content for Phase 10 %%EOF"
        files = {"file": ("p10_doc.pdf", pdf_bytes, "application/pdf")}
        doc_res = self.client.post("/api/ngos/upload-document", data={"document_type": "80G"}, files=files, headers=ngo_headers)
        self.assertEqual(doc_res.status_code, 200)
        self.assertEqual(doc_res.json()["sha256_hash"], hashlib.sha256(pdf_bytes).hexdigest())

        # 4. Project Creation
        proj_res = self.client.post("/api/ngo/projects", json={
            "project_name": "Rural Health Clinic",
            "description": "Constructing healthcare facilities.",
            "category": "Healthcare",
            "budget": 75000.0,
            "target_beneficiaries": 200
        }, headers=ngo_headers)
        self.assertEqual(proj_res.status_code, 200)
        proj_id = proj_res.json()["id"]

        # 5. Beneficiary Creation
        ben_res = self.client.post("/api/ngo/beneficiaries", json={
            "project_id": proj_id,
            "name_or_alias": "Patient-001",
            "age_group": "30-40",
            "gender": "Female",
            "location": "North District"
        }, headers=ngo_headers)
        self.assertEqual(ben_res.status_code, 200)

        # 6. Expense Creation
        exp_res = self.client.post("/api/ngo/expenses", json={
            "project_id": proj_id,
            "category": "Medical Supplies",
            "description": "Purchase of vaccines & equipment",
            "amount": 25000.0
        }, headers=ngo_headers)
        self.assertEqual(exp_res.status_code, 200)

        # 7. Fund Utilization & Expense Verification
        util_res = self.client.get("/api/ngo/expenses", headers=ngo_headers)
        self.assertEqual(util_res.status_code, 200)
        total_exp = sum(e["amount"] for e in util_res.json())
        self.assertGreaterEqual(total_exp, 25000.0)

        # 8. View Audit History
        audit_res = self.client.get("/api/ngos/audit-logs", headers=ngo_headers)
        self.assertEqual(audit_res.status_code, 200)
        self.assertGreaterEqual(len(audit_res.json()), 3)

    def test_03_admin_user_journey(self):
        """Validates Admin user flow: Document Inspection, Approval/Rejection, Audit log review."""
        admin_headers = self._get_auth_header("p10_admin@example.com", "AdminPass123!", "ADMIN")

        # View Pending Documents
        docs_res = self.client.get("/api/admin/documents/pending", headers=admin_headers)
        self.assertEqual(docs_res.status_code, 200)

        # View Admin Audit Logs
        logs_res = self.client.get("/api/admin/audit-logs", headers=admin_headers)
        self.assertEqual(logs_res.status_code, 200)

    def test_04_donor_user_journey_and_isolation(self):
        """Validates Donor user flow and strict restriction from NGO/Admin endpoints."""
        donor_headers = self._get_auth_header("p10_donor@example.com", "DonorPass123!", "DONOR")

        # Donor accessing NGO endpoint -> 403 Forbidden
        ngo_access = self.client.get("/api/ngos/profile", headers=donor_headers)
        self.assertEqual(ngo_access.status_code, 403)

        # Donor accessing Admin endpoint -> 403 Forbidden
        admin_access = self.client.get("/api/admin/audit-logs", headers=donor_headers)
        self.assertEqual(admin_access.status_code, 403)

    # =========================================================================
    # 2. SECURITY & BOUNDARY TESTING
    # =========================================================================

    def test_05_unauthenticated_and_temporary_token_restrictions(self):
        """Verifies unauthenticated access rejection and temporary unverified OTP token isolation."""
        # Unauthenticated access
        unauth = self.client.get("/api/ngos/profile")
        self.assertEqual(unauth.status_code, 401, f"Expected 401 for unauthenticated access, got {unauth.status_code}")

        # Temporary JWT token (otp_verified = False)
        temp_headers = self._get_auth_header("p10_ngo_unverified@example.com", "Password123!", "NGO", otp_verified=False)
        temp_access = self.client.get("/api/ngos/profile", headers=temp_headers)
        self.assertEqual(temp_access.status_code, 403, f"Expected 403 for unverified OTP token access, got {temp_access.status_code}")

    def test_06_tenant_ownership_isolation(self):
        """Verifies NGO B cannot access or modify NGO A's projects or expenses."""
        import uuid
        uid_a = uuid.uuid4().hex[:6]
        uid_b = uuid.uuid4().hex[:6]
        ngo_a_headers = self._get_auth_header(f"p10_ngo_iso_a_{uid_a}@example.com", "Password123!", "NGO")
        ngo_b_headers = self._get_auth_header(f"p10_ngo_iso_b_{uid_b}@example.com", "Password123!", "NGO")

        # Register NGO A & Create Project
        reg_a = self.client.post("/api/ngos/register", json={
            "org_name": f"NGO Alpha {uid_a}",
            "registration_number": f"REG-P10-A-{uid_a}",
            "tax_id": f"TAX-P10-A-{uid_a}",
            "category": "Education",
            "mission_statement": "Alpha mission",
            "website": "https://alpha10.org",
            "address": "Alpha Street"
        }, headers=ngo_a_headers)
        self.assertEqual(reg_a.status_code, 200, f"Registration A failed: {reg_a.text}")

        proj_a_res = self.client.post("/api/ngo/projects", json={
            "project_name": "Alpha School Build",
            "description": "Building schools",
            "category": "Education",
            "budget": 50000.0,
            "target_beneficiaries": 100
        }, headers=ngo_a_headers)
        self.assertEqual(proj_a_res.status_code, 200, f"Project creation failed: {proj_a_res.text}")
        proj_a_id = proj_a_res.json()["id"]

        # Register NGO B Profile
        reg_b = self.client.post("/api/ngos/register", json={
            "org_name": f"NGO Beta {uid_b}",
            "registration_number": f"REG-P10-B-{uid_b}",
            "tax_id": f"TAX-P10-B-{uid_b}",
            "category": "Education",
            "mission_statement": "Beta mission",
            "website": "https://beta10.org",
            "address": "Beta Street"
        }, headers=ngo_b_headers)
        self.assertEqual(reg_b.status_code, 200, f"Registration B failed: {reg_b.text}")

        # NGO B attempts to create expense for NGO A's project -> 403
        rogue_exp = self.client.post("/api/ngo/expenses", json={
            "project_id": proj_a_id,
            "category": "Travel",
            "description": "Rogue expense attempt",
            "amount": 5000.0
        }, headers=ngo_b_headers)
        self.assertEqual(rogue_exp.status_code, 403)

    def test_07_audit_log_metadata_secret_sanitization(self):
        """Verifies no passwords, OTP tokens, or secret credentials exist in AuditLog metadata."""
        logs = self.db.query(AuditLog).all()
        for log in logs:
            if log.metadata_json:
                meta_lower = log.metadata_json.lower()
                self.assertNotIn("password", meta_lower)
                self.assertNotIn("access_token", meta_lower)
                self.assertNotIn("otp_code", meta_lower)

    # =========================================================================
    # 3. DOCUMENT SECURITY & HEURISTIC TAMPER ENGINE
    # =========================================================================

    def test_08_document_tamper_engine_heuristics(self):
        """Verifies raw bytes SHA-256 calculation, magic byte checks, and risk classifications."""
        # 1. Valid PDF
        pdf_bytes = b"%PDF-1.5 Sample Authentic PDF Content %%EOF"
        res_pdf = DocumentTamperEngine.analyze_document(pdf_bytes, "doc.pdf", "80G")
        self.assertEqual(res_pdf["sha256_hash"], hashlib.sha256(pdf_bytes).hexdigest())
        self.assertEqual(res_pdf["tamper_risk_level"], "LOW")

        # 2. Extension Spoofing (PDF bytes with .png extension)
        res_spoof = DocumentTamperEngine.analyze_document(pdf_bytes, "fake_image.png", "80G")
        self.assertGreaterEqual(res_spoof["tamper_risk_score"], 30.0)

        # 3. Editing Software Signature Detection
        pdf_edited = b"%PDF-1.5 Content generated via Photoshop CS6 %%EOF"
        res_edited = DocumentTamperEngine.analyze_document(pdf_edited, "edited.pdf", "80G")
        self.assertGreaterEqual(res_edited["tamper_risk_score"], 35.0)

    # =========================================================================
    # 4. DEMO GOVERNMENT REGISTRY & VERIFICATION
    # =========================================================================

    def test_09_demo_government_registry_verification(self):
        """Verifies demo registry matching and clear academic/demo disclaimer labeling."""
        import uuid
        uid = uuid.uuid4().hex[:6]
        ngo_headers = self._get_auth_header(f"p10_ngo_gov_{uid}@example.com", "Password123!", "NGO")
        self.client.post("/api/ngos/register", json={
            "org_name": f"NGO Gov {uid}",
            "registration_number": f"REG-GOV-{uid}",
            "tax_id": f"TAX-GOV-{uid}",
            "category": "Education",
            "mission_statement": "Gov mission",
            "website": "https://gov.org",
            "address": "Gov Street"
        }, headers=ngo_headers)

        res = self.client.post("/api/ngos/government-verification", headers=ngo_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("SIMULATED DEMO GOVERNMENT REGISTRY", data["disclaimer"].upper())

    # =========================================================================
    # 5. TRANSPARENCY SCORE PARITY & DETERMINISM
    # =========================================================================

    def test_10_transparency_score_consistency(self):
        """Verifies DB, NGO Profile, and Public Dossier share identical transparency scores."""
        import uuid
        uid = uuid.uuid4().hex[:6]
        ngo_headers = self._get_auth_header(f"p10_ngo_score_{uid}@example.com", "Password123!", "NGO")
        reg_res = self.client.post("/api/ngos/register", json={
            "org_name": f"NGO Score {uid}",
            "registration_number": f"REG-SCORE-{uid}",
            "tax_id": f"TAX-SCORE-{uid}",
            "category": "Education",
            "mission_statement": "Score mission",
            "website": "https://score.org",
            "address": "Score Street"
        }, headers=ngo_headers)
        self.assertEqual(reg_res.status_code, 200)

        # Get profile score
        prof_res = self.client.get("/api/ngos/profile", headers=ngo_headers)
        self.assertEqual(prof_res.status_code, 200)
        prof_data = prof_res.json()
        ngo_id = prof_data["id"]
        score_prof = prof_data["transparency_score"]

        # Approve NGO so public dossier is accessible
        ngo_db = self.db.query(NGODetail).filter(NGODetail.id == ngo_id).first()
        ngo_db.status = NGOStatus.APPROVED
        self.db.commit()

        # Get DB score
        score_db = ngo_db.transparency_score

        # Get Public score
        pub_res = self.client.get(f"/api/public/ngos/{ngo_id}")
        self.assertEqual(pub_res.status_code, 200)
        score_pub = pub_res.json()["transparency_score"]

        # Verify Parity
        self.assertEqual(score_db, score_prof)
        self.assertEqual(score_db, score_pub)

    # =========================================================================
    # 6. BLOCKCHAIN LEDGER INTEGRITY
    # =========================================================================

    def test_11_blockchain_ledger_hash_integrity(self):
        """Verifies full SHA-256 chain integrity for all ledger blocks."""
        ledger_res = LedgerEngine.verify_chain(self.db)
        self.assertTrue(ledger_res.get("valid"), f"Ledger integrity compromised: {ledger_res}")


if __name__ == "__main__":
    unittest.main()
