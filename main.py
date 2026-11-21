#!/usr/bin/env python3
"""Entry point for the-passport-page-of-a-countr-2-20261121-0318.

Copies the pre-rendered entry.png that sits next to this file in the
repository root into the output directory given by MAKEFUN_OUTPUT_DIR
(default /output), writing it there as entry.png.

Deterministic: the output is a byte-for-byte copy of the input image.
No network, no randomness, no timestamps in the output. Standard
library only, so it runs in the grader's sandbox with nothing installed.
The image itself is rendered by render.py (Pillow, local run only).
"""

import os
import shutil
import sys
from pathlib import Path


def main() -> int:
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"

    source = Path(__file__).resolve().parent / "entry.png"
    if not source.is_file():
        print(f"entry.png not found next to main.py: {source}",
              file=sys.stderr)
        return 1

    destination_dir = Path(output_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / "entry.png"

    shutil.copyfile(source, destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
