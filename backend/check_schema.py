import sqlite3
conn = sqlite3.connect(r"E:\NGO\backend\ngo_commons.db")
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(ledger_blocks);")
for col in cursor.fetchall():
    print(col)
conn.close()
