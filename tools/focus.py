#!/usr/bin/env python3
"""Focus mode: while a study session runs, keep distracting apps (browsers, Discord, games, ...)
closed. Blocked apps are closed gently first (so browsers restore their tabs later), then forced.

Controlled through study.py:
    study focus start --minutes 90     start (or extend) focus mode
    study focus status                 is it on, time left, what was blocked
    study focus stop "reason"          early stop: waits out a cooldown first (Ctrl+C cancels)
    study focus end                    normal end of a study session (used by /save)

The watchdog is this file run as `focus.py watch`; it exits by itself when the time is up.
State lives in .focus/ (local to this machine, not synced).
"""

import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = Path(__file__).resolve().parent / "focus_config.json"
STATE_DIR = ROOT / ".focus"
STATE = STATE_DIR / "state.json"
LOG = STATE_DIR / "focus.log"
IS_WIN = os.name == "nt"
IS_MAC = sys.platform == "darwin"
OS_KEY = "windows" if IS_WIN else ("mac" if IS_MAC else "linux")
LOCAL = STATE_DIR / "focus_local.json"   # per-machine choices: categories, extra apps, allowed apps
NEVER_KILL = {"python", "python.exe", "pythonw.exe", "python3", "claude", "claude.exe", "node", "node.exe",
              "explorer.exe", "windowsterminal.exe", "powershell.exe", "pwsh.exe", "cmd.exe", "bash", "bash.exe",
              "conhost.exe", "openconsole.exe", "qtwebengineprocess.exe", "qtwebengineprocess", "gnome-shell",
              "gnome-terminal-server", "konsole", "xterm", "code", "code.exe", "systemd", "init", "sshd"}


def load_config():
    with open(CONFIG, encoding="utf-8") as f:
        return json.load(f)


def load_local():
    try:
        with open(LOCAL, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        d = {}
    d.setdefault("enabled", False)  # opt-in per machine (/setup asks)
    d.setdefault("categories", None)   # None = config default_categories
    d.setdefault("extra", [])          # extra process names to block
    d.setdefault("allow", [])          # process names never to block (e.g. a browser needed for class)
    return d


def save_local(d):
    STATE_DIR.mkdir(exist_ok=True)
    with open(LOCAL, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)


def blocked_names(cfg=None, local=None):
    cfg = cfg or load_config()
    local = local or load_local()
    groups = cfg["block"].get(OS_KEY, {})
    cats = local["categories"] or cfg.get("default_categories") or list(groups)
    names = {n for c in cats for n in groups.get(c, [])} | set(local["extra"])
    allow = {a.lower() for a in local["allow"]}
    return {n for n in names if n.lower() not in NEVER_KILL and n.lower() not in allow}


def configure(action, value=None):
    """study focus config [show | categories a,b | add NAME | allow NAME | unallow NAME | remove NAME | on | off]."""
    cfg, local = load_config(), load_local()
    groups = cfg["block"].get(OS_KEY, {})
    if action == "categories":
        cats = [c.strip() for c in (value or "").split(",") if c.strip()]
        bad = [c for c in cats if c not in groups]
        if bad:
            return f"unknown categories {bad}; choose from {', '.join(groups)}"
        local["categories"] = cats
    elif action == "add" and value:
        local["extra"] = sorted(set(local["extra"]) | {value})
    elif action == "remove" and value:
        local["extra"] = [x for x in local["extra"] if x.lower() != value.lower()]
        if value.lower() not in {x.lower() for x in local["allow"]}:
            local["allow"].append(value)
    elif action == "allow" and value:
        local["allow"] = sorted(set(local["allow"]) | {value})
    elif action == "unallow" and value:
        local["allow"] = [x for x in local["allow"] if x.lower() != value.lower()]
    elif action in ("on", "off"):
        local["enabled"] = action == "on"
    if action != "show":
        save_local(local)
    cats = local["categories"] or cfg.get("default_categories") or list(groups)
    lines = [f"focus mode: {'ENABLED' if local['enabled'] else 'disabled (study focus config on)'} ({OS_KEY})",
             f"categories blocked: {', '.join(cats)}   (all: {', '.join(groups)})",
             f"extra apps: {', '.join(local['extra']) or '-'}",
             f"never blocked: {', '.join(local['allow']) or '-'}",
             f"{len(blocked_names(cfg, local))} process names blocked in total"]
    return "\n".join(lines)


def read_state():
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def write_state(st):
    STATE_DIR.mkdir(exist_ok=True)
    tmp = STATE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=2)
    tmp.replace(STATE)


def log(msg):
    STATE_DIR.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}\n")


def pid_alive(pid):
    if not pid:
        return False
    if IS_WIN:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                             capture_output=True, text=True, creationflags=0x08000000).stdout
        return f'"{pid}"' in out
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


# ---------------------------------------------------------------- process scanning / closing

def running_blocked(names):
    """Return {name: [pids]} of blocked processes currently running."""
    found = {}
    lower = {n.lower(): n for n in names}
    if IS_WIN:
        out = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True,
                             creationflags=0x08000000).stdout
        for line in out.splitlines():
            parts = [p.strip('"') for p in line.split('","')]
            if len(parts) >= 2 and parts[0].lower() in lower:
                try:
                    found.setdefault(lower[parts[0].lower()], []).append(int(parts[1]))
                except ValueError:
                    pass
    elif IS_MAC:
        out = subprocess.run(["ps", "-axco", "pid=,comm=", "-U", str(os.getuid())], capture_output=True, text=True).stdout
        for line in out.splitlines():
            parts = line.strip().split(None, 1)
            if len(parts) == 2 and parts[1].strip().lower() in lower:
                try:
                    found.setdefault(lower[parts[1].strip().lower()], []).append(int(parts[0]))
                except ValueError:
                    pass
    else:
        me = os.getuid()
        for d in Path("/proc").iterdir():
            if not d.name.isdigit():
                continue
            try:
                if d.stat().st_uid != me:
                    continue
                comm = (d / "comm").read_text().strip()
                exe = os.path.basename(os.readlink(d / "exe")) if (d / "exe").exists() else ""
            except OSError:
                continue
            for cand in (comm, exe):
                if cand.lower() in lower:
                    found.setdefault(lower[cand.lower()], []).append(int(d.name))
                    break
    return found


def close_processes(name, pids):
    """Gentle close, then force after a few seconds."""
    if IS_WIN:
        subprocess.run(["taskkill", "/IM", name], capture_output=True, creationflags=0x08000000)
        time.sleep(2.5)
        if running_blocked({name}):
            subprocess.run(["taskkill", "/F", "/T", "/IM", name], capture_output=True, creationflags=0x08000000)
    else:
        for pid in pids:
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
        time.sleep(2.5)
        for pid in running_blocked({name}).get(name, []):
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass


# ---------------------------------------------------------------- watchdog

def watch():
    cfg = load_config()
    names = blocked_names(cfg)
    every = float(cfg.get("check_every_seconds", 2))
    log(f"watchdog started pid {os.getpid()}, blocking {len(names)} process names")
    while True:
        st = read_state()
        if not st or st.get("watchdog_pid") != os.getpid():
            log("state removed or taken over - watchdog exiting")
            return
        if datetime.now() >= datetime.fromisoformat(st["until"]):
            st["active"] = False
            st["ended"] = datetime.now().isoformat(timespec="seconds")
            st["end_reason"] = "time up"
            write_state(st)
            log("time up - focus mode off")
            return
        for name, pids in running_blocked(names).items():
            close_processes(name, pids)
            st = read_state() or st
            st.setdefault("blocked", {})
            st["blocked"][name] = st["blocked"].get(name, 0) + 1
            write_state(st)
            log(f"closed {name} (pids {pids})")
        time.sleep(every)


# ---------------------------------------------------------------- control (called from study.py)

def status_text():
    st = read_state()
    if not st or not st.get("active"):
        last = ""
        if st and st.get("ended"):
            last = f" (last session ended {st['ended'][:16]}: {st.get('end_reason', '')})"
        return "focus mode: OFF" + last
    until = datetime.fromisoformat(st["until"])
    left = max(0, int((until - datetime.now()).total_seconds() // 60))
    alive = pid_alive(st.get("watchdog_pid"))
    blocked = st.get("blocked", {})
    btxt = ", ".join(f"{k} x{v}" for k, v in blocked.items()) or "nothing yet"
    warn = "" if alive else "  (WARNING: watchdog not running - run `study focus start` again)"
    return f"focus mode: ON until {until:%H:%M} ({left} min left). Closed: {btxt}{warn}"


def start(minutes):
    if not load_local()["enabled"]:
        return "focus mode is disabled on this machine (turn it on with `study focus config on`)"
    st = read_state()
    until = datetime.now() + timedelta(minutes=minutes)
    if st and st.get("active") and pid_alive(st.get("watchdog_pid")):
        st["until"] = max(datetime.fromisoformat(st["until"]), until).isoformat(timespec="seconds")
        write_state(st)
        return f"focus mode already on - extended until {datetime.fromisoformat(st['until']):%H:%M}"
    st = {"active": True, "started": datetime.now().isoformat(timespec="seconds"),
          "until": until.isoformat(timespec="seconds"), "blocked": {}, "watchdog_pid": None}
    write_state(st)
    exe = sys.executable
    kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL, "stdin": subprocess.DEVNULL}
    if IS_WIN:
        pyw = Path(exe).with_name("pythonw.exe")
        if pyw.exists():
            exe = str(pyw)
        kwargs["creationflags"] = 0x00000008 | 0x00000200 | 0x08000000  # DETACHED | NEW_GROUP | NO_WINDOW
    else:
        kwargs["start_new_session"] = True
    proc = subprocess.Popen([exe, str(Path(__file__).resolve()), "watch"], **kwargs)
    st["watchdog_pid"] = proc.pid
    write_state(st)
    names = sorted(blocked_names())
    return (f"focus mode ON until {until:%H:%M} ({minutes} min). Keeping closed: " + ", ".join(names) +
            "\nLinks open in the study browser (`study browse`).")


def _finish(reason):
    st = read_state()
    if not st or not st.get("active"):
        return "focus mode was already off"
    pid = st.get("watchdog_pid")
    st.update({"active": False, "ended": datetime.now().isoformat(timespec="seconds"), "end_reason": reason,
               "watchdog_pid": None})
    write_state(st)  # the watchdog sees the pid change and exits on its own
    if pid and pid_alive(pid):
        try:
            if IS_WIN:
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, creationflags=0x08000000)
            else:
                os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    blocked = st.get("blocked", {})
    summary = ", ".join(f"{k} x{v}" for k, v in blocked.items()) or "nothing"
    log(f"focus mode off: {reason}")
    return f"focus mode OFF ({reason}). Closed during the session: {summary}"


def end():
    return _finish("session ended")


def stop(reason, cooldown=None):
    st = read_state()
    if not st or not st.get("active"):
        return "focus mode is not on"
    if not reason or len(reason.strip()) < 8:
        return "To stop focus mode early, give a real reason, e.g.  study focus stop \"need to email my professor\""
    secs = int(cooldown if cooldown is not None else load_config().get("stop_cooldown_seconds", 120))
    print(f"Stopping focus mode early: \"{reason}\"")
    print(f"Cooldown: {secs // 60} min {secs % 60} s. Still want it after that? (Ctrl+C to cancel and keep focusing)",
          flush=True)
    try:
        for left in range(secs, 0, -15):
            print(f"  {left} s...", flush=True)
            time.sleep(min(15, left))
    except KeyboardInterrupt:
        return "cancelled - focus mode stays ON. Good call."
    log(f"early stop reason: {reason}")
    return _finish(f"stopped early: {reason}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "watch":
        watch()
    else:
        print(__doc__)
