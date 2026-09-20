import os
import shutil
import sqlite3
import json
import urllib.request
from datetime import datetime

DB_PATH = r"E:\NGO\backend\ngo_commons.db"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_PATH = os.path.join(r"E:\NGO\backend", f"ngo_commons_before_inr_migration_{TIMESTAMP}.db")

# 1. Create Backup
if not os.path.exists(BACKUP_PATH):
    print(f"Creating backup from {DB_PATH} to {BACKUP_PATH}...")
    shutil.copy2(DB_PATH, BACKUP_PATH)

backup_exists = os.path.exists(BACKUP_PATH)
print(f"Backup created: {backup_exists} (Size: {os.path.getsize(BACKUP_PATH)} bytes)")

# 2. Inspect Database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]
print(f"\nDatabase Tables ({len(tables)}): {tables}")

table_details = {}
for tbl in tables:
    cursor.execute(f"PRAGMA table_info('{tbl}');")
    cols = [row[1] for row in cursor.fetchall()]
    cursor.execute(f"SELECT count(*) FROM '{tbl}';")
    cnt = cursor.fetchone()[0]
    table_details[tbl] = {"count": cnt, "columns": cols}

# Inspect Currency in Donations if table exists
donation_currency_dist = []
total_donations_count = 0
total_donations_sum = 0
recent_donations = []

if "donations" in tables:
    cursor.execute("SELECT count(*), currency FROM donations GROUP BY currency;")
    donation_currency_dist = cursor.fetchall()

    cursor.execute("SELECT count(*), sum(amount) FROM donations;")
    total_donations_count, total_donations_sum = cursor.fetchone()

    cursor.execute("SELECT * FROM donations ORDER BY id DESC LIMIT 10;")
    recent_donations = cursor.fetchall()

# Inspect Ledger Blocks if table exists
ledger_count = 0
recent_blocks = []
if "ledger_blocks" in tables:
    cursor.execute("SELECT count(*) FROM ledger_blocks;")
    ledger_count = cursor.fetchone()[0]

    cursor.execute("SELECT `index`, event_type, payload_json, previous_hash, block_hash FROM ledger_blocks ORDER BY `index` DESC LIMIT 5;")
    recent_blocks = cursor.fetchall()

conn.close()

# 3. Ledger verification via API
try:
    res = urllib.request.urlopen("http://localhost:8000/api/ledger/verify")
    verify_res = json.loads(res.read().decode("utf-8"))
except Exception as e:
    verify_res = {"error": str(e)}

report_data = {
    "db_path": DB_PATH,
    "backup_path": BACKUP_PATH,
    "backup_exists": backup_exists,
    "tables": table_details,
    "donation_currency_dist": donation_currency_dist,
    "total_donations_count": total_donations_count,
    "total_donations_sum": total_donations_sum,
    "recent_donations": recent_donations,
    "ledger_count": ledger_count,
    "recent_blocks": recent_blocks,
    "ledger_verify": verify_res
}

with open(r"E:\NGO\backend\db_inspection_report.json", "w", encoding="utf-8") as f:
    json.dump(report_data, f, indent=2, default=str)

print("\nDB Inspection Complete. Written to E:\\NGO\\backend\\db_inspection_report.json")
