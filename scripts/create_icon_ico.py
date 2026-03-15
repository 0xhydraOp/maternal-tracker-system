"""Create icon.ico from icon.png for Windows build."""
from __future__ import annotations

import sys
from pathlib import Path

# Project root is parent of scripts/
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

ICON_PNG = ROOT / "assets" / "icon.png"
ICON_ICO = ROOT / "assets" / "icon.ico"


def main() -> None:
    if not ICON_PNG.exists():
        from utils.icon_utils import ensure_icon_exists
        ensure_icon_exists()
    from PIL import Image
    img = Image.open(ICON_PNG)
    img.save(ICON_ICO, format="ICO", sizes=[(256, 256), (48, 48), (32, 32), (16, 16)])
    print(f"Created {ICON_ICO}")


if __name__ == "__main__":
    main()
