"""Create the first admin account.  Run:  python create_admin.py"""
import getpass
import sys

from accounts import create_user
from db import init_db
from utils.validation import password_problem, valid_email


def main():
    init_db()
    name = input("Admin name: ").strip() or "Shop Admin"
    email = input("Admin email: ").strip().lower()
    if not valid_email(email):
        sys.exit("That email address does not look valid.")
    password = getpass.getpass("Password (min 8 chars, letters + numbers): ")
    problem = password_problem(password)
    if problem:
        sys.exit(problem)
    if getpass.getpass("Confirm password: ") != password:
        sys.exit("Passwords do not match.")
    ok, msg = create_user(name, email, "", password, role="admin")
    print(msg)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
