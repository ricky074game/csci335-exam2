#!/usr/bin/env python3
"""Study browser for Windows, on Microsoft Edge WebView2 (via pywebview).

Same rules as the Qt version (tools/studybrowser.py): only the notes, course material and the docs
in tools/allowlist.json open; everything else is blocked. Remote-controlled by `study view`.
Ctrl+F find, Ctrl+wheel zoom and Alt+Left/Right back/forward are built into WebView2.
"""

import argparse
import json
import os
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import browser_common as bc  # noqa: E402
import winplace  # noqa: E402

import webview  # noqa: E402  (pywebview)


class StudyBrowser:
    def __init__(self, target, place=None, find=None):
        self.data, self.prefixes = bc.load_allowlist()
        self.home = bc.build_home(self.data)
        self.pending_find = find
        self.place_region = place
        self.hooked = False
        start = bc.resolve_target(target, self.home)
        if not bc.allowed(start, self.prefixes):
            start = bc.file_url(self.home)
        self.win = webview.create_window("Study browser — focus mode", start, width=1200, height=900,
                                         text_select=True)
        self.win.events.loaded += self.on_loaded

    # ------------------------------------------------------------ policy hooks (run on the UI thread)
    def install_guards(self):
        from System import Action, EventHandler
        from Microsoft.Web.WebView2.Core import (CoreWebView2NavigationStartingEventArgs,
                                                 CoreWebView2NewWindowRequestedEventArgs,
                                                 CoreWebView2DownloadStartingEventArgs)

        def do():
            core = self.win.native.browser.webview.CoreWebView2
            core.NavigationStarting += EventHandler[CoreWebView2NavigationStartingEventArgs](self.on_nav)
            core.FrameNavigationStarting += EventHandler[CoreWebView2NavigationStartingEventArgs](self.on_frame_nav)
            core.NewWindowRequested += EventHandler[CoreWebView2NewWindowRequestedEventArgs](self.on_new_window)
            try:
                core.DownloadStarting += EventHandler[CoreWebView2DownloadStartingEventArgs](self.on_download)
            except Exception:
                pass
            self.core = core
        self.win.native.Invoke(Action(do))

    def on_nav(self, sender, e):
        if not bc.allowed(e.Uri, self.prefixes):
            e.Cancel = True
            blocked = bc.blocked_html(e.Uri, self.home)
            threading.Thread(target=lambda: (time.sleep(0.05), self.win.load_html(blocked)), daemon=True).start()

    def on_frame_nav(self, sender, e):
        if bc.allowed(e.Uri, self.prefixes):
            return
        try:
            from urllib.parse import urlsplit
            if urlsplit(e.Uri).netloc and urlsplit(e.Uri).netloc == urlsplit(self.win.get_current_url() or "").netloc:
                return  # same-site frames (simulators)
        except Exception:
            pass
        e.Cancel = True

    def on_new_window(self, sender, e):
        e.Handled = True  # no popups / new windows; open in place if allowed
        uri = e.Uri
        if bc.allowed(uri, self.prefixes):
            threading.Thread(target=lambda: self.win.load_url(uri), daemon=True).start()

    def on_download(self, sender, e):
        e.Cancel = True

    # ------------------------------------------------------------ page events
    def on_loaded(self):
        if not self.hooked:
            self.hooked = True
            try:
                self.install_guards()
            except Exception as ex:  # never run unguarded
                print(json.dumps({"status": "error", "error": f"could not install guards: {ex}"}), flush=True)
                self.win.destroy()
                return
            if self.place_region:
                self.place(self.place_region)
            self.bring_to_front()
            threading.Thread(target=self.poll_commands, daemon=True).start()
        try:
            if self.pending_find:
                text = json.dumps(self.pending_find)
                self.win.evaluate_js(f"setTimeout(function(){{window.find({text}, false, false, true);}}, 300)")
                self.pending_find = None
        except Exception:
            pass

    # ------------------------------------------------------------ remote control
    def place(self, region):
        try:
            x, y, w, h = winplace.region_rect(region, winplace.work_area())
            self.win.restore()
            self.win.move(x, y)
            self.win.resize(w, h)
        except Exception:
            pass

    def bring_to_front(self):
        try:
            self.win.restore()
            self.win.show()
            from System import Action

            def do():
                self.win.native.Activate()
                winplace.force_foreground(int(self.win.native.Handle.ToInt64()))
            self.win.native.Invoke(Action(do))
        except Exception:
            pass

    def poll_commands(self):
        while True:
            time.sleep(0.4)
            if not bc.CMD_FILE.exists():
                continue
            try:
                cmd = json.loads(bc.CMD_FILE.read_text(encoding="utf-8"))
                bc.CMD_FILE.unlink()
            except (OSError, ValueError):
                continue
            if cmd.get("place"):
                self.place(cmd["place"])
            if cmd.get("open") is not None:
                url = bc.resolve_target(cmd["open"], self.home)
                self.pending_find = cmd.get("find")
                if bc.allowed(url, self.prefixes):
                    self.win.load_url(url)
                else:
                    self.win.load_html(bc.blocked_html(url, self.home))
            elif cmd.get("find"):
                self.win.evaluate_js(f"window.find({json.dumps(cmd['find'])}, false, false, true)")
            self.bring_to_front()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", nargs="?", default="")
    ap.add_argument("--place")
    ap.add_argument("--find")
    a = ap.parse_args()
    StudyBrowser(a.target, a.place, a.find)
    bc.PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    bc.PID_FILE.write_text(str(os.getpid()))
    try:
        webview.start(gui="edgechromium", storage_path=str(bc.CACHE / "wv2profile"), private_mode=False)
    finally:
        try:
            bc.PID_FILE.unlink()
        except OSError:
            pass


if __name__ == "__main__":
    main()
