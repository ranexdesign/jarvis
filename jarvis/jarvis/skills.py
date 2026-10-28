"""PC-automation skills. Each skill is fn(text, ctx) -> reply string.

ctx provides: say(text), hear() -> str, confirm(question) -> bool.
First matching regex in SKILLS wins; anything unmatched goes to the LLM brain.
"""
import ctypes
import datetime
import os
import re
import subprocess
import time
import webbrowser

import psutil
import requests

from . import config


def _quote(s: str) -> str:
    return requests.utils.quote(s)


def launch(cmd: str):
    if cmd.endswith(":"):
        os.startfile(cmd)
    else:
        subprocess.Popen(f'start "" "{cmd}"', shell=True)


def sk_time(t, ctx):
    now = datetime.datetime.now()
    if "date" in t or "day" in t:
        return now.strftime("Today is %A, %d %B %Y.")
    return now.strftime("It's %I:%M %p.")


def sk_open(t, ctx):
    name = re.sub(r"^(please )?(open|launch|start|run)\s+", "", t).replace("the ", "").strip()
    if name in config.FOLDERS:
        os.startfile(str(config.FOLDERS[name]))
        return f"Opening {name}."
    if name in config.SITES:
        webbrowser.open(config.SITES[name])
        return f"Opening {name}."
    if name in config.APPS:
        launch(config.APPS[name])
        return f"Opening {name}."
    if "." in name and " " not in name:
        webbrowser.open(name if name.startswith("http") else f"https://{name}")
        return f"Opening {name}."
    launch(name)
    return f"Trying to open {name}."


def sk_close(t, ctx):
    name = re.sub(r"^(close|quit|kill|exit)\s+", "", t).replace("the ", "").strip()
    proc = config.PROCESS_NAMES.get(name)
    if not proc:
        return f"I don't know how to close {name} yet."
    subprocess.run(["taskkill", "/IM", proc, "/F"], capture_output=True, check=False)
    return f"Closed {name}."


def sk_search(t, ctx):
    q = re.sub(r"^(search|google|look up)( for)?( on google)?\s*", "", t).strip()
    webbrowser.open("https://www.google.com/search?q=" + _quote(q))
    return f"Searching for {q}."


def sk_youtube(t, ctx):
    q = re.sub(r"\s+on youtube$", "", re.sub(r"^play\s+", "", t)).strip()
    webbrowser.open("https://www.youtube.com/results?search_query=" + _quote(q))
    return f"Playing {q} on YouTube."


def sk_volume(t, ctx):
    import pyautogui
    if "mute" in t:
        pyautogui.press("volumemute")
        return "Toggled mute."
    up = any(w in t for w in ("up", "increase", "raise", "louder"))
    pyautogui.press("volumeup" if up else "volumedown", presses=6)
    return "Volume adjusted."


def sk_screenshot(t, ctx):
    import pyautogui
    folder = config.HOME / "Pictures"
    folder.mkdir(exist_ok=True)
    pyautogui.screenshot(str(folder / f"jarvis_{datetime.datetime.now():%Y%m%d_%H%M%S}.png"))
    return "Screenshot saved to your Pictures folder."


def sk_status(t, ctx):
    msg = (f"CPU is at {psutil.cpu_percent(interval=0.5):.0f} percent and memory at "
           f"{psutil.virtual_memory().percent:.0f} percent.")
    b = psutil.sensors_battery()
    if b:
        msg += f" Battery is {b.percent:.0f} percent{', charging' if b.power_plugged else ''}."
    return msg


def sk_weather(t, ctx):
    m = re.search(r"weather (?:in|at|for) (.+)", t)
    city = m.group(1).strip() if m else ""
    try:
        r = requests.get(f"https://wttr.in/{_quote(city)}?format=%l:+%C,+%t,+wind+%w", timeout=8)
        return r.text.strip()
    except requests.RequestException:
        return "I couldn't reach the weather service."


def sk_note(t, ctx):
    note = re.sub(r"^(take a note|note down|note|remember)( that)?\s*", "", t).strip()
    if not note:
        ctx.say("What should I note?")
        note = ctx.hear()
    if not note:
        return "I didn't catch that."
    config.NOTES_FILE.parent.mkdir(exist_ok=True)
    with open(config.NOTES_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.datetime.now():%Y-%m-%d %H:%M}] {note}\n")
    return "Noted."


def sk_type(t, ctx):
    import pyautogui
    time.sleep(1.5)
    pyautogui.write(re.sub(r"^type\s+", "", t), interval=0.03)
    return "Done."


def sk_lock(t, ctx):
    ctypes.windll.user32.LockWorkStation()
    return "Locking the workstation."


def sk_shutdown(t, ctx):
    restart = "restart" in t or "reboot" in t
    if ctx.confirm(f"Are you sure you want to {'restart' if restart else 'shut down'}?"):
        subprocess.run(["shutdown", "/r" if restart else "/s", "/t", "30"], check=False)
        return "Okay. Say 'cancel shutdown' within 30 seconds to abort."
    return "Cancelled."


def sk_cancel_shutdown(t, ctx):
    subprocess.run(["shutdown", "/a"], check=False)
    return "Shutdown aborted."


def sk_desktop(t, ctx):
    import pyautogui
    pyautogui.hotkey("win", "d")
    return "Showing desktop."


SKILLS = [
    (r"cancel (the )?(shutdown|restart)", sk_cancel_shutdown),
    (r"\b(shut ?down|restart|reboot) (the |my )?(pc|computer|laptop|system)", sk_shutdown),
    (r"\block (the |my )?(pc|computer|screen|laptop)", sk_lock),
    (r"\b(what('s| is) the )?(time|date)\b|what day", sk_time),
    (r"^(please )?(open|launch|start|run) ", sk_open),
    (r"^(close|quit|kill|exit) ", sk_close),
    (r"^(search|google|look up)", sk_search),
    (r"^play .+", sk_youtube),
    (r"\b(volume|mute|louder|quieter)\b", sk_volume),
    (r"screenshot|screen shot|capture (the )?screen", sk_screenshot),
    (r"(system|pc|computer) (status|health|performance)|battery|cpu|ram usage", sk_status),
    (r"\bweather\b", sk_weather),
    (r"^(take a note|note down|note|remember)", sk_note),
    (r"^type ", sk_type),
    (r"(minimi[sz]e all|show (the )?desktop)", sk_desktop),
]


def handle(cmd: str, ctx, brain) -> bool:
    """Run a command. Returns False if JARVIS should quit."""
    if re.search(r"\b(goodbye|go to sleep|shut yourself down|exit jarvis|quit jarvis)\b", cmd):
        ctx.say(f"Goodbye, {config.USER_TITLE}.")
        return False
    if re.search(r"(reset|forget) (our )?(chat|conversation|memory)", cmd):
        brain.clear()
        ctx.say("Memory cleared.")
        return True
    for pattern, fn in SKILLS:
        if re.search(pattern, cmd):
            try:
                ctx.say(fn(cmd, ctx))
            except Exception as e:  # noqa: BLE001 - a failing skill must never kill the assistant
                ctx.say(f"That didn't work: {e}")
            return True
    ctx.say(brain.ask(cmd))
    return True
