import requests, re, pathlib, urllib.request

BASE = "http://localhost:8000"
PASS, FAIL = [], []

def ok(t):  print(f"  PASS  {t}"); PASS.append(t)
def fail(t, r): print(f"  FAIL  {t}: {r}"); FAIL.append(t)
def post(p, **kw): return requests.post(f"{BASE}{p}", timeout=8, **kw)
def get(p, **kw):  return requests.get(f"{BASE}{p}", timeout=8, **kw)
def hdr(t): return {"Authorization": f"Bearer {t}"}

print("\n[1] SERVER")
try:
    r = get("/api/public/stats")
    ok(f"server up, stats={r.json()}")
except Exception as e:
    fail("server", str(e)); exit(1)

print("\n[2] LOGIN")
r = post("/api/auth/login", json={"email":"donor@example.com","password":"DonorPassword123!"})
tok_d = r.json().get("access_token") if r.ok else None
ok(f"donor login otp_required={r.json().get('requires_otp')}") if r.ok else fail("donor login", r.text[:80])

r = post("/api/auth/login", json={"email":"contact@greenearth.org","password":"NgoPassword123!"})
tok_n = r.json().get("access_token") if r.ok else None
ok(f"NGO login otp_required={r.json().get('requires_otp')}") if r.ok else fail("NGO login", r.text[:80])

r = post("/api/auth/login", json={"email":"admin@ngoimpact.org","password":"AdminPassword123!"})
tok_a = r.json().get("access_token") if r.ok else None
ok(f"Admin login otp_required={r.json().get('requires_otp')}") if r.ok else fail("Admin login", r.text[:80])

print("\n[3] PRE-OTP RBAC BLOCK")
if tok_n:
    r = get("/api/ngos/profile", headers=hdr(tok_n))
    ok(f"NGO /profile blocked pre-OTP ({r.status_code})") if r.status_code in (401,403) else fail("NGO pre-OTP", f"got {r.status_code} {r.text[:80]}")
if tok_a:
    r = get("/api/admin/stats", headers=hdr(tok_a))
    ok(f"Admin /stats blocked pre-OTP ({r.status_code})") if r.status_code in (401,403) else fail("Admin pre-OTP", f"got {r.status_code} {r.text[:80]}")

print("\n[4] GENERATE-ROLE-OTP")
if tok_n:
    r = post("/api/auth/generate-role-otp", headers=hdr(tok_n))
    ok(f"generate-role-otp {r.status_code}") if r.ok else fail("generate-role-otp", r.text[:100])

print("\n[5] FORGOT PASSWORD")
r = post("/api/auth/forgot-password", json={"email":"donor@example.com"})
ok(f"forgot-password ok") if r.ok else fail("forgot-password", r.text[:100])

mock = pathlib.Path("mock_email.txt")
if mock.exists():
    c = mock.read_text()
    m = re.search(r"OTP:\s*(\d{6})", c)
    if m: ok(f"OTP {m.group(1)} written to mock_email.txt")
    else: fail("mock_email", "no OTP in file")
else:
    fail("mock_email", "file not created")

print("\n[6] RESET PASSWORD")
if mock.exists():
    c = mock.read_text()
    m = re.search(r"OTP:\s*(\d{6})", c)
    if m:
        r = post("/api/auth/reset-password",
                 json={"email":"donor@example.com","otp":m.group(1),"new_password":"DonorPassword123!"})
        ok(f"reset-password success") if r.ok else fail("reset-password", r.text[:120])

print("\n[7] PUBLIC API")
for p in ["/api/public/ngos", "/api/public/stats"]:
    r = get(p)
    ok(f"GET {p} n={len(r.json()) if isinstance(r.json(),list) else '?'}") if r.ok else fail(p, r.status_code)

print("\n[8] DONATION")
if tok_d:
    ngos = get("/api/public/ngos").json()
    if ngos:
        r = post("/api/donations/create", headers=hdr(tok_d),
                 json={"ngo_id":ngos[0]["id"],"amount":10,"currency":"USD","donor_name":"Test","message":"diag"})
        ok(f"donation to ngo {ngos[0]['id']}") if r.ok else fail("donation", r.text[:120])

print("\n[9] LEDGER")
r = get("/api/ledger/verify")
ok(f"ledger/verify {r.status_code}") if r.ok else fail("ledger/verify", r.text[:80])

print("\n[10] FRONTEND")
try:
    urllib.request.urlopen("http://localhost:3000", timeout=5)
    ok("frontend :3000 reachable")
except Exception as e:
    fail("frontend", str(e))

print(f"\n{'='*50}")
print(f"  TOTAL: {len(PASS)} PASS / {len(FAIL)} FAIL")
if FAIL:
    print("  FAILURES:")
    for f in FAIL: print(f"    - {f}")
print("="*50)
