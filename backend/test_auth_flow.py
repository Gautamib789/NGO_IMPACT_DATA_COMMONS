import urllib.request
import json
import time
import re

base_url = 'http://localhost:8000'

def req(url, data=None):
    body = json.dumps(data).encode('utf-8') if data else None
    r = urllib.request.Request(f'{base_url}{url}', data=body, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(r) as res:
            return res.status, json.loads(res.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode('utf-8'))

ts = int(time.time())
email = f'qa_user_{ts}@example.com'
pass1 = 'InitialPassword123!'
pass2 = 'UpdatedPassword123!'

results = []
s1, d1 = req('/api/health')
results.append(f"HEALTH: {s1} - {d1.get('status')}")

s2, d2 = req('/api/auth/register', {'full_name': 'QA User', 'email': email, 'password': pass1, 'role': 'DONOR'})
results.append(f"REGISTER: {s2} - User ID: {d2.get('user_id')}")

s3, d3 = req('/api/auth/login', {'email': email, 'password': pass1})
results.append(f"LOGIN (OLD PWD): {s3} - Token: {bool(d3.get('access_token'))}")

s4, d4 = req('/api/auth/forgot-password', {'email': email})
results.append(f"FORGOT PWD: {s4} - {d4.get('message')}")

time.sleep(1)
with open('mock_email.txt', 'r') as f:
    text = f.read()
    otps = re.findall(r'(\d{6})', text)
    otp = otps[-1] if otps else '000000'
    results.append(f"OTP EXTRACTED: {otp}")

s5, d5 = req('/api/auth/reset-password', {'email': email, 'otp': otp, 'new_password': pass2})
results.append(f"RESET PWD: {s5} - {d5.get('message')}")

s6, d6 = req('/api/auth/login', {'email': email, 'password': pass2})
results.append(f"LOGIN (NEW PWD): {s6} - Token: {bool(d6.get('access_token'))}")

s7, d7 = req('/api/auth/login', {'email': email, 'password': pass1})
results.append(f"LOGIN (OLD PWD FAIL): {s7} - Detail: {d7.get('detail')}")

print("\n".join(results))
