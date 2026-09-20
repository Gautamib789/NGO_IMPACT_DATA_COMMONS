import sys
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.otp import OtpCode, OTPPurpose
from app.core.security import get_password_hash
from app.services.ledger_engine import LedgerEngine

client = TestClient(app)

def run_tests():
    print("=== STARTING COMPREHENSIVE 2FA & SECURITY TESTS ===")
    db: Session = SessionLocal()

    try:
        # Seed test users if needed
        admin = db.query(User).filter(User.email == "admin@ngoimpact.org").first()
        donor = db.query(User).filter(User.email == "donor@example.com").first()
        ngo_user = db.query(User).filter(User.email == "contact@ruralhealth.org").first()

        assert admin is not None, "Admin user should exist"
        assert donor is not None, "Donor user should exist"
        assert ngo_user is not None, "NGO user should exist"

        # ----------------------------------------------------
        # Test 1: DONOR successful login (no 2FA required)
        # ----------------------------------------------------
        res1 = client.post("/api/auth/login", json={"email": "donor@example.com", "password": "DonorPassword123!"})
        assert res1.status_code == 200, f"Donor login failed: {res1.text}"
        data1 = res1.json()
        assert data1["requires_otp"] == False, "Donor should not require OTP"
        donor_token = data1["access_token"]
        print("✓ Test 1 Passed: DONOR successful login (direct token, no OTP)")

        # ----------------------------------------------------
        # Test 2: ADMIN correct password -> OTP required
        # ----------------------------------------------------
        res2 = client.post("/api/auth/login", json={"email": "admin@ngoimpact.org", "password": "AdminPassword123!"})
        assert res2.status_code == 200, f"Admin login failed: {res2.text}"
        data2 = res2.json()
        assert data2["requires_otp"] == True, "Admin must require OTP"
        temp_admin_token = data2["access_token"]
        print("✓ Test 2 Passed: ADMIN correct password -> requires_otp=True & temporary JWT issued")

        # ----------------------------------------------------
        # Test 3: NGO correct password -> OTP required
        # ----------------------------------------------------
        res3 = client.post("/api/auth/login", json={"email": "contact@ruralhealth.org", "password": "NgoPassword123!"})
        assert res3.status_code == 200, f"NGO login failed: {res3.text}"
        data3 = res3.json()
        assert data3["requires_otp"] == True, "NGO must require OTP"
        temp_ngo_token = data3["access_token"]
        print("✓ Test 3 Passed: NGO correct password -> requires_otp=True & temporary JWT issued")

        # ----------------------------------------------------
        # Test 4: ADMIN wrong password
        # ----------------------------------------------------
        res4 = client.post("/api/auth/login", json={"email": "admin@ngoimpact.org", "password": "WrongPassword123!"})
        assert res4.status_code == 401, "Admin wrong password should return 401"
        print("✓ Test 4 Passed: ADMIN wrong password returned 401 Unauthorized")

        # ----------------------------------------------------
        # Test 5: NGO wrong password
        # ----------------------------------------------------
        res5 = client.post("/api/auth/login", json={"email": "contact@ruralhealth.org", "password": "WrongPassword123!"})
        assert res5.status_code == 401, "NGO wrong password should return 401"
        print("✓ Test 5 Passed: NGO wrong password returned 401 Unauthorized")

        # ----------------------------------------------------
        # Test 14 & 15: Temporary JWT CANNOT access protected ADMIN or NGO routes
        # ----------------------------------------------------
        res14 = client.get("/api/admin/ngos/all", headers={"Authorization": f"Bearer {temp_admin_token}"})
        assert res14.status_code == 403, f"Temporary admin token should be blocked: {res14.text}"
        assert "2FA OTP Verification is required" in res14.json()["detail"]
        print("✓ Test 14 Passed: Temporary ADMIN JWT denied access to protected admin routes (403)")

        res15 = client.post("/api/ngos/financials", json={"total_expenses": 1000, "total_donations_received": 5000, "beneficiary_count": 50}, headers={"Authorization": f"Bearer {temp_ngo_token}"})
        assert res15.status_code == 403, f"Temporary NGO token should be blocked: {res15.text}"
        assert "2FA OTP Verification is required" in res15.json()["detail"]
        print("✓ Test 15 Passed: Temporary NGO JWT denied access to protected NGO routes (403)")

        # ----------------------------------------------------
        # Test Unauthenticated OTP verification attempt (Token binding verification)
        # ----------------------------------------------------
        res_no_token = client.post("/api/auth/verify-login-otp", json={"email": "admin@ngoimpact.org", "otp": "123456"})
        assert res_no_token.status_code == 401, "Unauthenticated OTP verification without temporary session token must return 401"
        print("✓ Security Test Passed: Unauthenticated OTP verification attempt blocked without temporary JWT (401)")

        # ----------------------------------------------------
        # Test 6: Correct ADMIN OTP verification -> Final JWT
        # ----------------------------------------------------
        admin_otp_entry = db.query(OtpCode).filter(OtpCode.user_id == admin.id, OtpCode.purpose == OTPPurpose.LOGIN, OtpCode.used == False).order_by(OtpCode.created_at.desc()).first()
        assert admin_otp_entry is not None, "Admin OTP should be present in database"
        
        test_admin_otp = "123456"
        admin_otp_entry.hashed_otp = get_password_hash(test_admin_otp)
        db.commit()

        res6 = client.post("/api/auth/verify-login-otp", json={"email": "admin@ngoimpact.org", "otp": test_admin_otp}, headers={"Authorization": f"Bearer {temp_admin_token}"})
        assert res6.status_code == 200, f"Verify Admin OTP failed: {res6.text}"
        final_admin_token = res6.json()["access_token"]
        print("✓ Test 6 Passed: Correct ADMIN OTP verified -> final JWT issued")

        # ----------------------------------------------------
        # Test 7: Correct NGO OTP verification -> Final JWT
        # ----------------------------------------------------
        ngo_otp_entry = db.query(OtpCode).filter(OtpCode.user_id == ngo_user.id, OtpCode.purpose == OTPPurpose.LOGIN, OtpCode.used == False).order_by(OtpCode.created_at.desc()).first()
        assert ngo_otp_entry is not None, "NGO OTP should be present in database"
        
        test_ngo_otp = "654321"
        ngo_otp_entry.hashed_otp = get_password_hash(test_ngo_otp)
        db.commit()

        res7 = client.post("/api/auth/verify-login-otp", json={"email": "contact@ruralhealth.org", "otp": test_ngo_otp}, headers={"Authorization": f"Bearer {temp_ngo_token}"})
        assert res7.status_code == 200, f"Verify NGO OTP failed: {res7.text}"
        final_ngo_token = res7.json()["access_token"]
        print("✓ Test 7 Passed: Correct NGO OTP verified -> final JWT issued")

        # ----------------------------------------------------
        # Test 16: Final JWT accesses correct dashboard / APIs
        # ----------------------------------------------------
        res16_admin = client.get("/api/admin/ngos/all", headers={"Authorization": f"Bearer {final_admin_token}"})
        assert res16_admin.status_code == 200, f"Final Admin token should access admin API: {res16_admin.text}"
        
        res16_ngo = client.post("/api/ngos/financials", json={"total_expenses": 1000, "total_donations_received": 5000, "beneficiary_count": 50}, headers={"Authorization": f"Bearer {final_ngo_token}"})
        assert res16_ngo.status_code == 200, f"Final NGO token should access NGO API: {res16_ngo.text}"
        print("✓ Test 16 Passed: Final JWTs successfully access protected Admin & NGO routes")

        # ----------------------------------------------------
        # Test 17 & 18: Cross-role restriction (ADMIN cannot access NGO-only, NGO cannot access ADMIN-only)
        # ----------------------------------------------------
        res17 = client.get("/api/admin/ngos/all", headers={"Authorization": f"Bearer {final_ngo_token}"})
        assert res17.status_code == 403, "NGO token should not access admin routes"
        print("✓ Test 17 Passed: NGO user forbidden from accessing Admin routes (403)")

        res18 = client.post("/api/ngos/financials", json={"total_expenses": 1000, "total_donations_received": 5000, "beneficiary_count": 50}, headers={"Authorization": f"Bearer {final_admin_token}"})
        assert res18.status_code == 403, "Admin token should not access NGO routes"
        print("✓ Test 18 Passed: ADMIN user forbidden from accessing NGO routes (403)")

        # ----------------------------------------------------
        # Test 8: Wrong OTP
        # ----------------------------------------------------
        login_res_ngo = client.post("/api/auth/login", json={"email": "contact@ruralhealth.org", "password": "NgoPassword123!"})
        temp_ngo_2 = login_res_ngo.json()["access_token"]

        res8 = client.post("/api/auth/verify-login-otp", json={"email": "contact@ruralhealth.org", "otp": "000000"}, headers={"Authorization": f"Bearer {temp_ngo_2}"})
        assert res8.status_code == 401, "Wrong OTP should return 401"
        print("✓ Test 8 Passed: Wrong OTP returned 401 Unauthorized")

        # ----------------------------------------------------
        # Test 9: Expired OTP
        # ----------------------------------------------------
        ngo_otp = db.query(OtpCode).filter(OtpCode.user_id == ngo_user.id, OtpCode.purpose == OTPPurpose.LOGIN, OtpCode.used == False).order_by(OtpCode.created_at.desc()).first()
        if ngo_otp:
            ngo_otp.expires_at = datetime.utcnow() - timedelta(minutes=1)
            db.commit()
        res9 = client.post("/api/auth/verify-login-otp", json={"email": "contact@ruralhealth.org", "otp": "123456"}, headers={"Authorization": f"Bearer {temp_ngo_2}"})
        assert res9.status_code == 400, "Expired OTP should return 400"
        print("✓ Test 9 Passed: Expired OTP returned 400 Bad Request")

        # ----------------------------------------------------
        # Test 10: OTP reuse after successful verification
        # ----------------------------------------------------
        res10 = client.post("/api/auth/verify-login-otp", json={"email": "admin@ngoimpact.org", "otp": test_admin_otp}, headers={"Authorization": f"Bearer {temp_admin_token}"})
        assert res10.status_code == 400, "Reused OTP should be rejected"
        print("✓ Test 10 Passed: Previously used OTP rejected on second attempt")

        # ----------------------------------------------------
        # Test 11 & 12: Resend OTP and Max Resend Limit
        # ----------------------------------------------------
        login_res_resend = client.post("/api/auth/login", json={"email": "contact@ruralhealth.org", "password": "NgoPassword123!"})
        temp_ngo_resend = login_res_resend.json()["access_token"]

        for i in range(3):
            res_resend = client.post("/api/auth/resend-login-otp", json={"email": "contact@ruralhealth.org"}, headers={"Authorization": f"Bearer {temp_ngo_resend}"})
            assert res_resend.status_code == 200, f"Resend {i+1} failed: {res_resend.text}"
        res_resend_exceeded = client.post("/api/auth/resend-login-otp", json={"email": "contact@ruralhealth.org"}, headers={"Authorization": f"Bearer {temp_ngo_resend}"})
        assert res_resend_exceeded.status_code == 429, "Exceeding resend limit should return 429"
        print("✓ Test 11 & 12 Passed: OTP Resend works and enforces max 3 limit (429)")

        # ----------------------------------------------------
        # Test 13: Failed OTP attempt protection (lockout after 5 failures)
        # ----------------------------------------------------
        login_res_lock = client.post("/api/auth/login", json={"email": "admin@ngoimpact.org", "password": "AdminPassword123!"})
        temp_admin_lock = login_res_lock.json()["access_token"]

        for _ in range(5):
            client.post("/api/auth/verify-login-otp", json={"email": "admin@ngoimpact.org", "otp": "999999"}, headers={"Authorization": f"Bearer {temp_admin_lock}"})
        res13 = client.post("/api/auth/verify-login-otp", json={"email": "admin@ngoimpact.org", "otp": "999999"}, headers={"Authorization": f"Bearer {temp_admin_lock}"})
        assert res13.status_code == 429, "Locked account should return 429"
        print("✓ Test 13 Passed: Account locked after 5 failed OTP attempts (429)")

        # Clean up lock for admin for future tests
        db.query(OtpCode).filter(OtpCode.user_id == admin.id, OtpCode.purpose == OTPPurpose.LOGIN).update({"attempt_count": 0})
        db.commit()

        # ----------------------------------------------------
        # Test 19, 20 & 21: Password Reset Isolation & Cross-Purpose Rejection
        # ----------------------------------------------------
        res19 = client.post("/api/auth/forgot-password", json={"email": "donor@example.com"})
        assert res19.status_code == 200, "Forgot password should return 200"
        reset_otp_entry = db.query(OtpCode).filter(OtpCode.user_id == donor.id, OtpCode.purpose == OTPPurpose.RESET_PASSWORD, OtpCode.used == False).order_by(OtpCode.created_at.desc()).first()
        assert reset_otp_entry is not None, "Reset OTP should be created"
        
        test_reset_otp = "777888"
        reset_otp_entry.hashed_otp = get_password_hash(test_reset_otp)
        db.commit()

        res20 = client.post("/api/auth/verify-login-otp", json={"email": "donor@example.com", "otp": test_reset_otp}, headers={"Authorization": f"Bearer {donor_token}"})
        assert res20.status_code == 400, "RESET_PASSWORD OTP must not be accepted for LOGIN"

        client.post("/api/auth/login", json={"email": "admin@ngoimpact.org", "password": "AdminPassword123!"})
        admin_login_otp = db.query(OtpCode).filter(OtpCode.user_id == admin.id, OtpCode.purpose == OTPPurpose.LOGIN, OtpCode.used == False).order_by(OtpCode.created_at.desc()).first()
        test_login_otp = "111222"
        admin_login_otp.hashed_otp = get_password_hash(test_login_otp)
        db.commit()

        res21 = client.post("/api/auth/verify-reset-otp", json={"email": "admin@ngoimpact.org", "otp": test_login_otp})
        assert res21.status_code == 400, "LOGIN OTP must not be accepted for RESET_PASSWORD"
        print("✓ Test 19, 20 & 21 Passed: Password Reset functional & complete cross-purpose OTP isolation verified")

        # ----------------------------------------------------
        # Test 22: Health Check
        # ----------------------------------------------------
        res22 = client.get("/api/health")
        assert res22.status_code == 200, "Health check failed"
        print("✓ Test 22 Passed: API Health Check returns 200 OK")

        # ----------------------------------------------------
        # Test 23: SHA-256 Ledger Integrity
        # ----------------------------------------------------
        res23 = client.get("/api/ledger/verify")
        assert res23.status_code == 200, "Ledger verify failed"
        assert res23.json()["valid"] == True, "Ledger chain must be valid"
        print("✓ Test 23 Passed: SHA-256 Blockchain Ledger verification (valid: true)")

        # ----------------------------------------------------
        # Test 24: Existing Donation Public API
        # ----------------------------------------------------
        res24 = client.get("/api/public/ngos")
        assert res24.status_code == 200, "Public NGOs list failed"
        print("✓ Test 24 Passed: Public NGO & Donation API functional")

        print("\n==================================================")
        print("🎉 ALL 24 TEST SCENARIOS PASSED PERFECTLY!")
        print("==================================================")

    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
