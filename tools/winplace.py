#!/usr/bin/env python3
"""Window placement helpers so the tutor can lay windows out to "show" the student things.

Regions: left, right, full, left60, right40, top, bottom, center.
- Our own windows (study browser, exam editor) place themselves from these regions (all platforms;
  on Linux/Wayland they run through XWayland so placement works).
- On Windows the terminal window can be moved too (`arrange_terminal`), via the Win32 API.
"""

import os
import sys

IS_WIN = os.name == "nt"

REGIONS = {
    "left": (0.0, 0.0, 0.5, 1.0), "right": (0.5, 0.0, 0.5, 1.0), "full": (0.0, 0.0, 1.0, 1.0),
    "left60": (0.0, 0.0, 0.6, 1.0), "right40": (0.6, 0.0, 0.4, 1.0),
    "left40": (0.0, 0.0, 0.4, 1.0), "right60": (0.4, 0.0, 0.6, 1.0),
    "top": (0.0, 0.0, 1.0, 0.5), "bottom": (0.0, 0.5, 1.0, 0.5), "center": (0.15, 0.08, 0.7, 0.84),
}


def region_rect(region, work):
    """work = (x, y, w, h) of the usable screen area. Returns (x, y, w, h) in the same units."""
    fx, fy, fw, fh = REGIONS.get(region, REGIONS["center"])
    x, y, w, h = work
    return int(x + fx * w), int(y + fy * h), int(fw * w), int(fh * h)


# ---------------------------------------------------------------- Windows: move other windows

if IS_WIN:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        pass

    def work_area():
        r = wintypes.RECT()
        user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(r), 0)  # SPI_GETWORKAREA
        return r.left, r.top, r.right - r.left, r.bottom - r.top

    def _windows():
        found = []
        proto = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def cb(hwnd, _):
            if user32.IsWindowVisible(hwnd):
                n = user32.GetWindowTextLengthW(hwnd)
                if n:
                    buf = ctypes.create_unicode_buffer(n + 1)
                    user32.GetWindowTextW(hwnd, buf, n + 1)
                    cls = ctypes.create_unicode_buffer(256)
                    user32.GetClassNameW(hwnd, cls, 256)
                    found.append((hwnd, buf.value, cls.value))
            return True

        user32.EnumWindows(proto(cb), 0)
        return found

    def force_foreground(hwnd):
        """Bring a window to the front even from a background process. Windows normally refuses
        (foreground lock); a synthetic Alt tap counts as user input and lifts it."""
        user32.ShowWindow(hwnd, 9)                                   # SW_RESTORE
        user32.keybd_event(0x12, 0, 0, 0)                            # Alt down
        user32.keybd_event(0x12, 0, 2, 0)                            # Alt up
        user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002)   # HWND_TOPMOST, no move/size
        user32.SetWindowPos(hwnd, -2, 0, 0, 0, 0, 0x0001 | 0x0002)   # back to normal z-order
        user32.SetForegroundWindow(hwnd)
        user32.BringWindowToTop(hwnd)

    def place_hwnd(hwnd, region):
        x, y, w, h = region_rect(region, work_area())
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE (un-maximize so it can be sized)
        user32.SetWindowPos(hwnd, 0, x, y, w, h, 0x0040)  # SWP_SHOWWINDOW
        return True

    def find_terminal():
        """The console/terminal window hosting this session (Windows Terminal, conhost, VS Code...)."""
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        wins = _windows()
        # Windows Terminal hosts consoles in a pseudo window; prefer the real top-level terminal window
        for h, title, cls in wins:
            if cls == "CASCADIA_HOSTING_WINDOW_CLASS":
                return h
        for h, title, cls in wins:
            if cls == "ConsoleWindowClass" or "claude" in title.lower():
                return h
        return hwnd or None

    def arrange_terminal(region):
        h = find_terminal()
        if not h:
            return "could not find the terminal window"
        place_hwnd(h, region)
        return f"terminal moved to {region}"

    def place_title(substring, region, foreground=True):
        for h, title, _ in _windows():
            if substring.lower() in title.lower():
                place_hwnd(h, region)
                if foreground:
                    user32.SetForegroundWindow(h)
                return f"'{title}' moved to {region}"
        return f"no window titled like '{substring}'"
else:
    def work_area():
        return None

    def arrange_terminal(region):
        return ("can't move the terminal on Linux (Wayland doesn't let apps move other windows) - "
                "only the study browser and editor are placed")

    def place_title(substring, region, foreground=True):
        return "moving arbitrary windows isn't supported on Linux"


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "terminal":
        print(arrange_terminal(sys.argv[2]))
    else:
        print(__doc__)
