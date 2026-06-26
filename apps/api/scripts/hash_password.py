from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "apps" / "api" / "src"
sys.path.insert(0, str(API_SRC))

from oneepis_api.services.auth import hash_password  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a PBKDF2 password hash for OneEpis.")
    parser.add_argument(
        "--password",
        help="Password to hash. Omit it to enter the password without echo.",
    )
    args = parser.parse_args()

    password = args.password if args.password is not None else getpass.getpass("Password: ")
    if not password:
        raise SystemExit("Password cannot be empty.")

    print(hash_password(password))


if __name__ == "__main__":
    main()
