"""The animated arc-reactor core."""
import math
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF, QRadialGradient
from PySide6.QtWidgets import QWidget

from .theme import STATE_COLORS, rgba

ENERGY = {"standby": 0.25, "listening": 0.6, "thinking": 0.9, "speaking": 1.0}


class Orb(QWidget):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(360, 360)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.state = "standby"
        self._energy = 0.25
        self._color = QColor(STATE_COLORS["standby"])
        self._t = 0.0
        self._rot = [0.0, 0.0, 0.0]
        self._last = time.perf_counter()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    def set_state(self, state: str):
        self.state = state

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def _tick(self):
        now = time.perf_counter()
        dt = min(now - self._last, 0.05)
        self._last = now
        k = min(1.0, dt * 4)
        self._energy += (ENERGY[self.state] - self._energy) * k
        tgt = QColor(STATE_COLORS[self.state])
        self._color = QColor(
            int(self._color.red() + (tgt.red() - self._color.red()) * k),
            int(self._color.green() + (tgt.green() - self._color.green()) * k),
            int(self._color.blue() + (tgt.blue() - self._color.blue()) * k),
        )
        speed = 0.4 + self._energy * 1.6
        self._rot[0] += dt * 30 * speed
        self._rot[1] -= dt * 14 * speed
        self._rot[2] += dt * 70 * speed
        self._t += dt
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        c = QPointF(w / 2, h / 2)
        R = min(w, h) / 2 - 6
        col, e, t = self._color, self._energy, self._t

        # ambient glow
        g = QRadialGradient(c, R)
        g.setColorAt(0.0, rgba(col, 60 + 50 * e))
        g.setColorAt(0.55, rgba(col, 16 + 10 * e))
        g.setColorAt(1.0, rgba(col, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(g)
        p.drawEllipse(c, R, R)
        p.setBrush(Qt.BrushStyle.NoBrush)

        p.translate(c)

        # outer hairline ring
        p.setPen(QPen(rgba(col, 70), 1))
        p.drawEllipse(QPointF(0, 0), R * 0.98, R * 0.98)

        # tick ring (counter-rotating)
        p.save()
        p.rotate(self._rot[1])
        for i in range(72):
            major = i % 6 == 0
            p.setPen(QPen(rgba(col, 190 if major else 80), 1.4 if major else 1))
            p.drawLine(QPointF(0, -R * 0.93), QPointF(0, -R * 0.93 + (11 if major else 5)))
            p.rotate(5)
        p.restore()

        # three heavy segments
        p.setPen(QPen(rgba(col, 210), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        r = R * 0.80
        rect = QRectF(-r, -r, 2 * r, 2 * r)
        for k in range(3):
            p.drawArc(rect, int((k * 120 + self._rot[0]) * 16), 70 * 16)

        # dashed ring
        pen = QPen(rgba(col, 110), 1.2)
        pen.setStyle(Qt.PenStyle.DashLine)
        p.setPen(pen)
        p.drawEllipse(QPointF(0, 0), R * 0.71, R * 0.71)

        # fast inner arcs
        p.setPen(QPen(rgba(col, 235), 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        r = R * 0.62
        rect = QRectF(-r, -r, 2 * r, 2 * r)
        for k in range(4):
            p.drawArc(rect, int((k * 90 - self._rot[2]) * 16), 28 * 16)

        # listening ripples
        if self.state == "listening":
            for k in range(3):
                ph = (t * 0.7 + k / 3) % 1.0
                p.setPen(QPen(rgba(col, (1 - ph) * 130), 1.5))
                rr = R * (0.30 + 0.42 * ph)
                p.drawEllipse(QPointF(0, 0), rr, rr)

        # radial equalizer
        bars = 72
        amp = {"standby": 0.10, "listening": 0.38, "thinking": 0.30, "speaking": 1.0}[self.state]
        p.save()
        p.setPen(QPen(rgba(col, 200), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for i in range(bars):
            wave = abs(math.sin(t * 3.1 + i * 0.55) * math.cos(t * 1.7 + i * 0.21))
            ln = R * (0.015 + 0.11 * amp * (0.25 + 0.75 * wave))
            p.drawLine(QPointF(0, -R * 0.44), QPointF(0, -R * 0.44 - ln))
            p.rotate(360 / bars)
        p.restore()

        # core
        pulse = 1 + 0.05 * math.sin(t * (2 + 3 * e))
        cr = R * 0.30 * pulse
        cg = QRadialGradient(QPointF(0, 0), cr)
        cg.setColorAt(0.0, QColor(255, 255, 255, 245))
        cg.setColorAt(0.35, rgba(col, 235))
        cg.setColorAt(1.0, rgba(col, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(cg)
        p.drawEllipse(QPointF(0, 0), cr, cr)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(rgba(col, 230), 2))
        p.drawEllipse(QPointF(0, 0), R * 0.33, R * 0.33)

        # rotating triangle (reactor emblem)
        p.save()
        p.rotate(self._rot[0] * 0.8)
        tri = QPolygonF([QPointF(R * 0.17 * math.cos(math.radians(a)), R * 0.17 * math.sin(math.radians(a)))
                         for a in (-90, 30, 150)])
        p.setPen(QPen(QColor(255, 255, 255, 215), 1.6))
        p.drawPolygon(tri)
        p.restore()
