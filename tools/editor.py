#!/usr/bin/env python3
"""Minimal exam editor: question on top, your answer below. No autocomplete, no IntelliSense.

Only the essentials, each one switchable (toolbar checkboxes, saved in progress/editor_settings.json):
  * Tab / Shift+Tab indent and dedent (whole selection too); Backspace removes a whole indent level
  * Auto-indent on Enter (extra level after '{'; '{|}' + Enter puts '}' on its own line)
  * Auto-close brackets/quotes: { ( [ " '  (typing the closer just steps over it)
  * Optional plain syntax colouring (off by default), line numbers
  * Exam mode: turns off auto-close, auto-indent and colouring (Tab still works) - closest to paper
  * Timer: countdown if --minutes is given, otherwise elapsed time
  * Autosave every few seconds; Ctrl+S save; Ctrl+Enter or "Submit" saves and closes

Usage: python tools/editor.py FILE [--minutes N] [--title TEXT]
On exit prints one JSON line: {"status": "submitted"|"closed", "seconds": N, "file": "..."}

The file keeps the question above a marker line; only the text below the marker is edited:
  .cpp:  // ===== YOUR ANSWER =====      other:  <!-- ===== YOUR ANSWER ===== -->
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import font as tkfont
except ImportError:  # pragma: no cover
    print(json.dumps({"status": "error", "error": "tkinter is not installed. On Debian/Ubuntu: "
                      "sudo apt install python3-tk ; Fedora: sudo dnf install python3-tkinter"}))
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
SETTINGS = ROOT / "progress" / "editor_settings.json"
MARKERS = ("===== YOUR ANSWER =====",)
DEFAULTS = {
    "auto_close": True, "auto_indent": True, "highlight": False, "line_numbers": True,
    "exam_mode": False, "tab_width": 4, "font_size": 13, "theme": "dark",
}
THEMES = {
    "dark": {"bg": "#1e1f22", "fg": "#d6d6d6", "q_bg": "#26282c", "q_fg": "#e8e8e8", "gutter": "#26282c",
             "gutter_fg": "#6b6f76", "cursor": "#ffffff", "sel": "#264f78", "bar": "#2b2d31", "bar_fg": "#d6d6d6",
             "kw": "#cc7832", "type": "#6fa8dc", "str": "#6a8759", "com": "#7f848e", "num": "#b5cea8",
             "pre": "#bbb529", "warn": "#ff6b6b", "ok": "#7bd88f"},
    "light": {"bg": "#ffffff", "fg": "#1f1f1f", "q_bg": "#f4f4f2", "q_fg": "#1f1f1f", "gutter": "#f0f0f0",
              "gutter_fg": "#9a9a9a", "cursor": "#000000", "sel": "#cce0ff", "bar": "#e9e9e7", "bar_fg": "#1f1f1f",
              "kw": "#0033b3", "type": "#00627a", "str": "#067d17", "com": "#8c8c8c", "num": "#1750eb",
              "pre": "#9e880d", "warn": "#c62828", "ok": "#2e7d32"},
}
KEYWORDS = ("if else for while do return break continue switch case default new delete class struct public "
            "private protected const static virtual override template typename using namespace this nullptr "
            "true false operator friend try catch throw noexcept explicit inline sizeof").split()
TYPES = ("int void bool char double float long short unsigned auto size_t std string vector list set map "
         "iterator const_iterator reverse_iterator").split()
PAIRS = {"{": "}", "(": ")", "[": "]", '"': '"', "'": "'"}


def load_settings():
    s = dict(DEFAULTS)
    try:
        s.update(json.loads(SETTINGS.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return s


def save_settings(s):
    try:
        SETTINGS.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS.write_text(json.dumps(s, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError:
        pass


def split_file(text):
    """Return (header, marker_line, answer)."""
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        if any(m in ln for m in MARKERS):
            answer = "\n".join(lines[i + 1:])
            return "\n".join(lines[:i]), ln, answer.lstrip("\n")
    return "", None, text


def header_to_question(header):
    out = []
    for ln in header.split("\n"):
        s = ln
        if s.strip() in ("/*", "*/"):
            continue
        s = re.sub(r"^ \* ?", "", s)
        s = re.sub(r"^ \*/$", "", s)
        s = re.sub(r"^> ?", "", s)
        out.append(s)
    return "\n".join(out).strip("\n")


def pick_mono(size):
    fams = set(tkfont.families())
    for f in ("Consolas", "Cascadia Mono", "JetBrains Mono", "DejaVu Sans Mono", "Ubuntu Mono",
              "Liberation Mono", "Menlo", "Courier New"):
        if f in fams:
            return (f, size)
    return ("TkFixedFont", size)


class Editor:
    def __init__(self, path, minutes=None, title=None):
        self.path = Path(path)
        self.minutes = minutes
        self.cfg = load_settings()
        self.start = time.time()
        self.status = "closed"
        raw = self.path.read_text(encoding="utf-8") if self.path.exists() else ""
        self.header, self.marker, answer = split_file(raw)
        if self.marker is None:
            self.marker = "// ===== YOUR ANSWER =====" if self.path.suffix == ".cpp" else "<!-- ===== YOUR ANSWER ===== -->"
        self.saved_text = answer
        self.dirty = False

        self.root = tk.Tk()
        self.root.title(title or f"Exam editor — {self.path.name}")
        self.root.geometry("1100x860")
        self.font = tkfont.Font(family=pick_mono(self.cfg["font_size"])[0], size=self.cfg["font_size"])
        self.qfont = tkfont.Font(family=self.font.actual("family"), size=max(9, self.cfg["font_size"] - 1))
        self._build(answer)
        self.apply_theme()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.tick()
        self.autosave()
        self.text.focus_set()
        self.text.mark_set("insert", "end-1c")

    # ------------------------------------------------------------ layout
    def _build(self, answer):
        r = self.root
        bar = tk.Frame(r, padx=6, pady=4)
        bar.pack(side="top", fill="x")
        self.bar = bar
        self.timer = tk.Label(bar, text="", font=(self.font.actual("family"), 12, "bold"), padx=8)
        self.timer.pack(side="left")
        self.vars = {}
        for key, label in (("exam_mode", "Exam mode"), ("auto_close", "Auto-close { ( ["),
                           ("auto_indent", "Auto-indent"), ("highlight", "Colours"),
                           ("line_numbers", "Line numbers")):
            v = tk.BooleanVar(value=self.cfg[key])
            cb = tk.Checkbutton(bar, text=label, variable=v, command=lambda k=key: self.toggle(k))
            cb.pack(side="left", padx=4)
            self.vars[key] = v
        self.checkbuttons = [w for w in bar.winfo_children() if isinstance(w, tk.Checkbutton)]
        self.submit_btn = tk.Button(bar, text="Submit  (Ctrl+Enter)", command=self.submit, padx=10)
        self.submit_btn.pack(side="right", padx=4)
        self.save_btn = tk.Button(bar, text="Save (Ctrl+S)", command=self.save, padx=6)
        self.save_btn.pack(side="right", padx=4)
        self.theme_btn = tk.Button(bar, text="Light/Dark", command=self.flip_theme, padx=6)
        self.theme_btn.pack(side="right", padx=4)
        self.saved_lbl = tk.Label(bar, text="")
        self.saved_lbl.pack(side="right", padx=8)

        pw = tk.PanedWindow(r, orient="vertical", sashwidth=6, sashrelief="flat")
        pw.pack(fill="both", expand=True)
        self.pw = pw

        qf = tk.Frame(pw)
        self.q = tk.Text(qf, wrap="word", font=self.qfont, padx=12, pady=10, relief="flat",
                         borderwidth=0, height=14)
        qs = tk.Scrollbar(qf, command=self.q.yview)
        self.q.configure(yscrollcommand=qs.set)
        qs.pack(side="right", fill="y")
        self.q.pack(side="left", fill="both", expand=True)
        self.q.insert("1.0", header_to_question(self.header) or "(no question text)")
        self.q.configure(state="disabled")
        pw.add(qf, minsize=80, height=300)

        ef = tk.Frame(pw)
        self.gutter = tk.Canvas(ef, width=44, highlightthickness=0, borderwidth=0)
        # prose answers (.md) wrap like a notebook; code keeps long lines unwrapped
        self.text = tk.Text(ef, wrap="none" if self.path.suffix == ".cpp" else "word", undo=True, autoseparators=True, maxundo=-1, font=self.font,
                            padx=8, pady=8, relief="flat", borderwidth=0, tabs=(self.font.measure(" " * 4),))
        vs = tk.Scrollbar(ef, command=self._yview)
        hs = tk.Scrollbar(ef, orient="horizontal", command=self.text.xview)
        self.text.configure(yscrollcommand=lambda a, b: (vs.set(a, b), self.draw_gutter()),
                            xscrollcommand=hs.set)
        vs.pack(side="right", fill="y")
        hs.pack(side="bottom", fill="x")
        self.gutter.pack(side="left", fill="y")
        self.text.pack(side="left", fill="both", expand=True)
        pw.add(ef, minsize=120)
        self.text.insert("1.0", answer)
        self.text.edit_reset()
        self.text.edit_modified(False)
        self.update_gutter_visibility()

        t = self.text
        t.bind("<Tab>", self.on_tab)
        t.bind("<Shift-Tab>", self.on_shift_tab)
        t.bind("<ISO_Left_Tab>", self.on_shift_tab)
        t.bind("<Return>", self.on_return)
        t.bind("<BackSpace>", self.on_backspace)
        for ch in "{([\"'":
            t.bind(ch if ch not in "\"'" else ("<quotedbl>" if ch == '"' else "<apostrophe>"),
                   lambda e, c=ch: self.on_open(c))
        for ch, ks in (("}", "<braceright>"), (")", "<parenright>"), ("]", "<bracketright>")):
            t.bind(ks, lambda e, c=ch: self.on_close_char(c))
        t.bind("<<Modified>>", self.on_modified)
        t.bind("<Configure>", lambda e: self.draw_gutter())
        t.bind("<KeyRelease>", lambda e: self.draw_gutter())
        for seq in ("<Control-s>", "<Control-S>"):
            r.bind(seq, lambda e: (self.save(), "break")[1])
        r.bind("<Control-Return>", lambda e: (self.submit(), "break")[1])
        t.bind("<Control-Return>", lambda e: (self.submit(), "break")[1])
        t.bind("<Control-y>", lambda e: (self._redo(), "break")[1])
        t.bind("<Control-Z>", lambda e: (self._redo(), "break")[1])
        t.bind("<Control-slash>", self.toggle_comment)
        t.bind("<Control-a>", lambda e: (t.tag_add("sel", "1.0", "end-1c"), "break")[1])
        for seq, d in (("<Control-equal>", 1), ("<Control-plus>", 1), ("<Control-minus>", -1)):
            r.bind(seq, lambda e, d=d: self.zoom(d))
        r.bind("<Control-MouseWheel>", lambda e: self.zoom(1 if e.delta > 0 else -1))

    # ------------------------------------------------------------ settings / theme
    def feature(self, key):
        if self.cfg.get("exam_mode") and key in ("auto_close", "auto_indent", "highlight"):
            return False
        return self.cfg.get(key)

    def toggle(self, key):
        self.cfg[key] = bool(self.vars[key].get())
        save_settings(self.cfg)
        self.update_gutter_visibility()
        self.highlight()

    def flip_theme(self):
        self.cfg["theme"] = "light" if self.cfg.get("theme") == "dark" else "dark"
        save_settings(self.cfg)
        self.apply_theme()

    def zoom(self, d):
        size = max(8, min(32, self.cfg["font_size"] + d))
        self.cfg["font_size"] = size
        self.font.configure(size=size)
        self.qfont.configure(size=max(9, size - 1))
        self.text.configure(tabs=(self.font.measure(" " * 4),))
        save_settings(self.cfg)
        self.draw_gutter()
        return "break"

    def apply_theme(self):
        th = THEMES.get(self.cfg.get("theme"), THEMES["dark"])
        self.th = th
        self.text.configure(bg=th["bg"], fg=th["fg"], insertbackground=th["cursor"], selectbackground=th["sel"],
                            insertwidth=2)
        self.q.configure(bg=th["q_bg"], fg=th["q_fg"], selectbackground=th["sel"])
        self.gutter.configure(bg=th["gutter"])
        for w in [self.bar] + list(self.bar.winfo_children()):
            try:
                w.configure(bg=th["bar"], fg=th["bar_fg"])
            except tk.TclError:
                w.configure(bg=th["bar"])
        for cb in self.checkbuttons:
            cb.configure(selectcolor=th["bg"], activebackground=th["bar"], activeforeground=th["bar_fg"])
        self.pw.configure(bg=th["bar"])
        for tag in ("kw", "type", "str", "com", "num", "pre"):
            self.text.tag_configure(tag, foreground=th[tag])
        self.highlight()
        self.draw_gutter()

    def update_gutter_visibility(self):
        if self.cfg.get("line_numbers"):
            self.gutter.pack(side="left", fill="y", before=self.text)
        else:
            self.gutter.pack_forget()
        self.draw_gutter()

    # ------------------------------------------------------------ gutter
    def _yview(self, *a):
        self.text.yview(*a)
        self.draw_gutter()

    def draw_gutter(self):
        if not self.cfg.get("line_numbers"):
            return
        g = self.gutter
        g.delete("all")
        last = int(self.text.index("end-1c").split(".")[0])
        width = self.font.measure("0" * max(2, len(str(last)))) + 16
        g.configure(width=width)
        idx = self.text.index("@0,0")
        while True:
            info = self.text.dlineinfo(idx)
            if info is None:
                break
            line = idx.split(".")[0]
            g.create_text(width - 6, info[1] + 8, anchor="ne", text=line, font=self.font,
                          fill=self.th["gutter_fg"] if hasattr(self, "th") else "#888")
            nxt = self.text.index(f"{idx}+1line")
            if nxt == idx:
                break
            idx = nxt

    # ------------------------------------------------------------ editing helpers
    def tab(self):
        return " " * int(self.cfg.get("tab_width", 4))

    def sel_lines(self):
        try:
            a, b = self.text.index("sel.first"), self.text.index("sel.last")
        except tk.TclError:
            return None
        la, lb = int(a.split(".")[0]), int(b.split(".")[0])
        if b.endswith(".0") and lb > la:
            lb -= 1
        return la, lb

    def on_tab(self, e):
        lines = self.sel_lines()
        if lines and lines[0] != lines[1]:
            self.text.edit_separator()
            for ln in range(lines[0], lines[1] + 1):
                self.text.insert(f"{ln}.0", self.tab())
            self.text.tag_add("sel", f"{lines[0]}.0", f"{lines[1]}.end")
            return "break"
        col = int(self.text.index("insert").split(".")[1])
        w = int(self.cfg.get("tab_width", 4))
        if lines:
            self.text.delete("sel.first", "sel.last")
        self.text.insert("insert", " " * (w - col % w))
        return "break"

    def on_shift_tab(self, e):
        lines = self.sel_lines() or (int(self.text.index("insert").split(".")[0]),) * 2
        w = int(self.cfg.get("tab_width", 4))
        self.text.edit_separator()
        for ln in range(lines[0], lines[1] + 1):
            lead = re.match(r"[ ]*", self.text.get(f"{ln}.0", f"{ln}.end")).group()
            n = min(len(lead), w) if lead else (1 if self.text.get(f"{ln}.0") == "\t" else 0)
            if n:
                self.text.delete(f"{ln}.0", f"{ln}.{n}")
        return "break"

    def on_return(self, e):
        if e.state & 0x4:  # Ctrl+Enter handled elsewhere
            return "break"
        if not self.feature("auto_indent"):
            return None
        t = self.text
        before = t.get("insert linestart", "insert")
        after = t.get("insert", "insert lineend")
        indent = re.match(r"[ \t]*", before).group()
        stripped = before.rstrip()
        extra = self.tab() if stripped.endswith("{") else ""
        t.edit_separator()
        if stripped.endswith("{") and after.lstrip().startswith("}"):
            t.delete("insert", f"insert+{len(after) - len(after.lstrip())}c")
            t.insert("insert", "\n" + indent + extra)
            pos = t.index("insert")
            t.insert("insert", "\n" + indent)
            t.mark_set("insert", pos)
        else:
            t.insert("insert", "\n" + indent + extra)
        t.see("insert")
        return "break"

    def on_open(self, c):
        if not self.feature("auto_close"):
            return None
        t = self.text
        nxt = t.get("insert")
        prev = t.get("insert-1c") if t.index("insert") != "1.0" else ""
        if c in "\"'":
            if nxt == c:  # step over the closing quote
                t.mark_set("insert", "insert+1c")
                return "break"
            if prev.isalnum() or prev == "\\":
                return None
        if self.sel_lines() is not None and c in "{([":
            return None
        if nxt and not (nxt.isspace() or nxt in ")]};,"):
            return None
        t.edit_separator()
        t.insert("insert", c + PAIRS[c])
        t.mark_set("insert", "insert-1c")
        return "break"

    def on_close_char(self, c):
        t = self.text
        if self.feature("auto_close") and t.get("insert") == c:
            t.mark_set("insert", "insert+1c")
            return "break"
        if c == "}" and self.feature("auto_indent"):
            before = t.get("insert linestart", "insert")
            if before and not before.strip():
                w = int(self.cfg.get("tab_width", 4))
                n = min(len(before), w)
                t.delete(f"insert-{n}c", "insert")
        return None

    def on_backspace(self, e):
        t = self.text
        if self.sel_lines() is not None or t.index("insert") == "1.0":
            return None
        prev, nxt = t.get("insert-1c"), t.get("insert")
        if self.feature("auto_close") and PAIRS.get(prev) == nxt and prev in PAIRS:
            t.delete("insert-1c", "insert+1c")
            return "break"
        before = t.get("insert linestart", "insert")
        if before and not before.strip(" "):
            w = int(self.cfg.get("tab_width", 4))
            n = (len(before) - 1) % w + 1
            t.delete(f"insert-{n}c", "insert")
            return "break"
        return None

    def toggle_comment(self, e=None):
        lines = self.sel_lines() or (int(self.text.index("insert").split(".")[0]),) * 2
        texts = [self.text.get(f"{ln}.0", f"{ln}.end") for ln in range(lines[0], lines[1] + 1)]
        uncomment = all(s.lstrip().startswith("//") or not s.strip() for s in texts)
        self.text.edit_separator()
        for ln, s in zip(range(lines[0], lines[1] + 1), texts):
            if not s.strip():
                continue
            lead = len(s) - len(s.lstrip())
            if uncomment:
                cut = 3 if s.lstrip().startswith("// ") else 2
                self.text.delete(f"{ln}.{lead}", f"{ln}.{lead + cut}")
            else:
                self.text.insert(f"{ln}.{lead}", "// ")
        return "break"

    def _redo(self):
        try:
            self.text.edit_redo()
        except tk.TclError:
            pass

    # ------------------------------------------------------------ highlighting
    def on_modified(self, e=None):
        if self.text.edit_modified():
            self.dirty = True
            self.text.edit_modified(False)
            self.saved_lbl.configure(text="● unsaved")
            if hasattr(self, "_hl_job"):
                self.root.after_cancel(self._hl_job)
            self._hl_job = self.root.after(200, self.highlight)
            self.draw_gutter()

    def highlight(self):
        t = self.text
        for tag in ("kw", "type", "str", "com", "num", "pre"):
            t.tag_remove(tag, "1.0", "end")
        if not self.feature("highlight"):
            return
        src = t.get("1.0", "end-1c")
        spans = []
        token = re.compile(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'|^[ \t]*#[^\n]*|'
                           r'\b\d+(?:\.\d+)?\b|\b[A-Za-z_]\w*\b', re.S | re.M)
        kw, ty = set(KEYWORDS), set(TYPES)
        for m in token.finditer(src):
            s = m.group()
            if s.startswith("//") or s.startswith("/*"):
                tag = "com"
            elif s[0] in "\"'":
                tag = "str"
            elif s.lstrip().startswith("#"):
                tag = "pre"
            elif s[0].isdigit():
                tag = "num"
            elif s in kw:
                tag = "kw"
            elif s in ty:
                tag = "type"
            else:
                continue
            spans.append((tag, m.start(), m.end()))
        for tag, a, b in spans:
            t.tag_add(tag, f"1.0+{a}c", f"1.0+{b}c")

    # ------------------------------------------------------------ timer / saving
    def tick(self):
        el = int(time.time() - self.start)
        if self.minutes:
            left = int(self.minutes * 60) - el
            sign = "-" if left < 0 else ""
            m, s = divmod(abs(left), 60)
            txt = f"{sign}{m:02d}:{s:02d} left" if left >= 0 else f"TIME UP  {sign}{m:02d}:{s:02d}"
            color = self.th["warn"] if left < 0 or left < 60 * min(5, self.minutes / 5) else self.th["bar_fg"]
        else:
            m, s = divmod(el, 60)
            txt, color = f"{m:02d}:{s:02d}", self.th["bar_fg"]
        self.timer.configure(text=txt, fg=color)
        self.root.after(1000, self.tick)

    def answer_text(self):
        return self.text.get("1.0", "end-1c")

    def save(self):
        body = self.answer_text()
        content = (self.header + "\n" if self.header else "") + self.marker + "\n" + body
        if not content.endswith("\n"):
            content += "\n"
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(content, encoding="utf-8", newline="\n")
        tmp.replace(self.path)
        self.dirty = False
        self.saved_lbl.configure(text=f"saved {time.strftime('%H:%M:%S')}", fg=self.th["ok"])

    def autosave(self):
        if self.dirty:
            try:
                self.save()
            except OSError:
                pass
        self.root.after(4000, self.autosave)

    def submit(self):
        self.save()
        self.status = "submitted"
        self.root.destroy()

    def on_close(self):
        self.save()
        self.status = "closed"
        self.root.destroy()

    def run(self):
        self.root.mainloop()
        return {"status": self.status, "seconds": int(time.time() - self.start), "file": str(self.path)}


def main():
    ap = argparse.ArgumentParser(description="Minimal exam editor")
    ap.add_argument("file")
    ap.add_argument("--minutes", type=float)
    ap.add_argument("--title")
    a = ap.parse_args()
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
    try:
        ed = Editor(a.file, a.minutes, a.title)
    except tk.TclError as e:
        print(json.dumps({"status": "error", "error": f"cannot open a window ({e}). No display? "
                          "Run this on a machine with a desktop session."}))
        sys.exit(2)
    print(json.dumps(ed.run()))


if __name__ == "__main__":
    main()
