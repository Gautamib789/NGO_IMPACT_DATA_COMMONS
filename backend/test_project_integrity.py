import sys
import os
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from app.database import SessionLocal, engine
from app.models.user import User
from app.models.ngo import NGODetail
from app.models.project import Project
from app.core.security import get_password_hash, create_access_token

client = TestClient(app)

class TestNGOProjectIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()

        # Clean up existing test users if present
        cls.db.query(Project).filter(Project.project_name.like("Test Proj%")).delete(synchronize_session=False)
        cls.db.query(NGODetail).filter(NGODetail.org_name.in_(["Test Project NGO 1", "Test Project NGO 2"])).delete(synchronize_session=False)
        cls.db.query(User).filter(User.email.in_(["project_user1@ngo.org", "project_user2@ngo.org"])).delete(synchronize_session=False)
        cls.db.commit()

        # 1. Create NGO User 1
        user1 = User(
            email="project_user1@ngo.org",
            hashed_password=get_password_hash("Secret123!"),
            role="NGO",
            full_name="User One",
            is_active=True
        )
        cls.db.add(user1)
        cls.db.commit()
        cls.db.refresh(user1)

        ngo1 = NGODetail(
            user_id=user1.id,
            org_name="Test Project NGO 1",
            registration_number="REG-PROJ-001",
            tax_id="PANPROJ001",
            status="APPROVED",
            doc_completeness_score=100.0,
            transparency_score=100.0
        )
        cls.db.add(ngo1)
        cls.db.commit()
        cls.db.refresh(ngo1)

        # 2. Create NGO User 2 (Different NGO)
        user2 = User(
            email="project_user2@ngo.org",
            hashed_password=get_password_hash("Secret123!"),
            role="NGO",
            full_name="User Two",
            is_active=True
        )
        cls.db.add(user2)
        cls.db.commit()
        cls.db.refresh(user2)

        ngo2 = NGODetail(
            user_id=user2.id,
            org_name="Test Project NGO 2",
            registration_number="REG-PROJ-002",
            tax_id="PANPROJ002",
            status="APPROVED",
            doc_completeness_score=100.0,
            transparency_score=100.0
        )
        cls.db.add(ngo2)
        cls.db.commit()
        cls.db.refresh(ngo2)

        # Tokens
        cls.token1 = create_access_token(subject=str(user1.id), role=user1.role, otp_verified=True)
        cls.headers1 = {"Authorization": f"Bearer {cls.token1}"}

        cls.token2 = create_access_token(subject=str(user2.id), role=user2.role, otp_verified=True)
        cls.headers2 = {"Authorization": f"Bearer {cls.token2}"}

    @classmethod
    def tearDownClass(cls):
        cls.db.query(Project).filter(Project.project_name.like("Test Proj%")).delete(synchronize_session=False)
        cls.db.query(NGODetail).filter(NGODetail.org_name.in_(["Test Project NGO 1", "Test Project NGO 2"])).delete(synchronize_session=False)
        cls.db.query(User).filter(User.email.in_(["project_user1@ngo.org", "project_user2@ngo.org"])).delete(synchronize_session=False)
        cls.db.commit()
        cls.db.close()

    def test_01_valid_project_creation(self):
        """Test valid project creation succeeds with HTTP 201 and low risk status."""
        payload = {
            "project_name": "Test Proj Health Clinic",
            "category": "Healthcare",
            "description": "Providing basic health checkups to rural families",
            "budget": 75000,
            "location": "Mysuru, Karnataka",
            "latitude": 12.2958,
            "longitude": 76.6394,
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "target_beneficiaries": 1000,
            "outcomes": "Improve community health scores",
            "status": "ACTIVE"
        }
        res = client.post("/api/ngo/projects", json=payload, headers=self.headers1)
        self.assertEqual(res.status_code, 201, f"Expected 201, got {res.status_code}: {res.text}")
        data = res.json()
        self.assertEqual(data["project_name"], "Test Proj Health Clinic")
        self.assertEqual(data["budget"], 75000.0)
        self.assertEqual(data["beneficiary_count"], 1000)
        self.assertEqual(data["integrity_status"], "VERIFIED")
        self.assertEqual(data["risk_level"], "LOW")
        self.assertEqual(data["risk_score"], 0.0)
        self.assertIn("id", data)

    def test_02_missing_required_fields(self):
        """Test missing required project_name returns HTTP 422 with clear error."""
        payload = {
            "category": "Healthcare",
            "budget": 50000
        }
        res = client.post("/api/ngo/projects", json=payload, headers=self.headers1)
        self.assertEqual(res.status_code, 422, f"Expected 422, got {res.status_code}: {res.text}")
        data = res.json()
        self.assertIn("detail", data)

    def test_03_invalid_budget(self):
        """Test budget <= 0 returns HTTP 422 validation error."""
        payload = {
            "project_name": "Test Proj Zero Budget",
            "category": "Education",
            "budget": 0
        }
        res = client.post("/api/ngo/projects", json=payload, headers=self.headers1)
        self.assertEqual(res.status_code, 422, f"Expected 422, got {res.status_code}: {res.text}")
        data = res.json()
        self.assertTrue("detail" in data)

    def test_04_invalid_date_range(self):
        """Test end_date before start_date returns HTTP 422 validation error."""
        payload = {
            "project_name": "Test Proj Invalid Dates",
            "category": "Environment",
            "budget": 10000,
            "start_date": "2026-12-31",
            "end_date": "2026-01-01"
        }
        res = client.post("/api/ngo/projects", json=payload, headers=self.headers1)
        self.assertEqual(res.status_code, 422, f"Expected 422, got {res.status_code}: {res.text}")

    def test_05_unauthenticated_request(self):
        """Test unauthenticated project creation returns HTTP 401."""
        payload = {
            "project_name": "Test Proj Unauth",
            "budget": 50000
        }
        res = client.post("/api/ngo/projects", json=payload)
        self.assertEqual(res.status_code, 401)

    def test_06_cross_ngo_project_access_denied(self):
        """Test NGO 2 cannot view, edit, or delete NGO 1's project (HTTP 403)."""
        # Create project under NGO 1
        payload = {
            "project_name": "Test Proj NGO1 Private",
            "budget": 50000,
            "category": "Education"
        }
        res = client.post("/api/ngo/projects", json=payload, headers=self.headers1)
        self.assertEqual(res.status_code, 201)
        proj_id = res.json()["id"]

        # NGO 2 tries to GET NGO 1's project detail
        res_get = client.get(f"/api/ngo/projects/{proj_id}", headers=self.headers2)
        self.assertEqual(res_get.status_code, 403, f"Expected 403 Access Denied, got {res_get.status_code}")

        # NGO 2 tries to PUT (edit) NGO 1's project
        res_put = client.put(f"/api/ngo/projects/{proj_id}", json={"project_name": "Hacked", "budget": 100}, headers=self.headers2)
        self.assertEqual(res_put.status_code, 403, f"Expected 403 Access Denied, got {res_put.status_code}")

        # NGO 2 tries to DELETE NGO 1's project
        res_del = client.delete(f"/api/ngo/projects/{proj_id}", headers=self.headers2)
        self.assertEqual(res_del.status_code, 403, f"Expected 403 Access Denied, got {res_del.status_code}")

    def test_07_update_and_delete_own_project(self):
        """Test NGO 1 can update and delete its own project successfully."""
        # Create
        payload = {
            "project_name": "Test Proj Editable",
            "budget": 25000,
            "category": "Water"
        }
        res = client.post("/api/ngo/projects", json=payload, headers=self.headers1)
        self.assertEqual(res.status_code, 201)
        proj_id = res.json()["id"]

        # Update
        update_payload = {
            "project_name": "Test Proj Editable Updated",
            "budget": 30000,
            "category": "Water & Sanitation"
        }
        res_upd = client.put(f"/api/ngo/projects/{proj_id}", json=update_payload, headers=self.headers1)
        self.assertEqual(res_upd.status_code, 200)
        self.assertEqual(res_upd.json()["project_name"], "Test Proj Editable Updated")

        # Delete
        res_del = client.delete(f"/api/ngo/projects/{proj_id}", headers=self.headers1)
        self.assertEqual(res_del.status_code, 200)

        # Verify deleted
        res_get = client.get(f"/api/ngo/projects/{proj_id}", headers=self.headers1)
        self.assertEqual(res_get.status_code, 404)

if __name__ == "__main__":
    unittest.main()
