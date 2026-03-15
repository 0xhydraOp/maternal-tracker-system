"""
Generate and provide the application icon for the Maternal Tracker.
Creates a heart + care symbol icon suitable for maternal health tracking.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, Qt, QRectF
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPixmap

from config import BASE_DIR

ICON_PATH = BASE_DIR / "assets" / "icon.png"


def _create_icon_pixmap(size: int) -> QPixmap:
    """Create the app icon as a pixmap - heart shape in maternal care style."""
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)

    # Background circle - soft teal/blue (maternal, care, health)
    bg_color = QColor("#2c7be5")
    painter.setBrush(bg_color)
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(2, 2, size - 4, size - 4)

    # Heart path - white
    scale = size / 64
    cx, cy = size / 2, size / 2 + 2 * scale
    # Simple heart using Bezier curves
    path = QPainterPath()
    path.moveTo(cx, cy + 8 * scale)
    path.cubicTo(cx - 12 * scale, cy - 8 * scale, cx - 16 * scale, cy - 16 * scale, cx, cy - 6 * scale)
    path.cubicTo(cx + 16 * scale, cy - 16 * scale, cx + 12 * scale, cy - 8 * scale, cx, cy + 8 * scale)
    path.closeSubpath()

    painter.setBrush(QColor("white"))
    painter.setPen(Qt.NoPen)
    painter.drawPath(path)

    painter.end()
    return pix


def ensure_icon_exists() -> None:
    """Create the icon file if it doesn't exist."""
    if ICON_PATH.exists():
        return
    ICON_PATH.parent.mkdir(parents=True, exist_ok=True)
    pix = _create_icon_pixmap(256)
    pix.save(str(ICON_PATH))


def get_app_icon() -> QIcon:
    """Return the application icon, creating it if needed."""
    ensure_icon_exists()
    icon = QIcon(str(ICON_PATH))
    # Add scaled versions for different DPI
    for sz in [16, 32, 48, 64, 128, 256]:
        icon.addPixmap(_create_icon_pixmap(sz))
    return icon
