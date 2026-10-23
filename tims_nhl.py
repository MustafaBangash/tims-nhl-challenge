"""Run the project directly from a source checkout without installing it."""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from tims_nhl_challenge.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())

