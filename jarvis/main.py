"""JARVIS entry point:  python main.py   (add --no-mic to start in text mode)"""
import sys

from PySide6.QtWidgets import QApplication

from jarvis.assistant import Assistant
from jarvis.ui.fonts import load_inter, make_font
from jarvis.ui.window import HudWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("JARVIS")
    load_inter()
    app.setFont(make_font(10))

    assistant = Assistant(mic_on="--no-mic" not in sys.argv)
    window = HudWindow(assistant)
    assistant.quit_requested.connect(window.close)
    window.show()
    assistant.start()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
