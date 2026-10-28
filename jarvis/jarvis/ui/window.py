"""Main HUD window."""
import html
import os
from datetime import datetime
from pathlib import Path

import psutil
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QFont, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from .fonts import make_font
from .orb import Orb
from .theme import (
    BG_BOTTOM,
    BG_TOP,
    CYAN,
    STATE_COLORS,
    STATE_HINTS,
    STATE_LABELS,
    TEXT,
    TEXT_DIM,
    rgba,
)
from .widgets import Panel, SectionTitle, StatBar

QUICK_ACTIONS = [
    ("Time", "what time is it"), ("System", "system status"),
    ("Weather", "weather"), ("Screenshot", "take a screenshot"),
    ("Note", "take a note"), ("Desktop", "show desktop"),
]

CHIP_QSS = """
QPushButton {
    color: #BFEFFF; background: rgba(34,211,238,0.07);
    border: 1px solid rgba(34,211,238,0.28); border-radius: 13px; padding: 7px 10px; font-size: 9pt;
}
QPushButton:hover { background: rgba(34,211,238,0.20); border-color: rgba(34,211,238,0.7); }
QPushButton:pressed { background: rgba(34,211,238,0.32); }
QPushButton:checked { background: rgba(52,245,197,0.18); border-color: rgba(52,245,197,0.8); color: #D6FFF3; }
"""
INPUT_QSS = f"""
QLineEdit {{
    color: {TEXT}; background: rgba(34,211,238,0.06); border: 1px solid rgba(34,211,238,0.28);
    border-radius: 14px; padding: 9px 14px; font-size: 10pt; selection-background-color: {CYAN};
    selection-color: #021018;
}}
QLineEdit:focus {{ border-color: rgba(34,211,238,0.85); }}
"""
WINBTN_QSS = """
QPushButton { color: #8FB3CC; background: transparent; border: none; font-size: 16pt; padding: 0 10px; }
QPushButton:hover { color: #FFFFFF; }
"""


class HudWindow(QWidget):
    def __init__(self, assistant):
        super().__init__()
        self.assistant = assistant
        self.setWindowTitle("JARVIS")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(1200, 740)
        self.setMinimumSize(1060, 680)
        self._build()
        self._wire()

        self._stats = QTimer(self)
        self._stats.timeout.connect(self._refresh_stats)
        self._stats.start(1000)
        self._refresh_stats()
        self.set_state("standby")

        self.setWindowOpacity(0.0)
        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setDuration(700)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)

    def showEvent(self, e):
        super().showEvent(e)
        self._fade.start()

    # ------------------------------------------------------------------ layout
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 18, 26, 22)
        root.setSpacing(16)

        # --- top bar
        top = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(1)
        title = QLabel("J.A.R.V.I.S")
        title.setFont(make_font(15, QFont.Weight.Bold, 5))
        title.setStyleSheet("color: #E6F8FF;")
        sub = QLabel("JUST A RATHER VERY INTELLIGENT SYSTEM")
        sub.setFont(make_font(7, QFont.Weight.Medium, 2))
        sub.setStyleSheet(f"color: {TEXT_DIM};")
        titles.addWidget(title)
        titles.addWidget(sub)
        top.addLayout(titles)
        top.addStretch()
        ver = QLabel(f"v{__version__}")
        ver.setFont(make_font(8, QFont.Weight.Medium, 1))
        ver.setStyleSheet(f"color: {TEXT_DIM};")
        top.addWidget(ver)
        for text, slot in (("–", self.showMinimized), ("×", self.close)):
            b = QPushButton(text)
            b.setStyleSheet(WINBTN_QSS)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(slot)
            top.addWidget(b)
        root.addLayout(top)

        body = QHBoxLayout()
        body.setSpacing(18)
        root.addLayout(body, 1)

        # --- left: system
        left = Panel("System status")
        left.setFixedWidth(250)
        self.clock = QLabel("--:--")
        self.clock.setFont(make_font(30, QFont.Weight.Light))
        self.clock.setStyleSheet("color: #EAF9FF;")
        self.date = QLabel("")
        self.date.setFont(make_font(9, QFont.Weight.Medium, 1))
        self.date.setStyleSheet(f"color: {TEXT_DIM};")
        left.body.addWidget(self.clock)
        left.body.addWidget(self.date)
        left.body.addSpacing(8)
        self.bar_cpu, self.bar_ram = StatBar("CPU"), StatBar("Memory")
        self.bar_disk, self.bar_bat = StatBar("Disk"), StatBar("Battery", low_is_bad=True)
        for b in (self.bar_cpu, self.bar_ram, self.bar_disk, self.bar_bat):
            left.body.addWidget(b)
        left.body.addSpacing(10)
        left.body.addWidget(SectionTitle("Quick actions"))
        grid = QGridLayout()
        grid.setSpacing(8)
        for i, (label, cmd) in enumerate(QUICK_ACTIONS):
            b = QPushButton(label)
            b.setStyleSheet(CHIP_QSS)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _=False, c=cmd: self.assistant.submit(c))
            grid.addWidget(b, i // 2, i % 2)
        left.body.addLayout(grid)
        left.body.addStretch()
        body.addWidget(left)

        # --- center: core
        center = QVBoxLayout()
        center.addStretch()
        self.orb = Orb()
        center.addWidget(self.orb, 0, Qt.AlignmentFlag.AlignHCenter)
        self.status = QLabel("STANDBY")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setFont(make_font(20, QFont.Weight.Light, 9))
        self.hint = QLabel("")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint.setFont(make_font(9, QFont.Weight.Normal, 0.5))
        self.hint.setStyleSheet(f"color: {TEXT_DIM};")
        center.addSpacing(6)
        center.addWidget(self.status)
        center.addWidget(self.hint)
        center.addSpacing(10)
        self.mic_btn = QPushButton("MIC ON")
        self.mic_btn.setCheckable(True)
        self.mic_btn.setChecked(self.assistant.mic_on)
        self.mic_btn.setFont(make_font(8, QFont.Weight.DemiBold, 2))
        self.mic_btn.setStyleSheet(CHIP_QSS)
        self.mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mic_btn.setFixedWidth(130)
        center.addWidget(self.mic_btn, 0, Qt.AlignmentFlag.AlignHCenter)
        center.addStretch()
        body.addLayout(center, 1)

        # --- right: conversation
        right = Panel("Conversation")
        right.setFixedWidth(350)
        self.chat = QTextBrowser()
        self.chat.setFrameShape(QTextBrowser.Shape.NoFrame)
        self.chat.setFont(make_font(10))
        self.chat.setStyleSheet(
            "QTextBrowser { background: transparent; color: #D7E6F2; }"
            "QScrollBar:vertical { width: 6px; background: transparent; }"
            "QScrollBar::handle:vertical { background: rgba(34,211,238,0.35); border-radius: 3px; min-height: 30px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
        )
        right.body.addWidget(self.chat, 1)
        row = QHBoxLayout()
        row.setSpacing(8)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Type a command...")
        self.input.setStyleSheet(INPUT_QSS)
        send = QPushButton("Send")
        send.setStyleSheet(CHIP_QSS)
        send.setCursor(Qt.CursorShape.PointingHandCursor)
        send.clicked.connect(self._send)
        self.input.returnPressed.connect(self._send)
        row.addWidget(self.input, 1)
        row.addWidget(send)
        right.body.addLayout(row)
        body.addWidget(right)

    def _wire(self):
        a = self.assistant
        a.state_changed.connect(self.set_state)
        a.user_said.connect(lambda t: self.add_message("YOU", t, TEXT_DIM))
        a.jarvis_said.connect(lambda t: self.add_message("JARVIS", t, CYAN))
        a.notice.connect(lambda t: self.add_message("SYSTEM", t, "#FBBF24"))
        a.mic_changed.connect(self._mic_changed)
        self.orb.clicked.connect(a.push_to_talk)
        self.mic_btn.toggled.connect(a.set_mic)
        self._mic_changed(a.mic_on)

    # ------------------------------------------------------------------ behaviour
    def _send(self):
        text = self.input.text().strip()
        if text:
            self.assistant.submit(text)
            self.input.clear()

    def _mic_changed(self, on: bool):
        self.mic_btn.blockSignals(True)
        self.mic_btn.setChecked(on)
        self.mic_btn.setText("MIC ON" if on else "MIC OFF")
        self.mic_btn.blockSignals(False)

    def set_state(self, state: str):
        self.orb.set_state(state)
        color = STATE_COLORS[state]
        self.status.setText(STATE_LABELS[state])
        self.status.setStyleSheet(f"color: {color};")
        self.hint.setText(STATE_HINTS[state])
        self.update()

    def add_message(self, who: str, text: str, color: str):
        body_color = "#EAF6FF" if who == "JARVIS" else "#B9CCDA"
        self.chat.append(
            f'<div style="margin-bottom:12px;">'
            f'<span style="color:{color}; font-size:7.5pt; font-weight:600; letter-spacing:2px;">{who}</span><br>'
            f'<span style="color:{body_color}; font-size:10pt;">{html.escape(text)}</span></div>'
        )
        self.chat.verticalScrollBar().setValue(self.chat.verticalScrollBar().maximum())

    def _refresh_stats(self):
        now = datetime.now()
        self.clock.setText(now.strftime("%I:%M").lstrip("0") + now.strftime(" %p"))
        self.date.setText(now.strftime("%A, %d %B").upper())
        self.bar_cpu.set_value(psutil.cpu_percent())
        self.bar_ram.set_value(psutil.virtual_memory().percent)
        self.bar_disk.set_value(psutil.disk_usage(Path.home().anchor or os.sep).percent)
        bat = psutil.sensors_battery()
        if bat:
            self.bar_bat.set_value(bat.percent, f"{bat.percent:.0f}%{' ⚡' if bat.power_plugged else ''}")
        else:
            self.bar_bat.set_value(100, "AC POWER")

    # ------------------------------------------------------------------ window chrome
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and e.position().y() < 70:
            self.windowHandle().startSystemMove()

    def closeEvent(self, e):
        self.assistant.stop()
        if not self.assistant.wait(1500):
            self.assistant.terminate()
        super().closeEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        path = QPainterPath()
        path.addRoundedRect(1, 1, w - 2, h - 2, 18, 18)
        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0, BG_TOP)
        bg.setColorAt(1, BG_BOTTOM)
        p.fillPath(path, bg)
        p.setClipPath(path)
        p.setPen(QPen(rgba(CYAN, 9), 1))
        for x in range(0, w, 40):
            p.drawLine(x, 0, x, h)
        for y in range(0, h, 40):
            p.drawLine(0, y, w, y)
        glow = QRadialGradient(w / 2, h / 2, w * 0.42)
        glow.setColorAt(0, rgba(STATE_COLORS[self.orb.state], 34))
        glow.setColorAt(1, rgba(STATE_COLORS[self.orb.state], 0))
        p.fillRect(self.rect(), glow)
        p.setClipping(False)
        p.setPen(QPen(rgba(CYAN, 80), 1))
        p.drawPath(path)
        p.setPen(QPen(rgba(CYAN, 28), 1))
        p.drawLine(26, 68, w - 26, 68)
