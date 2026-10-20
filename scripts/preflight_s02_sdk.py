"""Read-only S02 SDK compatibility check; prints class and signature names only."""

from __future__ import annotations

import importlib.metadata
import inspect

from sie_sdk import SIEClient
from sie_sdk.client import errors


REQUIRED_ERRORS = (
    "ModelLoadingError",
    "ProvisioningError",
    "RequestError",
    "ServerError",
    "SIEConnectionError",
    "SIEError",
)


def main() -> int:
    version = importlib.metadata.version("sie-sdk")
    missing = [
        name for name in REQUIRED_ERRORS if not isinstance(getattr(errors, name, None), type)
    ]
    params = inspect.signature(SIEClient.encode).parameters
    required_options = ("output_types", "is_query")
    missing_options = [name for name in required_options if name not in params]
    print(f"sie-sdk version: {version}")
    present_errors = ", ".join(name for name in REQUIRED_ERRORS if name not in missing)
    present_options = ", ".join(name for name in required_options if name not in missing_options)
    print(f"SDK errors present: {present_errors}")
    print(f"encode options present: {present_options}")
    print(f"missing error classes: {', '.join(missing) if missing else 'none'}")
    print(f"missing encode options: {', '.join(missing_options) if missing_options else 'none'}")
    if version != "0.6.4" or missing or missing_options:
        print("S02 SDK compatibility: BLOCKED; do not apply implementation until reconciled.")
        return 1
    print("S02 SDK compatibility: static surface PASS; runtime exception semantics need tests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
