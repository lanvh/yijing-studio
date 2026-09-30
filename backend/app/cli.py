import argparse
import getpass
import os

from pydantic import EmailStr, TypeAdapter, ValidationError

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.auth import AuthService, DuplicateUser


def main():
    parser = argparse.ArgumentParser(description="Create a local AI Seed Studio account.")
    parser.add_argument("command", choices=["create-user"])
    parser.add_argument("--email")
    parser.add_argument("--display-name", default="创作者")
    parser.add_argument("--role", choices=["admin", "user"], default="user")
    parser.add_argument("--from-env", action="store_true", help="Read ADMIN_EMAIL/ADMIN_PASSWORD.")
    args = parser.parse_args()
    get_settings()
    if args.from_env:
        from dotenv import load_dotenv

        load_dotenv("../.env")
        load_dotenv(".env")
        email = args.email or os.getenv("ADMIN_EMAIL", "")
        password = os.getenv("ADMIN_PASSWORD", "")
    else:
        email = args.email or input("Email: ").strip()
        password = getpass.getpass("Password (12-128 characters): ")
        if password != getpass.getpass("Confirm password: "):
            parser.exit(1, "Passwords do not match.\n")
    try:
        email = str(TypeAdapter(EmailStr).validate_python(email)).lower()
        with SessionLocal() as db:
            user = AuthService(db).create_user(email, password, args.display_name, args.role)
            print(f"Created account: {user.email} ({user.role})")
    except DuplicateUser:
        parser.exit(1, "Account already exists; no changes made.\n")
    except (ValueError, ValidationError):
        # Validation inputs may contain credentials; do not echo them.
        parser.exit(1, "Invalid email, password length, or display name.\n")


if __name__ == "__main__":
    main()
