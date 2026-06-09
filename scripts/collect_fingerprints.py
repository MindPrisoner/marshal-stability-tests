"""Collect marshal fingerprints for the current interpreter.

This script is intended for manual comparison across Python versions and
operating systems. It prints JSON so that CI artifacts can be compared later.
"""

from __future__ import annotations

import argparse
import json
import marshal
import platform
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from marshal_stability.cases import stable_cases
from marshal_stability.fingerprint import sha256_of_marshal


def collect(repeats: int) -> dict[str, Any]:
    """Return runtime metadata and fingerprints for all stable cases."""
    fingerprints: dict[str, dict[str, Any]] = {}
    for case in stable_cases():
        hashes = [sha256_of_marshal(case.value) for _ in range(repeats)]
        fingerprints[case.label] = {
            "sha256": hashes[0],
            "stable_within_run": len(set(hashes)) == 1,
        }
    return {
        "python_version": sys.version,
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "marshal_version": marshal.version,
        "repeats": repeats,
        "fingerprints": fingerprints,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=10)
    args = parser.parse_args()
    print(json.dumps(collect(args.repeats), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
