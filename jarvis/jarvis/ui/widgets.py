"""Reusable HUD widgets: panel with corner brackets, stat bar, section title."""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from .fonts import make_font
from .theme import AMBER, CYAN, RED, TEXT, TEXT_DIM, rgba


class Panel(QFrame):
    """Translucent glass panel with cyan corner brackets."""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(18, 16, 18, 16)
        self.body.setSpacing(10)
        if title:
            self.body.addWidget(SectionTitle(title))

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(r, 12, 12)
        p.fillPath(path, QColor(8, 22, 36, 150))
        p.setPen(QPen(rgba(CYAN, 45), 1))
        p.drawPath(path)
        p.setPen(QPen(rgba(CYAN, 220), 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        L, m = 14, 1.5
        x0, y0, x1, y1 = r.left() + m, r.top() + m, r.right() - m, r.bottom() - m
        for (x, y, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            p.drawLine(int(x), int(y), int(x + dx * L), int(y))
            p.drawLine(int(x), int(y), int(x), int(y + dy * L))


class SectionTitle(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text.upper(), parent)
        self.setFont(make_font(8, QFont.Weight.DemiBold, 2.4))
        self.setStyleSheet(f"color: {rgba(CYAN, 190).name(QColor.NameFormat.HexArgb)};")


class StatBar(QWidget):
    """Label + value on one row, thin gradient bar beneath."""

    def __init__(self, label: str, low_is_bad: bool = False, parent=None):
        super().__init__(parent)
        self.label = label.upper()
        self.low_is_bad = low_is_bad   # True for battery: warn when LOW instead of high
        self.value = 0.0
        self.text = "--"
        self.setFixedHeight(40)

    def set_value(self, pct: float, text: str | None = None):
        self.value = max(0.0, min(100.0, pct))
        self.text = text if text is not None else f"{self.value:.0f}%"
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        p.setFont(make_font(8, QFont.Weight.DemiBold, 1.6))
        p.setPen(QColor(TEXT_DIM))
        p.drawText(0, 0, w, 18, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.label)
        p.setFont(make_font(10, QFont.Weight.Medium))
        p.setPen(QColor(TEXT))
        p.drawText(0, 0, w, 18, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, self.text)

        track = QRectF(0, 26, w, 4)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(rgba(CYAN, 28))
        p.drawRoundedRect(track, 2, 2)
        if self.low_is_bad:
            base = RED if self.value < 15 else AMBER if self.value < 30 else CYAN
        else:
            base = RED if self.value > 90 else AMBER if self.value > 75 else CYAN
        fill = QRectF(0, 26, w * self.value / 100, 4)
        g = QLinearGradient(fill.left(), 0, max(fill.right(), 1), 0)
        g.setColorAt(0, rgba(base, 120))
        g.setColorAt(1, QColor(base))
        p.setBrush(g)
        p.drawRoundedRect(fill, 2, 2)
