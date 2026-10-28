"""Loads the bundled Inter font and builds QFont objects from it."""
from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase

FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
FAMILY = "Inter"


def load_inter() -> str:
    """Register every bundled Inter weight. Falls back to Segoe UI if files are missing."""
    global FAMILY
    found = None
    for ttf in sorted(FONT_DIR.glob("Inter-*.ttf")):
        fid = QFontDatabase.addApplicationFont(str(ttf))
        if fid != -1 and found is None:
            families = QFontDatabase.applicationFontFamilies(fid)
            found = families[0] if families else None
    FAMILY = found or "Segoe UI"
    return FAMILY


def make_font(size: float, weight: QFont.Weight = QFont.Weight.Normal, spacing: float = 0) -> QFont:
    f = QFont(FAMILY)
    f.setPointSizeF(size)
    f.setWeight(weight)
    if spacing:
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, spacing)
    return f
