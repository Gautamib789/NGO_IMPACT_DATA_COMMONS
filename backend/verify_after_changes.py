import sqlite3
import json
import urllib.request

DB_PATH = r"E:\NGO\backend\ngo_commons.db"
BASELINE_PATH = r"E:\NGO\backend\baseline_safety_check.json"

with open(BASELINE_PATH, "r", encoding="utf-8") as f:
    baseline = json.load(f)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Record current stats
cursor.execute("SELECT COUNT(*) FROM users;")
current_users = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM ngo_details;")
current_ngos = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM donations;")
current_donations = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM ledger_blocks;")
current_ledger_blocks = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM fraud_flags;")
current_fraud_flags = cursor.fetchone()[0]

# Historical ledger hashes check
cursor.execute("SELECT [index], block_hash, previous_hash, payload_json FROM ledger_blocks ORDER BY [index] ASC;")
blocks = cursor.fetchall()

mismatched_hashes = []
usd_payload_count = 0
inr_payload_count = 0

for index_num, block_hash, prev_hash, payload_json in blocks:
    idx_str = str(index_num)
    if idx_str in baseline["historical_hashes"]:
        expected = baseline["historical_hashes"][idx_str]
        if expected["block_hash"] != block_hash or expected["previous_hash"] != prev_hash:
            mismatched_hashes.append({
                "index": index_num,
                "expected_hash": expected["block_hash"],
                "actual_hash": block_hash,
                "expected_prev": expected["previous_hash"],
                "actual_prev": prev_hash
            })
    
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

comparison = {
    "users_match": baseline["total_users"] == current_users,
    "baseline_users": baseline["total_users"],
    "current_users": current_users,
    "ngos_match": baseline["total_ngos"] == current_ngos,
    "baseline_ngos": baseline["total_ngos"],
    "current_ngos": current_ngos,
    "donations_match": baseline["total_donations"] == current_donations,
    "baseline_donations": baseline["total_donations"],
    "current_donations": current_donations,
    "ledger_blocks_match": baseline["total_ledger_blocks"] == current_ledger_blocks,
    "baseline_ledger_blocks": baseline["total_ledger_blocks"],
    "current_ledger_blocks": current_ledger_blocks,
    "fraud_flags_match": baseline["total_fraud_flags"] == current_fraud_flags,
    "baseline_fraud_flags": baseline["total_fraud_flags"],
    "current_fraud_flags": current_fraud_flags,
    "usd_payload_blocks_count": usd_payload_count,
    "inr_payload_blocks_count": inr_payload_count,
    "mismatched_hashes_count": len(mismatched_hashes),
    "mismatched_hashes": mismatched_hashes,
    "ledger_verify": verify_res
}

print("=== VERIFICATION COMPARISON ===")
print(json.dumps(comparison, indent=2))

if (
    comparison["users_match"] and
    comparison["ngos_match"] and
    comparison["donations_match"] and
    comparison["ledger_blocks_match"] and
    comparison["fraud_flags_match"] and
    comparison["mismatched_hashes_count"] == 0 and
    verify_res.get("valid") is True
):
    print("\n✅ PERFECT MATCH! All database counts preserved, historical hashes 100% byte-identical, chain valid: true.")
else:
    print("\n❌ VERIFICATION FAILED!")
