"""Write the API's OpenAPI document to a file (default: openapi.json).

Each release attaches this file so cairn-app can generate its client from a pinned version.
"""

import json
import sys
from pathlib import Path

from cairn_api.main import create_app


def main() -> None:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "openapi.json")
    out.write_text(json.dumps(create_app().openapi(), indent=2, sort_keys=True) + "\n")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
