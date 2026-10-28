"""Background worker: listens, thinks, acts, speaks - and reports state to the UI via signals."""
import datetime
import queue
import re
import threading

from PySide6.QtCore import QThread, Signal

from . import config
from .brain import Brain
from .skills import handle
from .voice import Listener, Speaker

YES = re.compile(r"\b(yes|yeah|yep|sure|confirm|do it|proceed|go ahead|affirmative)\b")


class Assistant(QThread):
    state_changed = Signal(str)     # standby | listening | thinking | speaking
    user_said = Signal(str)
    jarvis_said = Signal(str)
    notice = Signal(str)
    mic_changed = Signal(bool)
    quit_requested = Signal()

    def __init__(self, mic_on: bool = True):
        super().__init__()
        self.mic_on = mic_on
        self.brain = Brain()
        self._q: queue.Queue = queue.Queue()
        self._ptt = threading.Event()
        self._running = True
        self.speaker = None
        self.listener = None

    # ---------- thread-safe API for the UI ----------
    def submit(self, text: str):
        if text.strip():
            self._q.put(text.strip())

    def set_mic(self, on: bool):
        self.mic_on = on and bool(self.listener and self.listener.available)
        self.mic_changed.emit(self.mic_on)

    def push_to_talk(self):
        if self.listener is not None and not self.listener.available:
            self.notice.emit("Microphone unavailable. Type your command instead.")
            return
        self._ptt.set()

    def stop(self):
        self._running = False
        self._q.put(None)

    # ---------- ctx interface used by skills ----------
    def say(self, text: str):
        self.jarvis_said.emit(text)
        self.state_changed.emit("speaking")
        self.speaker.say(text)

    def hear(self) -> str:
        self.state_changed.emit("listening")
        if self.listener.available:
            heard = self.listener.listen(7, 10)
        else:
            heard = self._typed(20) or ""
        if heard:
            self.user_said.emit(heard)
        return heard

    def confirm(self, question: str) -> bool:
        self.say(question)
        return bool(YES.search(self.hear()))

    # ---------- internals ----------
    def _typed(self, timeout: float):
        try:
            return self._q.get(timeout=timeout) if timeout else self._q.get_nowait()
        except queue.Empty:
            return None

    def _process(self, cmd: str):
        self.state_changed.emit("thinking")
        if not handle(cmd, self, self.brain):
            self._running = False
            self.quit_requested.emit()
        self.state_changed.emit("standby")

    def run(self):
        self.speaker = Speaker()          # COM objects must live in this thread
        self.listener = Listener()
        if not self.listener.available:
            self.mic_on = False
            self.mic_changed.emit(False)
            self.notice.emit("No microphone detected - text mode only. Install PyAudio to enable voice.")
        h = datetime.datetime.now().hour
        part = "morning" if h < 12 else "afternoon" if h < 18 else "evening"
        self.say(f"Good {part}, {config.USER_TITLE}. JARVIS online and at your service.")
        self.state_changed.emit("standby")

        while self._running:
            typed = self._typed(0)
            if typed:
                self.user_said.emit(typed)
                self._process(typed)
                continue

            if self._ptt.is_set():                      # orb clicked: listen once, no wake word
                self._ptt.clear()
                self.state_changed.emit("listening")
                heard = self.listener.listen(6, 10)
                if heard:
                    self.user_said.emit(heard)
                    self._process(heard)
                else:
                    self.state_changed.emit("standby")
                continue

            if self.mic_on and self.listener.available:  # always-on wake-word loop
                heard = self.listener.listen(2, 8)
                if config.WAKE_WORD in heard:
                    cmd = heard.split(config.WAKE_WORD, 1)[1].strip(" ,.")
                    if not cmd:
                        self.say("Yes?")
                        cmd = self.hear()
                    else:
                        self.user_said.emit(cmd)
                    if cmd:
                        self._process(cmd)
                continue

            typed = self._typed(0.2)
            if typed:
                self.user_said.emit(typed)
                self._process(typed)
