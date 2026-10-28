"""LLM brain - talks to a local Ollama server (free, offline)."""
import requests

from . import config


class Brain:
    def __init__(self):
        self.history: list[dict] = []

    def clear(self):
        self.history.clear()

    def ask(self, prompt: str) -> str:
        self.history.append({"role": "user", "content": prompt})
        self.history = self.history[-12:]
        try:
            r = requests.post(config.OLLAMA_URL, timeout=120, json={
                "model": config.MODEL, "stream": False,
                "messages": [{"role": "system", "content": config.SYSTEM_PROMPT}] + self.history,
            })
            r.raise_for_status()
            reply = r.json()["message"]["content"].strip()
            self.history.append({"role": "assistant", "content": reply})
            return reply
        except requests.ConnectionError:
            return (f"My brain isn't online, {config.USER_TITLE}. Install Ollama from ollama.com, "
                    f"then run: ollama pull {config.MODEL}")
        except (requests.RequestException, KeyError, ValueError) as e:
            return f"I hit a problem thinking about that: {e}"
