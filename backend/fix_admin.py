"""Fix admin password and verify all database users."""
from passlib.context import CryptContext
import sqlite3

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
new_hash = pwd.hash("AdminPassword123!")

conn = sqlite3.connect("ngo_commons.db")

# Update admin password
conn.execute("UPDATE users SET hashed_password=? WHERE email=?", (new_hash, "admin@ngoimpact.org"))
conn.commit()

# Show all users
rows = conn.execute("SELECT id, email, role, is_active FROM users").fetchall()
print("\n--- Users in database ---")
for r in rows:
    print(f"  id={r[0]}  role={r[2]:<8}  active={r[3]}  email={r[1]}")

# Verify password works
admin_row = conn.execute("SELECT hashed_password FROM users WHERE email=?", ("admin@ngoimpact.org",)).fetchone()
if admin_row and pwd.verify("AdminPassword123!", admin_row[0]):
    print("\n  [OK] Admin password hash verified successfully")
else:
    print("\n  [FAIL] Admin password hash mismatch!")

conn.close()
