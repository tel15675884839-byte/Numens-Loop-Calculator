from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

import uvicorn

DEFAULT_DESKTOP_BACKEND_PORT = 8765


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Loop Calculator local desktop backend.")
    parser.add_argument("--port", type=int, default=DEFAULT_DESKTOP_BACKEND_PORT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    if getattr(sys, "frozen", False):
        data_dir = Path(sys.executable).parent / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",
        port=args.port,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
