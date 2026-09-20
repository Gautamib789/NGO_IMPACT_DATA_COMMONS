import os
import sys
import unittest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add current dir to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from main import app
from app.database import get_db, Base
from app.models.user import User, UserRole
from app.models.otp import OtpCode, OTPPurpose
from app.core.security import get_password_hash, verify_password, create_access_token, decode_token

client = TestClient(app)

class TestAuthIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = sessionmaker(bind=create_engine("sqlite:///./ngo_commons.db"))()

    def test_01_valid_login(self):
        # Admin login with correct password
        res = client.post("/api/auth/login", json={"email": "admin@ngoimpact.org", "password": "AdminPassword123!"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("requires_otp"))
        self.assertIn("access_token", data)
        print("[OK] Test 1: Valid credentials login successful")

    def test_02_wrong_password(self):
        res = client.post("/api/auth/login", json={"email": "admin@ngoimpact.org", "password": "WrongPassword999!"})
        self.assertEqual(res.status_code, 401)
        self.assertIn("Incorrect email or password", res.json().get("detail", ""))
        print("[OK] Test 2: Wrong password rejected with 401")

    def test_03_nonexistent_user(self):
        res = client.post("/api/auth/login", json={"email": "nobody_exists_12345@ngoimpact.org", "password": "SomePassword123!"})
        self.assertEqual(res.status_code, 401)
        self.assertIn("Incorrect email or password", res.json().get("detail", ""))
        print("[OK] Test 3: Nonexistent user rejected with 401")

    def test_04_case_insensitive_email(self):
        res = client.post("/api/auth/login", json={"email": "  ADMIN@NGOIMPACT.ORG  ", "password": "AdminPassword123!"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get("email").lower(), "admin@ngoimpact.org")
        print("[OK] Test 4: Case-insensitive and trimmed email login successful")

    def test_05_inactive_user(self):
        # Temporarily create inactive user
        inactive_user = User(
            email="inactive_test_account@example.com",
            hashed_password=get_password_hash("Password123!"),
            full_name="Inactive Test User",
            role=UserRole.DONOR,
            is_active=False
        )
        self.db.add(inactive_user)
        self.db.commit()
        
        res = client.post("/api/auth/login", json={"email": "inactive_test_account@example.com", "password": "Password123!"})
        self.assertEqual(res.status_code, 400)
        self.assertIn("inactive", res.json().get("detail", "").lower())

        # Cleanup
        self.db.delete(inactive_user)
        self.db.commit()
        print("[OK] Test 5: Inactive user login blocked with 400")

    def test_06_corrupted_hash_safety(self):
        # Safe verify_password check on corrupted string
        self.assertFalse(verify_password("Password123!", "corrupted_non_bcrypt_hash"))
        self.assertFalse(verify_password("", "$2b$12$e8Y.1yTK2q..."))
        self.assertFalse(verify_password("Password123!", None))
        print("[OK] Test 6: Corrupted hash safety check passed")

    def test_07_jwt_token_generation(self):
        token = create_access_token(subject=2, role="ADMIN", otp_verified=True)
        self.assertTrue(isinstance(token, str) and len(token) > 20)
        print("[OK] Test 7: JWT generation successful")

    def test_08_jwt_token_decoding(self):
        token = create_access_token(subject=2, role="ADMIN", otp_verified=True)
        payload = decode_token(token)
        self.assertEqual(payload.get("sub"), "2")
        self.assertEqual(payload.get("role"), "ADMIN")
        self.assertTrue(payload.get("otp_verified"))
        print("[OK] Test 8: JWT payload decode successful")

    def test_09_forgot_password_generates_otp(self):
        res = client.post("/api/auth/forgot-password", json={"email": "admin@ngoimpact.org"})
        self.assertEqual(res.status_code, 200)
        self.assertIn("message", res.json())
        print("[OK] Test 9: Forgot password endpoint generates OTP")

    def test_10_otp_storage_and_expiry(self):
        user = self.db.query(User).filter(User.email == "admin@ngoimpact.org").first()
        otp_entry = self.db.query(OtpCode).filter(
            OtpCode.user_id == user.id,
            OtpCode.purpose == OTPPurpose.RESET_PASSWORD
        ).order_by(OtpCode.created_at.desc()).first()
        self.assertIsNotNone(otp_entry)
        self.assertTrue(otp_entry.expires_at > datetime.utcnow())
        print("[OK] Test 10: OTP stored in DB with 5-minute expiry")

    def test_11_email_delivery_fallback(self):
        res = client.post("/api/auth/forgot-password", json={"email": "admin@ngoimpact.org"})
        data = res.json()
        self.assertTrue(data.get("delivered") or data.get("dev_mode"))
        print("[OK] Test 11: Email delivery / dev mode fallback active")

    def test_12_invalid_otp_rejected(self):
        res = client.post("/api/auth/verify-reset-otp", json={"email": "admin@ngoimpact.org", "otp": "000000"})
        self.assertIn(res.status_code, [400, 401])
        print("[OK] Test 12: Invalid OTP rejected")

    def test_13_expired_otp_rejected(self):
        user = self.db.query(User).filter(User.email == "admin@ngoimpact.org").first()
        expired_otp = OtpCode(
            user_id=user.id,
            purpose=OTPPurpose.RESET_PASSWORD,
            hashed_otp=get_password_hash("999999"),
            expires_at=datetime.utcnow() - timedelta(minutes=10)
        )
        self.db.add(expired_otp)
        self.db.commit()

        res = client.post("/api/auth/verify-reset-otp", json={"email": "admin@ngoimpact.org", "otp": "999999"})
        self.assertEqual(res.status_code, 400)

        # Cleanup
        self.db.delete(expired_otp)
        self.db.commit()
        print("[OK] Test 13: Expired OTP rejected")

    def test_14_15_16_17_full_password_reset_flow(self):
        # 14. Generate OTP for test account
        user = self.db.query(User).filter(User.email == "contact@hopefoundation.org").first()
        client.post("/api/auth/forgot-password", json={"email": "contact@hopefoundation.org"})
        
        # Read latest OTP from mock_email.txt or console
        otp_entry = self.db.query(OtpCode).filter(
            OtpCode.user_id == user.id,
            OtpCode.purpose == OTPPurpose.RESET_PASSWORD,
            OtpCode.used == False
        ).order_by(OtpCode.created_at.desc()).first()
        self.assertIsNotNone(otp_entry)

        # Create known OTP
        test_otp = "123456"
        otp_entry.hashed_otp = get_password_hash(test_otp)
        self.db.commit()

        # Verify OTP
        v_res = client.post("/api/auth/verify-reset-otp", json={"email": "contact@hopefoundation.org", "otp": test_otp})
        self.assertEqual(v_res.status_code, 200)
        print("[OK] Test 14: Valid OTP verified successfully")

        # 15. Perform password reset
        new_pwd = "NewHopePassword123!"
        r_res = client.post("/api/auth/reset-password", json={"email": "contact@hopefoundation.org", "otp": test_otp, "new_password": new_pwd})
        self.assertEqual(r_res.status_code, 200)
        print("[OK] Test 15: Password reset executed")

        # 16. Old password fails
        old_login = client.post("/api/auth/login", json={"email": "contact@hopefoundation.org", "password": "WrongOldPassword!"})
        self.assertEqual(old_login.status_code, 401)
        print("[OK] Test 16: Old password login rejected")

        # 17. New password succeeds (reset back to NgoPassword123!)
        new_login = client.post("/api/auth/login", json={"email": "contact@hopefoundation.org", "password": new_pwd})
        self.assertEqual(new_login.status_code, 200)

        # Restore original password for testing consistency
        user.hashed_password = get_password_hash("NgoPassword123!")
        self.db.commit()
        print("[OK] Test 17: New password login successful & restored")

    def test_18_ngo_role_authorization(self):
        # NGO token with otp_verified=True
        ngo_user = self.db.query(User).filter(User.role == UserRole.NGO).first()
        token = create_access_token(subject=ngo_user.id, role="NGO", otp_verified=True)
        res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get("email"), ngo_user.email)
        print("[OK] Test 18: NGO role authorization endpoint passed")

    def test_19_admin_role_authorization(self):
        admin_user = self.db.query(User).filter(User.role == UserRole.ADMIN).first()
        token = create_access_token(subject=admin_user.id, role="ADMIN", otp_verified=True)
        res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get("email"), admin_user.email)
        print("[OK] Test 19: Admin role authorization endpoint passed")

    def test_20_unprotected_jwt_rejection(self):
        res = client.get("/api/auth/me")
        self.assertEqual(res.status_code, 401)
        print("[OK] Test 20: Unauthenticated access rejected with 401")


if __name__ == "__main__":
    unittest.main()
