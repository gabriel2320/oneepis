from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "apps" / "api" / "src"
sys.path.insert(0, str(API_SRC))

from oneepis_api.main import app  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Export or check the OneEpis OpenAPI contract.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate packages/contracts/openapi.json without rewriting it.",
    )
    args = parser.parse_args()

    target = ROOT / "packages" / "contracts" / "openapi.json"
    generated = json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not target.exists():
            raise SystemExit(f"OpenAPI contract is missing: {target}")
        current = target.read_text(encoding="utf-8")
        if current != generated:
            raise SystemExit(
                "OpenAPI contract drift detected. "
                "Run `npm run export:openapi` and commit the result.",
            )
        print(f"OpenAPI contract is up to date: {target}")
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(generated, encoding="utf-8")
    print(f"OpenAPI written to {target}")


if __name__ == "__main__":
    main()
