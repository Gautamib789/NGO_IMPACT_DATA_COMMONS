import sqlite3
import json
import urllib.request

DB_PATH = r"E:\NGO\backend\ngo_commons.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 1. Total donation count
cursor.execute("SELECT COUNT(*) FROM donations;")
total_donations = cursor.fetchone()[0]

# 2. Donation currency distribution in `donations` table
cursor.execute("SELECT currency, COUNT(*), SUM(amount) FROM donations GROUP BY currency;")
donations_dist = cursor.fetchall()

# 3. Ledger block count
cursor.execute("SELECT COUNT(*) FROM ledger_blocks;")
total_ledger_blocks = cursor.fetchone()[0]

# 4. Ledger currency distribution by examining `payload_json`
cursor.execute("SELECT [index], event_type, payload_json, timestamp FROM ledger_blocks ORDER BY [index] ASC;")
all_blocks = cursor.fetchall()

ledger_dist = {}
usd_blocks_detail = []
all_blocks_detail = []

for index_num, event_type, payload_json, timestamp in all_blocks:
    p_currency = "GENESIS / SYSTEM"
    data = {}
    try:
        if payload_json:
            data = json.loads(payload_json)
            if isinstance(data, dict):
                p_currency = data.get("currency", "NO_CURRENCY_FIELD_IN_PAYLOAD")
    except Exception as e:
        p_currency = "INVALID_JSON"

    ledger_dist[p_currency] = ledger_dist.get(p_currency, 0) + 1

    block_info = {
        "block_index": index_num,
        "event_type": event_type,
        "timestamp": timestamp,
        "payload_currency": p_currency,
        "donation_id": data.get("donation_id") if isinstance(data, dict) else None,
        "ngo_id": data.get("ngo_id") if isinstance(data, dict) else None,
        "ngo_name": data.get("ngo_name") if isinstance(data, dict) else None,
        "donor_name": data.get("donor_name") if isinstance(data, dict) else None,
        "amount": data.get("amount") if isinstance(data, dict) else None,
        "raw_payload": data
    }
    all_blocks_detail.append(block_info)

    if p_currency == "USD":
        usd_blocks_detail.append(block_info)

conn.close()

# 9. Verify ledger API response
try:
    res = urllib.request.urlopen("http://localhost:8000/api/ledger/verify")
    verify_result = json.loads(res.read().decode("utf-8"))
except Exception as e:
    verify_result = {"error": str(e)}

report = {
    "total_donations": total_donations,
    "donations_table_distribution": donations_dist,
    "total_ledger_blocks": total_ledger_blocks,
    "ledger_blocks_currency_distribution": ledger_dist,
    "usd_blocks_count": len(usd_blocks_detail),
    "usd_blocks_detail": usd_blocks_detail,
    "all_blocks_summary": [
        {
            "index": b["block_index"],
            "event": b["event_type"],
            "donation_id": b["donation_id"],
            "amount": b["amount"],
            "payload_currency": b["payload_currency"]
        } for b in all_blocks_detail
    ],
    "ledger_verify": verify_result
}

with open(r"E:\NGO\backend\usd_inspection_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, default=str)

print("INSPECTION COMPLETE. Saved to E:\\NGO\\backend\\usd_inspection_report.json")
