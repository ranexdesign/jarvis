"""Central configuration. Override with environment variables (see .env.example)."""
import os
from pathlib import Path

WAKE_WORD = os.getenv("JARVIS_WAKE", "jarvis")
LANGUAGE = os.getenv("JARVIS_LANG", "en-IN")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
MODEL = os.getenv("JARVIS_MODEL", "llama3.2:3b")
USER_TITLE = os.getenv("JARVIS_TITLE", "sir")

HOME = Path.home()
NOTES_FILE = HOME / "Documents" / "jarvis_notes.txt"

SYSTEM_PROMPT = (
    "You are JARVIS, a witty, calm, highly capable personal AI assistant running on the "
    f"user's Windows PC. Address the user as '{USER_TITLE}'. Replies are spoken aloud, so keep "
    "them to 1-3 short sentences, no markdown, no lists."
)

APPS = {
    "notepad": "notepad", "calculator": "calc", "paint": "mspaint",
    "command prompt": "cmd", "terminal": "wt", "task manager": "taskmgr",
    "file explorer": "explorer", "explorer": "explorer", "settings": "ms-settings:",
    "chrome": "chrome", "edge": "msedge", "firefox": "firefox",
    "word": "winword", "excel": "excel", "powerpoint": "powerpnt",
    "vs code": "code", "vscode": "code", "visual studio code": "code",
    "spotify": "spotify", "snipping tool": "snippingtool", "camera": "microsoft.windows.camera:",
}
PROCESS_NAMES = {
    "notepad": "notepad.exe", "calculator": "CalculatorApp.exe", "paint": "mspaint.exe",
    "chrome": "chrome.exe", "edge": "msedge.exe", "firefox": "firefox.exe",
    "word": "winword.exe", "excel": "excel.exe", "powerpoint": "powerpnt.exe",
    "vs code": "Code.exe", "vscode": "Code.exe", "spotify": "Spotify.exe",
    "task manager": "Taskmgr.exe",
}
SITES = {
    "youtube": "https://www.youtube.com", "google": "https://www.google.com",
    "gmail": "https://mail.google.com", "github": "https://github.com",
    "chatgpt": "https://chat.openai.com", "whatsapp": "https://web.whatsapp.com",
    "maps": "https://maps.google.com", "linkedin": "https://www.linkedin.com",
    "instagram": "https://www.instagram.com", "twitter": "https://x.com",
}
FOLDERS = {
    "downloads": HOME / "Downloads", "documents": HOME / "Documents",
    "desktop": HOME / "Desktop", "pictures": HOME / "Pictures",
    "music": HOME / "Music", "videos": HOME / "Videos",
}
