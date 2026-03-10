from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.core.config import contracts_root, generated_root
from packages.core.contracts import build_jsonschema_contracts, build_openapi_contracts
from packages.core.storage.fs_utils import ensure_dir, write_json_atomic


def main() -> None:
    generated = generated_root()
    contracts = contracts_root()

    generated_openapi = generated / "openapi"
    generated_schemas = generated / "jsonschema"
    frozen_openapi = contracts / "openapi"
    frozen_schemas = contracts / "jsonschema"
    for path in (generated_openapi, generated_schemas, frozen_openapi, frozen_schemas):
        ensure_dir(path)

    openapi_contracts = build_openapi_contracts()
    jsonschema_contracts = build_jsonschema_contracts()

    for name, payload in openapi_contracts.items():
        write_json_atomic(generated_openapi / name, payload)
        write_json_atomic(frozen_openapi / name, payload)

    for name, payload in jsonschema_contracts.items():
        write_json_atomic(generated_schemas / name, payload)
        write_json_atomic(frozen_schemas / name, payload)

    print(
        json.dumps(
            {
                "generated_openapi": sorted(openapi_contracts.keys()),
                "generated_jsonschema": sorted(jsonschema_contracts.keys()),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
