from __future__ import annotations

import sys

from apps.cli.main import main


if __name__ == "__main__":
    sys.argv = [sys.argv[0], "migrate-artifact-schema", *sys.argv[1:]]
    raise SystemExit(main())
