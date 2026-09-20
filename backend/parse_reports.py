import json

with open(r"E:\NGO\backend\db_inspection_report.json", "r", encoding="utf-8") as f:
    db_rep = json.load(f)

with open(r"E:\NGO\code_search_report.json", "r", encoding="utf-8") as f:
    code_rep = json.load(f)

print("=== DB SUMMARY ===")
print("Active DB Path:", db_rep["db_path"])
print("Backup Path:", db_rep["backup_path"])
print("Backup Exists:", db_rep["backup_exists"])
print("\nTables:")
for tbl, info in db_rep["tables"].items():
    print(f"  - {tbl}: {info['count']} rows, columns: {info['columns']}")

print("\nDonation Currency Distribution:")
print(db_rep["donation_currency_dist"])
print(f"Total Donations: {db_rep['total_donations_count']}, Total Sum: {db_rep['total_donations_sum']}")

print(f"\nLedger Blocks Count: {db_rep['ledger_count']}")
print("Ledger Verify Status:", db_rep["ledger_verify"])

print("\nRecent Donations:")
for d in db_rep["recent_donations"][:5]:
    print("  ", d)

print("\n=== CODE SEARCH SUMMARY ===")
print(f"Backend matches count: {code_rep['backend_matches_count']}")
print(f"Frontend matches count: {code_rep['frontend_matches_count']}")

# Group backend matches by file
be_files = {}
for m in code_rep["backend_matches"]:
    be_files.setdefault(m["file"], []).append(m)

print("\nBackend Files with USD/Currency:")
for f, matches in be_files.items():
    print(f"  - {f} ({len(matches)} matches)")

# Group frontend matches by file
fe_files = {}
for m in code_rep["frontend_matches"]:
    fe_files.setdefault(m["file"], []).append(m)

print("\nFrontend Files with USD/Currency:")
for f, matches in fe_files.items():
    print(f"  - {f} ({len(matches)} matches)")
