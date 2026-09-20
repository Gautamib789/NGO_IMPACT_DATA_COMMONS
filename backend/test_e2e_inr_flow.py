import urllib.request
import json

BASE_URL = "http://localhost:8000"

# 1. Register a new test donor
reg_url = f"{BASE_URL}/api/auth/register"
reg_payload = json.dumps({
    "email": "inr_donor_verify@example.com",
    "password": "Password123!",
    "full_name": "Verified INR Donor",
    "role": "DONOR"
}).encode("utf-8")

token = None
try:
    req = urllib.request.Request(reg_url, data=reg_payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        token = data.get("access_token")
        print("1. Registered test donor successfully. Access Token received.")
except Exception as e:
    # If already registered, login
    login_url = f"{BASE_URL}/api/auth/login"
    login_payload = json.dumps({
        "email": "inr_donor_verify@example.com",
        "password": "Password123!"
    }).encode("utf-8")
    req = urllib.request.Request(login_url, data=login_payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        token = data.get("access_token")
        print("1. Logged in existing test donor successfully.")

# 2. Create new donation of ₹2,500 INR
create_don_url = f"{BASE_URL}/api/donations/create"
don_payload = json.dumps({
    "ngo_id": 1,
    "amount": 2500.0,
    "currency": "INR",
    "donor_name": "Verified INR Donor",
    "message": "Supporting transparent community development in INR"
}).encode("utf-8")

req_don = urllib.request.Request(create_don_url, data=don_payload, headers={
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
})

with urllib.request.urlopen(req_don) as resp:
    don_data = json.loads(resp.read().decode("utf-8"))
    print("\n2. New Donation Created Successfully:")
    print("   - Donation ID:", don_data.get("id"))
    print("   - Amount:", don_data.get("amount"))
    print("   - Currency:", don_data.get("currency"))
    print("   - Tx Hash:", don_data.get("transaction_hash"))

# 3. Call Ledger Verify Endpoint
verify_url = f"{BASE_URL}/api/ledger/verify"
with urllib.request.urlopen(verify_url) as resp:
    ver_data = json.loads(resp.read().decode("utf-8"))
    print("\n3. Post-Donation Blockchain Ledger Integrity Check:")
    print("   - Valid:", ver_data.get("valid"))
    print("   - Total Blocks:", ver_data.get("total_blocks"))
    print("   - Latest Hash:", ver_data.get("latest_hash"))
    print("   - Status:", ver_data.get("status"))
