"""
Real authentication tests - no fake results.
Run: python test_auth_registration.py
Requires: backend server NOT running (tests auth layer directly, not HTTP).
"""
import sys
import os
import sqlite3
import pathlib

# Must be set BEFORE importing backend.auth so SECRET_KEY binds correctly
os.environ.setdefault("JWT_SECRET", "test-secret-for-unit-test-only")

ROOT = pathlib.Path(__file__).resolve().parent
DB = ROOT / "database" / "users.db"

# ── Clean slate: remove test users from previous runs ──────────────────
def _clean(usernames, emails):
    if not DB.exists():
        return
    conn = sqlite3.connect(str(DB))
    for u in usernames:
        conn.execute("DELETE FROM users WHERE username = ?", (u,))
    for e in emails:
        conn.execute("DELETE FROM users WHERE email = ?", (e,))
    conn.commit()
    conn.close()

_clean(["testuser_a", "testuser_b"], ["usera@test.local", "userb@test.local"])

from backend.auth import (
    initialize_auth_database,
    register_user,
    verify_credentials,
    get_user_by_identifier,
)

initialize_auth_database()

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
results = []

def check(label, condition):
    status = PASS if condition else FAIL
    print(f"  [{status}] {label}")
    results.append((label, condition))

print("\n=== AUTH REGISTRATION TESTS ===\n")

# A. Register User A
print("A. Register User A")
r = register_user("testuser_a", "usera@test.local", "SecurePass1!")
check("register returns ok=True", r["ok"] is True)

# B. Login User A (by username)
print("\nB. Login User A (username)")
check("verify by username", verify_credentials("testuser_a", "SecurePass1!") is True)
user = get_user_by_identifier("testuser_a")
check("user dict returned", user is not None)
check("no password_hash in user dict", "password_hash" not in user)
check("username correct", user and user["username"] == "testuser_a")

# B2. Login User A (by email)
print("\nB2. Login User A (email)")
check("verify by email", verify_credentials("usera@test.local", "SecurePass1!") is True)

# C. Logout is stateless (JWT) - verify user still exists after logout simulation
print("\nC. Logout (stateless - user must still exist)")
conn = sqlite3.connect(str(DB))
row = conn.execute("SELECT username FROM users WHERE username = ?", ("testuser_a",)).fetchone()
conn.close()
check("user still in DB after logout", row is not None)

# D. Login User A again
print("\nD. Login User A again")
check("can login again after logout", verify_credentials("testuser_a", "SecurePass1!") is True)

# E. Register User B
print("\nE. Register User B")
r2 = register_user("testuser_b", "userb@test.local", "AnotherPass2@")
check("register User B ok=True", r2["ok"] is True)

# F. Login User B
print("\nF. Login User B")
check("verify User B by username", verify_credentials("testuser_b", "AnotherPass2@") is True)
check("verify User B by email", verify_credentials("userb@test.local", "AnotherPass2@") is True)

# G. Incorrect password
print("\nG. Incorrect password")
check("wrong password rejected", verify_credentials("testuser_a", "WrongPassword") is False)
check("wrong password for User B rejected", verify_credentials("testuser_b", "WrongPassword") is False)

# H. Duplicate username
print("\nH. Duplicate username")
r3 = register_user("testuser_a", "different@test.local", "Pass123!")
check("duplicate username rejected", r3["ok"] is False)
check("field=username", r3.get("field") == "username")

# I. Duplicate email
print("\nI. Duplicate email")
r4 = register_user("different_user", "usera@test.local", "Pass123!")
check("duplicate email rejected", r4["ok"] is False)
check("field=email", r4.get("field") == "email")

# J. Password not stored as plaintext
print("\nJ. Password not stored as plaintext")
conn = sqlite3.connect(str(DB))
row = conn.execute("SELECT password_hash FROM users WHERE username = ?", ("testuser_a",)).fetchone()
conn.close()
ph = row[0] if row else ""
check("password_hash starts with pbkdf2_sha256", ph.startswith("pbkdf2_sha256$"))
check("plaintext not in hash", "SecurePass1!" not in ph)

# K. JWT token creation
print("\nK. JWT token creation")
from backend.auth import create_access_token, decode_token
token = create_access_token({"sub": "testuser_a", "role": "operator"})
check("token is non-empty string", isinstance(token, str) and len(token) > 10)
payload = decode_token(token)
check("token decodes correctly", payload is not None)
check("sub=testuser_a", payload and payload.get("sub") == "testuser_a")

# ── Cleanup test users ──────────────────────────────────────────────────
_clean(["testuser_a", "testuser_b"], ["usera@test.local", "userb@test.local"])
print("\n(Test users removed from database)\n")

# ── Summary ─────────────────────────────────────────────────────────────
passed = sum(1 for _, ok in results if ok)
total = len(results)
print(f"=== RESULTS: {passed}/{total} passed ===\n")
if passed < total:
    print("FAILED checks:")
    for label, ok in results:
        if not ok:
            print(f"  - {label}")
    sys.exit(1)
else:
    print("All checks passed.")
