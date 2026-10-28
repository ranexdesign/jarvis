"""Colours and state definitions for the HUD."""
from PySide6.QtGui import QColor

BG_TOP = QColor("#0A1626")
BG_BOTTOM = QColor("#040910")
TEXT = "#D7E6F2"
TEXT_DIM = "#6E8AA3"
CYAN = "#22D3EE"
AMBER = "#FBBF24"
RED = "#F87171"

STATE_COLORS = {
    "standby": "#22D3EE",
    "listening": "#34F5C5",
    "thinking": "#FBBF24",
    "speaking": "#7DE8FF",
}
STATE_LABELS = {
    "standby": "STANDBY",
    "listening": "LISTENING",
    "thinking": "PROCESSING",
    "speaking": "SPEAKING",
}
STATE_HINTS = {
    "standby": 'Say "Jarvis" or click the core to talk',
    "listening": "I'm listening...",
    "thinking": "Working on it...",
    "speaking": "",
}


def rgba(color: QColor | str, alpha: int) -> QColor:
    c = QColor(color)
    c.setAlpha(max(0, min(255, int(alpha))))
    return c
