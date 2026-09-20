import requests

BASE_URL = "http://127.0.0.1:8000"

def run_diagnostic():
    print("==================================================")
    print("AUTHENTICATION & ENDPOINT DIAGNOSTIC")
    print("==================================================")

    # 1. Test Login to get fresh token
    login_payload = {
        "email": "contact@greenearth.org",
        "password": "NgoPassword123!"
    }
    print(f"\n1. Attempting Login at {BASE_URL}/api/auth/login with {login_payload['email']}...")
    try:
        resp = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload)
        print(f"   Response Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"   Login failed! Body: {resp.text}")
            return
        
        data = resp.json()
        token = data.get("access_token")
        user = data.get("user")
        print(f"   Login Response: {data}")
        print(f"   Requires 2FA: {data.get('requires_2fa')}")

        if data.get('requires_2fa'):
            print("\n   2FA OTP is required. Sending verify-otp request with code 123456...")
            otp_resp = requests.post(f"{BASE_URL}/api/auth/verify-otp", json={
                "email": "contact@greenearth.org",
                "otp_code": "123456",
                "purpose": "LOGIN"
            })
            print(f"   OTP Verify Status: {otp_resp.status_code}")
            print(f"   OTP Response Body: {otp_resp.text}")
            if otp_resp.status_code == 200:
                token = otp_resp.json().get("access_token")

        headers = {"Authorization": f"Bearer {token}"}

        # 2. Test GET /api/ngos/profile
        print("\n2. Testing GET /api/ngos/profile...")
        r_prof = requests.get(f"{BASE_URL}/api/ngos/profile", headers=headers)
        print(f"   Status: {r_prof.status_code}")
        print(f"   Body: {r_prof.text[:200]}")

        # 3. Test GET /api/ngos/government-verification
        print("\n3. Testing GET /api/ngos/government-verification...")
        r_gov = requests.get(f"{BASE_URL}/api/ngos/government-verification", headers=headers)
        print(f"   Status: {r_gov.status_code}")
        print(f"   Body: {r_gov.text[:200]}")

        # 4. Test POST /api/ngos/government-verification
        print("\n4. Testing POST /api/ngos/government-verification...")
        r_gov_post = requests.post(f"{BASE_URL}/api/ngos/government-verification", headers=headers)
        print(f"   Status: {r_gov_post.status_code}")
        print(f"   Body: {r_gov_post.text[:200]}")

        # 5. Test Invalid/Stale Token
        print("\n5. Testing invalid/stale token behavior...")
        invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
        r_inv = requests.get(f"{BASE_URL}/api/ngos/profile", headers=invalid_headers)
        print(f"   Status with invalid token: {r_inv.status_code}")
        print(f"   Body: {r_inv.json()}")

    except Exception as e:
        print(f"   Error: {e}")

if __name__ == '__main__':
    run_diagnostic()
