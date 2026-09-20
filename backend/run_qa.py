import requests
import time
import re
import random
import string

BASE_URL = "http://localhost:8000/api"

print("====================================")
print(" NGO COMMONS - FULL QA SUITE       ")
print("====================================")

def extract_otp(raw_html):
    match = re.search(r">(\d{6})</h1>", raw_html)
    return match.group(1) if match else None

def get_latest_otp(email):
    # Quick utility to grab OTP from the mocked file
    time.sleep(0.5)
    try:
        with open("mock_email.txt", "r") as f:
            html = f.read()
        return extract_otp(html)
    except:
        return None

# ================================
# 1. PUBLIC FLOW
# ================================
print("\n[PHASE] PUBLIC FLOW")
r = requests.get(f"{BASE_URL}/public/ngos")
if r.status_code == 200:
    print("PASS: Public directory access")
else:
    print("FAIL: Public directory access", r.status_code)

r = requests.get(f"{BASE_URL}/public/stats")
if r.status_code == 200:
    print("PASS: Public stats access")
else:
    print("FAIL: Public stats access", r.status_code)

# ================================
# 2. RBAC & SECURITY TESTS
# ================================
print("\n[PHASE] SECURITY & RBAC NEGATIVE TESTS")
r_donor = requests.post(f"{BASE_URL}/auth/login", json={"email": "donor@example.com", "password":"DonorPassword123!"})
donor_token = r_donor.json().get("access_token") if r_donor.status_code == 200 else None

if donor_token:
    headers_donor = {"Authorization": f"Bearer {donor_token}"}
    # Donor trying to access Admin endpoints
    r = requests.post(f"{BASE_URL}/admin/approve-ngo/1", headers=headers_donor)
    if r.status_code in [403, 401]:
        print("PASS: Donor blocked from Admin route")
    else:
        print("FAIL: Donor accessed Admin route!", r.status_code)

    # Donor trying to access NGO endpoints
    r = requests.get(f"{BASE_URL}/ngos/profile", headers=headers_donor)
    if r.status_code in [403, 401]:
        print("PASS: Donor blocked from NGO profile")
    else:
        print("FAIL: Donor accessed NGO profile!", r.status_code)
else:
    print("FAIL: Unable to get donor token to test RBAC.")

# Unauthorized user accessing protected routes
r = requests.get(f"{BASE_URL}/donations/history")
if r.status_code in [401, 403]:
    print("PASS: Unauthenticated blocked")
else:
    print("FAIL: Unauthenticated allowed in protected route!", r.status_code)

# ================================
# 3. NGO WORKFLOW
# ================================
print("\n[PHASE] NGO FULL WORKFLOW")
rand_str = "".join(random.choices(string.ascii_letters, k=5))
ngo_email = f"ngo_{rand_str}@qa.com"
r = requests.post(f"{BASE_URL}/auth/register", json={
    "email": ngo_email,
    "password": "SecurePassword123!",
    "full_name": f"NGO QA {rand_str}",
    "role": "NGO"
})
if r.status_code == 200:
    print("PASS: NGO Registration")
else:
    print("FAIL: NGO Registration", r.status_code)

# Login requires OTP
r = requests.post(f"{BASE_URL}/auth/login", json={"email": ngo_email, "password": "SecurePassword123!"})
if r.json().get("requires_otp") == True:
    print("PASS: NGO Login protected by OTP")
    otp = get_latest_otp(ngo_email)
    r_ver = requests.post(f"{BASE_URL}/auth/verify-login-otp", json={"email": ngo_email, "otp": otp})
    if r_ver.status_code == 200:
        print("PASS: NGO OTP Validation")
        ngo_token = r_ver.json().get("access_token")
    else:
        print("FAIL: NGO OTP Validation", r_ver.status_code, r_ver.text)
        ngo_token = None
else:
    print("FAIL: NGO Login bypassing OTP")
    ngo_token = None

if ngo_token:
    ngo_headers = {"Authorization": f"Bearer {ngo_token}"}
    
    # 3.1 Profile Creation
    r = requests.post(f"{BASE_URL}/ngos/register", json={
        "org_name": f"Org_{rand_str}",
        "registration_number": f"REG_{rand_str}",
        "tax_id": f"TAX_{rand_str}",
        "category": "Education",
        "mission_statement": "Help the world",
        "website": "https://test.com",
        "address": "123 Earth"
    }, headers=ngo_headers)
    
    if r.status_code == 200:
        print("PASS: NGO Profile Creation")
        ngo_profile_id = r.json().get("id")
    else:
        print("FAIL: NGO Profile Creation", r.status_code, r.text)
        
    # Duplicate Registration Test (Same registration number MUST fail)
    r2 = requests.post(f"{BASE_URL}/ngos/register", json={
        "org_name": f"Org_Copy",
        "registration_number": f"REG_{rand_str}",
        "tax_id": f"TAX_COPY",
        "category": "Education",
        "mission_statement": "Copy the world",
        "website": "https://copy.com",
        "address": "456 Earth"
    }, headers=ngo_headers)
    if r2.status_code == 400:
        print("PASS: Duplicate NGO Registration Blocked")
    else:
        print("FAIL: Duplicate NGO Registration ALLOWED!", r2.status_code)

else:
    print("FAIL: Skipping NGO details tests due to missing token")

# ================================
# 4. DONATION NEGATIVE TESTS
# ================================
print("\n[PHASE] DONOR TESTS")
if donor_token:
    # Attempting to donate negative amounts or zero
    r_neg = requests.post(f"{BASE_URL}/donations/create", json={
        "ngo_id": 1,
        "amount": -50.0,
        "message": "Negative value test"
    }, headers=headers_donor)
    if r_neg.status_code >= 400:
        print("PASS: Negative donations properly blocked")
    else:
        print("FAIL: Negative donations succeeded!", r_neg.status_code)
        
    r_zero = requests.post(f"{BASE_URL}/donations/create", json={
        "ngo_id": 1,
        "amount": 0.0,
        "message": "Zero value test"
    }, headers=headers_donor)
    if r_zero.status_code >= 400:
        print("PASS: Zero donations properly blocked")
    else:
        print("FAIL: Zero donations succeeded!", r_zero.status_code)

