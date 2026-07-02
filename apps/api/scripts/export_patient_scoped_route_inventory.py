from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "apps" / "api" / "src"
sys.path.insert(0, str(API_SRC))

from oneepis_api.core.patient_scoped_route_inventory import (  # noqa: E402
    PATIENT_SCOPED_ROUTE_INVENTORY,
)


def main() -> None:
    json.dump(
        [asdict(route) for route in PATIENT_SCOPED_ROUTE_INVENTORY],
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
