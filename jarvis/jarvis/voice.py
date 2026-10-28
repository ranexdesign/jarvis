"""Speech in (SpeechRecognition) and speech out (pyttsx3). Both degrade gracefully."""
from . import config


class Speaker:
    """Offline Windows SAPI5 voice. Must be created and used from one thread."""

    def __init__(self):
        self.ok = False
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", 175)
            for v in self._engine.getProperty("voices"):
                if any(k in v.name.lower() for k in ("david", "mark", "george", "ravi")):
                    self._engine.setProperty("voice", v.id)
                    break
            self.ok = True
        except Exception as e:  # noqa: BLE001 - any driver failure should not crash the UI
            print(f"[tts disabled] {e}")

    def say(self, text: str):
        if self.ok:
            self._engine.say(text)
            self._engine.runAndWait()


class Listener:
    def __init__(self):
        self.available = False
        try:
            import speech_recognition as sr
            self._sr = sr
            self._rec = sr.Recognizer()
            self._rec.pause_threshold = 0.8
            self._rec.dynamic_energy_threshold = True
            with sr.Microphone() as mic:           # probe + calibrate once
                self._rec.adjust_for_ambient_noise(mic, duration=0.6)
            self.available = True
        except Exception as e:  # noqa: BLE001 - no mic / no PyAudio
            print(f"[mic disabled] {e}")

    def listen(self, timeout=6, phrase_limit=10) -> str:
        if not self.available:
            return ""
        sr = self._sr
        try:
            with sr.Microphone() as mic:
                audio = self._rec.listen(mic, timeout=timeout, phrase_time_limit=phrase_limit)
            return self._rec.recognize_google(audio, language=config.LANGUAGE).lower()
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            return ""
        except (sr.RequestError, OSError):
            return ""
