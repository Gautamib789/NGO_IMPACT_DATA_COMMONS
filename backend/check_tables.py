import sqlite3
conn = sqlite3.connect(r"E:\NGO\backend\ngo_commons.db")
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables in DB:", c.fetchall())
conn.close()
