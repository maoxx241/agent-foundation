from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.core.eval.gates import check_contract_drift


def main() -> int:
    drift = check_contract_drift()
    print(json.dumps({"contract_drift": drift}, indent=2, sort_keys=True))
    return 1 if drift else 0


if __name__ == "__main__":
    raise SystemExit(main())
