import sqlite3
import json
import urllib.request
import shutil
from datetime import datetime

DB_PATH = r"E:\NGO\backend\ngo_commons.db"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_PATH = rf"E:\NGO\backend\ngo_commons_backup_safe_usd_ledger_{TIMESTAMP}.db"

# 1. Create fresh database backup
shutil.copyfile(DB_PATH, BACKUP_PATH)
print(f"Created fresh DB backup at: {BACKUP_PATH}")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Record baseline stats
cursor.execute("SELECT COUNT(*) FROM users;")
total_users = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM ngo_details;")
total_ngos = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM donations;")
total_donations = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM ledger_blocks;")
total_ledger_blocks = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM fraud_flags;")
total_fraud_flags = cursor.fetchone()[0]

# Historical ledger hashes
cursor.execute("SELECT [index], block_hash, previous_hash, payload_json FROM ledger_blocks ORDER BY [index] ASC;")
blocks = cursor.fetchall()

historical_hashes = {}
usd_payload_count = 0
inr_payload_count = 0

for index_num, block_hash, prev_hash, payload_json in blocks:
    historical_hashes[str(index_num)] = {
        "block_hash": block_hash,
        "previous_hash": prev_hash
    }
    if payload_json and '"currency": "USD"' in payload_json:
        usd_payload_count += 1
    elif payload_json and '"currency": "INR"' in payload_json:
        inr_payload_count += 1

conn.close()

# Verify live API
try:
    res = urllib.request.urlopen("http://localhost:8000/api/ledger/verify")
    verify_res = json.loads(res.read().decode("utf-8"))
except Exception as e:
    verify_res = {"error": str(e)}

baseline_report = {
    "timestamp": TIMESTAMP,
    "backup_path": BACKUP_PATH,
    "total_users": total_users,
    "total_ngos": total_ngos,
    "total_donations": total_donations,
    "total_ledger_blocks": total_ledger_blocks,
    "total_fraud_flags": total_fraud_flags,
    "usd_payload_blocks_count": usd_payload_count,
    "inr_payload_blocks_count": inr_payload_count,
    "historical_hashes": historical_hashes,
    "ledger_verify": verify_res
}

with open(r"E:\NGO\backend\baseline_safety_check.json", "w", encoding="utf-8") as f:
    json.dump(baseline_report, f, indent=2)

print("Baseline state recorded successfully in E:\\NGO\\backend\\baseline_safety_check.json")
