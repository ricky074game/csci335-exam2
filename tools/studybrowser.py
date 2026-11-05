#!/usr/bin/env python3
"""Study browser: a locked-down browser that can ONLY open the study material.

Allowed: this repo's notes (rendered), course material (slides PDFs, homework pages) and the
documentation pages listed in tools/allowlist.json. Everything else is blocked with a notice.
No downloads, no popups, no address-bar escapes.

Usage:  python tools/studybrowser.py [URL | path/to/file]      (normally via `study browse`)
Needs:  pip install PyQt6 PyQt6-WebEngine markdown   (see requirements.txt)
"""

import html
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWLIST = Path(__file__).resolve().parent / "allowlist.json"
CACHE = ROOT / ".focus" / "browser"
CMD_FILE = ROOT / ".focus" / "browser_cmd.json"   # the tutor writes commands here (open/find/place)
PID_FILE = ROOT / ".focus" / "browser.pid"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import winplace  # noqa: E402

try:
    from PyQt6.QtCore import QTimer, QUrl, Qt
    from PyQt6.QtGui import QAction, QKeySequence
    from PyQt6.QtWidgets import QApplication, QLineEdit, QMainWindow, QToolBar
    from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except ImportError as e:  # pragma: no cover
    print(json.dumps({"status": "error", "error": f"PyQt6 WebEngine missing ({e}). Install: "
                      "pip install -r requirements.txt"}))
    sys.exit(2)

from pagestyle import CSS, page  # noqa: E402


import browser_common as bc  # noqa: E402


def load_allowlist():
    return bc.load_allowlist()


def strip_url(qurl):
    return bc.strip(qurl.toString())


class GuardedPage(QWebEnginePage):
    def __init__(self, profile, browser):
        super().__init__(profile, browser)
        self.browser = browser

    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        if self.browser.allowed(url):
            return True
        if not is_main_frame:
            cur = self.url()
            if url.host() and url.host() == cur.host():
                return True  # same-site frames (simulators, embedded viewers)
            return False
        self.browser.show_blocked(url)
        return False

    def createWindow(self, _type):
        return self  # popups/new tabs open in place, still filtered


class Browser(QMainWindow):
    def __init__(self, start, place=None, find=None):
        super().__init__()
        self.data, self.prefixes = load_allowlist()
        self.home = bc.build_home(self.data)
        self.setWindowTitle("Study browser — focus mode")
        self.resize(1200, 900)

        profile = QWebEngineProfile("studycs", self)
        profile.setPersistentStoragePath(str(CACHE / "profile"))
        profile.setCachePath(str(CACHE / "cache"))
        profile.downloadRequested.connect(lambda item: item.cancel())
        self.view = QWebEngineView(self)
        self.view.setPage(GuardedPage(profile, self))
        s = self.view.settings()
        for attr, on in ((QWebEngineSettings.WebAttribute.PluginsEnabled, True),
                         (QWebEngineSettings.WebAttribute.PdfViewerEnabled, True),
                         (QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, False),
                         (QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, False),
                         (QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)):
            s.setAttribute(attr, on)
        self.setCentralWidget(self.view)

        tb = QToolBar("nav", self)
        tb.setMovable(False)
        self.addToolBar(tb)
        for label, fn, key in (("◀", self.view.back, QKeySequence.StandardKey.Back),
                               ("▶", self.view.forward, QKeySequence.StandardKey.Forward),
                               ("⟳", self.view.reload, QKeySequence.StandardKey.Refresh)):
            act = QAction(label, self)
            act.triggered.connect(fn)
            if key is not None:
                act.setShortcut(key)
            tb.addAction(act)
        self.addr = QLineEdit(self)
        self.addr.setReadOnly(True)  # no typing addresses: pages come from the tutor
        tb.addWidget(self.addr)
        for label, d in (("A−", -0.1), ("A+", 0.1)):
            act = QAction(label, self)
            act.triggered.connect(lambda _=False, d=d: self.view.setZoomFactor(max(0.5, self.view.zoomFactor() + d)))
            tb.addAction(act)
        self.find_box = QLineEdit(self)
        self.find_box.setPlaceholderText("Find (Ctrl+F)")
        self.find_box.setMaximumWidth(200)
        self.find_box.returnPressed.connect(lambda: self.view.findText(self.find_box.text()))
        tb.addWidget(self.find_box)
        find_act = QAction(self)
        find_act.setShortcut(QKeySequence.StandardKey.Find)
        find_act.triggered.connect(lambda: (self.find_box.setFocus(), self.find_box.selectAll()))
        self.addAction(find_act)

        self.view.urlChanged.connect(lambda u: self.addr.setText(u.toString()))
        self.view.titleChanged.connect(lambda t: self.setWindowTitle(f"{t} — Study browser"))
        self.pending_find = find
        self.view.loadFinished.connect(self._after_load)
        if place:
            self.place(place)
        self.open(start)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll_commands)
        self.timer.start(400)

    # -------------------------------------------------------------- remote control (from the tutor)
    def place(self, region):
        scr = self.screen().availableGeometry()
        x, y, w, h = winplace.region_rect(region, (scr.x(), scr.y(), scr.width(), scr.height()))
        self.showNormal()
        self.setGeometry(x, y, w, h)

    def bring_to_front(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()
        if os.name == "nt":
            try:
                import ctypes
                ctypes.windll.user32.SetForegroundWindow(int(self.winId()))
            except Exception:
                pass

    def _after_load(self, ok):
        if ok and self.pending_find:
            self.view.findText(self.pending_find)
            self.pending_find = None

    def poll_commands(self):
        if not CMD_FILE.exists():
            return
        try:
            cmd = json.loads(CMD_FILE.read_text(encoding="utf-8"))
            CMD_FILE.unlink()
        except (OSError, ValueError):
            return
        if cmd.get("place"):
            self.place(cmd["place"])
        if cmd.get("find") and not cmd.get("open"):
            self.view.findText(cmd["find"])
        if cmd.get("open") is not None:
            self.pending_find = cmd.get("find")
            self.open(cmd["open"])
        if cmd.get("zoom"):
            self.view.setZoomFactor(float(cmd["zoom"]))
        self.bring_to_front()

    # -------------------------------------------------------------- policy
    def allowed(self, url):
        return bc.allowed(url.toString(), self.prefixes)

    def show_blocked(self, url):
        self.view.setHtml(bc.blocked_html(url.toString(), self.home), QUrl.fromLocalFile(str(CACHE / "blocked.html")))

    # -------------------------------------------------------------- navigation
    def go_home(self):
        self.view.setUrl(QUrl.fromLocalFile(str(self.home)))

    def open(self, target):
        url = QUrl(bc.resolve_target(target, self.home))
        if self.allowed(url):
            self.view.setUrl(url)
        else:
            self.show_blocked(url)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("target", nargs="?", default="")
    ap.add_argument("--place")
    ap.add_argument("--find")
    a = ap.parse_args()
    if sys.platform.startswith("linux") and os.environ.get("WAYLAND_DISPLAY") and "QT_QPA_PLATFORM" not in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "xcb"  # XWayland, so the window can position itself
    app = QApplication(sys.argv[:1])
    app.setApplicationName("Study browser")
    w = Browser(a.target, a.place, a.find)
    w.show()
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))
    code = app.exec()
    try:
        PID_FILE.unlink()
    except OSError:
        pass
    sys.exit(code)


if __name__ == "__main__":
    main()
