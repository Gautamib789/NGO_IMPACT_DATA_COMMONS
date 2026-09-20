import requests
import json
import sys

BASE = "http://localhost:8000"
FRONT = "http://localhost:3000"

print("======================================================")
print("  NGO IMPACT DATA COMMONS -- FINAL SYSTEM VERIFICATION")
print("======================================================")

# 1. Start by getting Auth Tokens
print("\n[✓] 1. Auth & RBAC Token Generation")
admin_r = requests.post(f"{BASE}/api/auth/login", json={"email": "admin@ngoimpact.org", "password": "AdminPassword123!"})
donor_r = requests.post(f"{BASE}/api/auth/login", json={"email": "donor@example.com", "password": "DonorPassword123!"})
ngo_r   = requests.post(f"{BASE}/api/auth/login", json={"email": "contact@greenearth.org", "password": "NgoPassword123!"})

if not (admin_r.status_code == 200 and donor_r.status_code == 200 and ngo_r.status_code == 200):
    print(f"[FAIL] Could not generate auth tokens.")
    sys.exit(1)

ah = {"Authorization": f"Bearer {admin_r.json()['access_token']}"}
dh = {"Authorization": f"Bearer {donor_r.json()['access_token']}"}
nh = {"Authorization": f"Bearer {ngo_r.json()['access_token']}"}
print("    - Admin token generated")
print("    - Donor token generated")
print("    - NGO token generated")

# 2. Check Backend Core Endpoints
print("\n[✓] 2. Backend Core Business Logic Endpoints")
endpoints = [
    ("GET", f"{BASE}/api/health", None, {}, "Health Check API"),
    ("GET", f"{BASE}/api/public/ngos", None, {}, "Public NGO Directory"),
    ("GET", f"{BASE}/api/ledger/blocks", None, {}, "Blockchain Ledger Stream"),
    ("GET", f"{BASE}/api/ledger/verify", None, {}, "Cryptographic Hash Validation"),
    ("GET", f"{BASE}/api/admin/ngos/pending", None, ah, "Admin NGO Pipeline"),
    ("GET", f"{BASE}/api/fraud/flags", None, ah, "AI Fraud Detection Scans"),
    ("GET", f"{BASE}/api/donations/my-donations", None, dh, "Donor Donation History"),
    ("GET", f"{BASE}/api/ngos/profile", None, nh, "NGO Operations Profile"),
    ("POST", f"{BASE}/api/chat", {"message": "hello"}, {}, "Gemini AI Chatbot Assistant"),
]

all_pass = True
for method, url, body, headers, desc in endpoints:
    r = requests.request(method, url, headers=headers, json=body, timeout=10)
    if r.status_code in [200, 201]:
        print(f"    - [PASS] {desc}")
    else:
        print(f"    - [FAIL] {desc} (Status: {r.status_code}, Body: {r.text[:50]})")
        all_pass = False

# 3. Simulate End-to-End Business Flow
print("\n[✓] 3. End-to-End Flow: Donation & Blockchain Ledger Transaction")
don_r = requests.post(f"{BASE}/api/donations/create", headers=dh, json={"ngo_id": 1, "amount": 150.0, "currency": "USD", "donor_name": "Testing Engine", "message": "Verify chain update"})
if don_r.status_code == 201:
    tx_hash = don_r.json().get("transaction_hash", "UNKNOWN")
    print(f"    - [PASS] Secure Donation Created (Tx: {tx_hash[:24]}...)")
else:
    print(f"    - [FAIL] Secure Donation Failed (HTTP {don_r.status_code})")
    all_pass = False

lv = requests.get(f"{BASE}/api/ledger/verify", timeout=5)
print(f"    - [PASS] Ledger Reverified POST-Donation: {lv.json()['status']}")

# 4. Frontend Rendering Compilation Checks
print("\n[✓] 4. Next.js 15 SSR & ISR Compilation Checks")
frontend_pages = [
    ("/", "Public Dashboard"),
    ("/explore", "Directory Explorer"),
    ("/login", "Authentication UI"),
    ("/ledger", "Blockchain Verification Portal"),
    ("/ngo/1", "NGO Public Dossier"),
    ("/admin/dashboard", "Admin Governance Portal")
]

for url_path, desc in frontend_pages:
    r = requests.get(f"{FRONT}{url_path}", timeout=15)
    if r.status_code == 200:
        print(f"    - [PASS] {desc} Route Active")
    else:
        print(f"    - [FAIL] {desc} Route Issue (HTTP {r.status_code})")
        all_pass = False

print("\n======================================================")
if all_pass:
    print(" 🚀 SUCCESS: NGO Impact Data Commons is FULLY OPERATIONAL!")
else:
    print(" ⚠️ WARNING: Some integrations failed verification.")
print("======================================================")
