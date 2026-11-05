#!/usr/bin/env python3
"""Mock-exam window: one question at a time, a box per part, arrows to move between questions.

  * Top bar: countdown, [<] Q1 ... Q10 [>] (Alt+Left / Alt+Right also work), Instructions, Submit
  * Question pane on top (read-only); below it one answer box per part (a), (b), ... or 1., 2., ...
  * Per part (or per question, with the top button): Text mode (wraps like a notebook, Tab jumps to the
    next box) or Code mode (monospace, Tab/Shift+Tab indent, auto-indent after '{').
    Coding questions start in Code mode.
  * Tree check under every box: anything that looks like tree notation (38(5(1,22),56)) is checked
    for SYNTAX only - unbalanced parentheses, a child without a side, duplicate keys. Never whether
    the tree is the right answer.
  * Autosaves answers/<mock>-<time>.json (resumable) and a readable .md next to it.

Usage: python tools/mockui.py MOCK_JSON OUT_JSON [--minutes N] [--elapsed SECONDS] [--place left60]
On exit prints one JSON line: {"status": "submitted"|"closed", "seconds": N, "file": "<the .md>"}
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import editor  # noqa: E402  (themes, settings, font picking; also imports tkinter)
from editor import tk, tkfont  # noqa: E402
from tkinter import messagebox  # noqa: E402

PART_LETTER = re.compile(r"^\s*(?:\*\*)?\(?([a-h])\)(?:\*\*)?(?=\s|$)")
PART_NUMBER = re.compile(r"^\s*(\d{1,2})\.\s")
TREE_START = re.compile(r"(?<![A-Za-z_\d.^])-?\d+\s*\(")   # not k2(, S(6), log2(, 2^(


# ---------------------------------------------------------------- question parsing

def strip_code(prompt):
    return re.sub(r"```.*?```", "", prompt, flags=re.S)


def detect_parts(prompt):
    """Part labels in order: ['a', 'b', ...], ['1', '2', ...] or [''] (a single answer box)."""
    lines = strip_code(prompt).splitlines()
    letters = []
    for ln in lines:
        m = PART_LETTER.match(ln)
        if m and m.group(1) not in letters:
            letters.append(m.group(1))
    if len(letters) >= 2:
        return letters
    numbers = []
    for ln in lines:
        m = PART_NUMBER.match(ln)
        if m and m.group(1) not in numbers:
            numbers.append(m.group(1))
    if len(numbers) >= 3:
        return numbers
    return [""]


def given_stub(q):
    """The function the exam prints for the student to complete (same rule as study.py)."""
    if q.get("type") != "coding":
        return ""
    for block in re.findall(r"```(?:cpp|c\+\+)?\n(.*?)```", q["prompt"], re.S):
        first = next((ln.strip() for ln in block.splitlines() if ln.strip()), "")
        if re.match(r"(class|struct|template|#include)\b", first):
            continue
        if re.search(r"//\s*(write|your|insert)\b.*code", block, re.I) and "(" in first:
            return block.rstrip() + "\n"
    return ""


def label_of(part):
    if not part:
        return "Answer"
    return f"({part})" if part.isalpha() else f"{part}."


# ---------------------------------------------------------------- tree syntax check

def tree_candidates(text):
    """Substrings that look like tree notation: a number directly followed by '('."""
    out, i = [], 0
    while True:
        m = TREE_START.search(text, i)
        if not m:
            return out
        j = m.start()
        k = j
        while k < len(text) and (text[k].isdigit() or text[k] in "(),- \t"):
            k += 1
        cand = text[j:k].strip().rstrip(",")
        # only once it looks like a tree (a child or a closing paren typed), not "47(" mid-word
        if re.search(r"\(.*[\d,)]", cand) and re.search(r"[,)]", cand):
            out.append(cand)
        i = k


def extra_child(s):
    """Explain a node with 3+ children: name it, list its children, suggest moving a ')'."""
    stack = []  # (key, [child start indexes])
    key = None
    for i, ch in enumerate(s):
        if ch == "(":
            stack.append((key, [i + 1]))
        elif ch == ",":
            if not stack:
                return None
            stack[-1][1].append(i + 1)
            if len(stack[-1][1]) == 3:
                node, starts = stack[-1]
                ends = [b - 1 for b in starts[1:]]
                depth, j = 0, starts[2]
                while j < len(s) and not (depth == 0 and s[j] in ",)"):
                    depth += (s[j] == "(") - (s[j] == ")")
                    j += 1
                kids = [s[a:b] or "(empty)" for a, b in zip(starts, ends + [j])]
                fix = s[:i] + ")" + s[i:]
                if fix.endswith(")"):
                    fix = fix[:-1]
                try:
                    import avl
                    avl.parse(fix)
                except ValueError:
                    fix = None
                msg = (f"{node} has 3 children: {'  |  '.join(kids)}  - a node holds only (left,right). "
                       f"Probably a ')' is missing after {kids[1]}")
                return msg + (f".  Did you mean  {fix}" if fix else "")
        elif ch == ")":
            if stack:
                stack.pop()
        m = re.match(r"-?\d+", s[i:])
        if m and (i == 0 or not (s[i - 1].isdigit() or s[i - 1] == "-")):
            key = m.group()
    return None


def check_tree(s):
    """Return (ok, message) for one tree-notation string. Syntax only."""
    s = re.sub(r"\s+", "", s)
    opens, closes = s.count("("), s.count(")")
    if opens > closes:
        return False, f"missing {opens - closes} ')'  ({opens} '(' but {closes} ')')"
    if closes > opens:
        return False, f"{closes - opens} extra ')'  ({opens} '(' but {closes} ')')"
    m = re.search(r"(-?\d+)\((-?\d+)\)", s)
    if m:
        k, c = m.groups()
        return False, f"{k}({c}) - which side? write {k}({c},) for a LEFT child or {k}(,{c}) for a RIGHT child"
    if "()" in s or "(,)" in s:
        return False, "empty '()' - leave the parentheses off a leaf"
    keys = re.findall(r"-?\d+", s)
    dup = sorted({k for k in keys if keys.count(k) > 1}, key=keys.index)
    if dup:
        return False, f"key {dup[0]} appears twice"
    depth = 0
    for ch in s:
        depth += ch == "("
        depth -= ch == ")"
        if depth < 0:
            return False, "a ')' closes before its '(' - check the order of the parentheses"
    try:
        import avl
        avl.parse(s)
    except ValueError as e:
        msg = str(e)
        hint = "each node is key(left,right): one comma inside every pair of parentheses"
        if "expected ','" in msg:
            return False, f"missing ',' - {hint}"
        if "expected ')'" in msg:
            extra = extra_child(s)
            if extra:
                return False, extra
            return False, f"too many children / commas - {hint}"
        return False, f"can't read it - {hint}"
    return True, f"tree OK ({len(keys)} nodes)"


# ---------------------------------------------------------------- the window

class MockUI:
    def __init__(self, mock_path, out_path, minutes=None, elapsed=0, place=None):
        self.mock = json.loads(Path(mock_path).read_text(encoding="utf-8"))
        self.out = Path(out_path)
        self.md = self.out.with_suffix(".md")
        self.minutes = minutes if minutes is not None else self.mock.get("minutes", 70)
        self.start = time.time() - elapsed
        self.status = "closed"
        self.cfg = editor.load_settings()
        self.qs = self.mock["questions"]
        state = {}
        if self.out.exists():
            try:
                state = json.loads(self.out.read_text(encoding="utf-8"))
                self.start = time.time() - state.get("elapsed", elapsed)
            except ValueError:
                state = {}
        self.answers = state.get("answers", {})
        self.modes = state.get("modes", {})
        for q in self.qs:
            parts = detect_parts(q["prompt"])
            q["_parts"] = parts
            a = self.answers.setdefault(q["id"], {})
            for p in parts:
                a.setdefault(p, given_stub(q) if len(parts) == 1 else "")
            self.modes.setdefault(q["id"], "code" if q.get("type") == "coding" else "text")
        self.cur = min(state.get("current", 0), len(self.qs) - 1)
        self.boxes = []
        self.dirty = True

        self.root = tk.Tk()
        self.root.title(f"{self.mock.get('title', 'Mock exam')} - {self.minutes:g} minutes")
        self.root.geometry("1180x900")
        fam = editor.pick_mono(self.cfg["font_size"])[0]
        self.mono = tkfont.Font(family=fam, size=self.cfg["font_size"])
        self.qfont = tkfont.Font(family=fam, size=max(9, self.cfg["font_size"] - 1))
        self.tfont = tkfont.Font(family="Segoe UI" if "Segoe UI" in tkfont.families() else "TkDefaultFont",
                                 size=self.cfg["font_size"])
        self.small = tkfont.Font(family=self.tfont.actual("family"), size=max(9, self.cfg["font_size"] - 2))
        self.th = editor.THEMES.get(self.cfg.get("theme"), editor.THEMES["dark"])
        self._build()
        self.show(self.cur)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.tick()
        self.autosave()
        if place:
            self.root.after(300, lambda: self.place(place))

    def place(self, region):
        try:
            import winplace
            winplace.place_title(self.root.title(), region)
        except Exception:  # noqa: BLE001 - window placement is a nicety
            pass

    # ------------------------------------------------------------ layout
    def _build(self):
        th, r = self.th, self.root
        r.configure(bg=th["bar"])
        bar = tk.Frame(r, padx=6, pady=5, bg=th["bar"])
        bar.pack(side="top", fill="x")
        self.timer = tk.Label(bar, font=(self.mono.actual("family"), 13, "bold"), padx=8, bg=th["bar"], fg=th["bar_fg"])
        self.timer.pack(side="left")
        self.prev_btn = self._btn(bar, "◀", lambda: self.show(self.cur - 1), width=3)
        self.prev_btn.pack(side="left", padx=(10, 2))
        self.qbtns = []
        for i, q in enumerate(self.qs):
            b = self._btn(bar, f"Q{i + 1}", lambda i=i: self.show(i), width=4)
            b.pack(side="left", padx=1)
            self.qbtns.append(b)
        self.next_btn = self._btn(bar, "▶", lambda: self.show(self.cur + 1), width=3)
        self.next_btn.pack(side="left", padx=(2, 10))
        self._btn(bar, "Submit exam", self.submit).pack(side="right", padx=4)
        self._btn(bar, "Light/Dark", self.flip_theme).pack(side="right", padx=4)
        self._btn(bar, "Instructions", self.show_instructions).pack(side="right", padx=4)
        self.saved_lbl = tk.Label(bar, text="", bg=th["bar"], fg=th["ok"], font=self.small)
        self.saved_lbl.pack(side="right", padx=8)

        info = tk.Frame(r, padx=10, pady=3, bg=th["bar"])
        info.pack(side="top", fill="x")
        self.info_lbl = tk.Label(info, text="", bg=th["bar"], fg=th["bar_fg"], font=(self.tfont.actual("family"),
                                 self.cfg["font_size"], "bold"))
        self.info_lbl.pack(side="left")
        self.mode_btn = self._btn(info, "", self.toggle_mode)
        self.mode_btn.pack(side="right")
        tk.Label(info, text="Alt+← / Alt+→ : previous / next question", bg=th["bar"], fg=th["gutter_fg"],
                 font=self.small).pack(side="right", padx=12)

        pw = tk.PanedWindow(r, orient="vertical", sashwidth=7, sashrelief="flat", bg=th["bar"])
        pw.pack(fill="both", expand=True)
        qf = tk.Frame(pw)
        self.q = tk.Text(qf, wrap="word", font=self.qfont, padx=14, pady=10, relief="flat", borderwidth=0,
                         bg=th["q_bg"], fg=th["q_fg"], selectbackground=th["sel"])
        qs = tk.Scrollbar(qf, command=self.q.yview)
        self.q.configure(yscrollcommand=qs.set)
        qs.pack(side="right", fill="y")
        self.q.pack(side="left", fill="both", expand=True)
        pw.add(qf, minsize=80, height=330)

        af = tk.Frame(pw, bg=th["bg"])
        self.canvas = tk.Canvas(af, highlightthickness=0, borderwidth=0, bg=th["bg"])
        vs = tk.Scrollbar(af, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vs.set)
        vs.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=th["bg"])
        self.inner_id = self.canvas.create_window(0, 0, window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.inner_id, width=e.width))
        pw.add(af, minsize=150)

        for seq in ("<Alt-Left>", "<Control-Prior>"):
            r.bind_all(seq, lambda e: (self.show(self.cur - 1), "break")[1])
        for seq in ("<Alt-Right>", "<Control-Next>"):
            r.bind_all(seq, lambda e: (self.show(self.cur + 1), "break")[1])
        r.bind_all("<Control-s>", lambda e: (self.save(), "break")[1])
        r.bind_all("<Control-MouseWheel>", lambda e: self.zoom(1 if e.delta > 0 else -1))
        self.canvas.bind_all("<MouseWheel>", self.on_wheel)
        # Tk 8.6 on X11 (Linux) sends the wheel as Button-4 (up) / Button-5 (down), not <MouseWheel>
        self.canvas.bind_all("<Button-4>", self.on_wheel)
        self.canvas.bind_all("<Button-5>", self.on_wheel)

    def _btn(self, parent, text, cmd, width=None):
        th = self.th
        b = tk.Button(parent, text=text, command=cmd, padx=8, bg=th["q_bg"], fg=th["bar_fg"], relief="flat",
                      activebackground=th["sel"], activeforeground=th["bar_fg"], font=self.small)
        if width:
            b.configure(width=width)
        return b

    def on_wheel(self, e):
        w = e.widget
        if isinstance(w, tk.Text):
            return None          # the box scrolls itself
        if str(w).startswith(str(self.canvas)) or w is self.canvas:
            up = e.num == 4 or (e.num not in (4, 5) and e.delta > 0)
            self.canvas.yview_scroll(-1 if up else 1, "units")
        return None

    # ------------------------------------------------------------ showing a question
    def collect(self):
        """Copy the visible boxes back into self.answers."""
        q = self.qs[self.cur]
        for part, box, _ in self.boxes:
            self.answers[q["id"]][part] = box.get("1.0", "end-1c")

    def show(self, i):
        if not 0 <= i < len(self.qs):
            return
        if self.boxes:
            self.collect()
        self.cur = i
        q = self.qs[i]
        th = self.th
        self.q.configure(state="normal")
        self.q.delete("1.0", "end")
        self.q.insert("1.0", re.sub(r"\*\*", "", q["prompt"]).strip())
        self.q.configure(state="disabled")
        self.info_lbl.configure(text=f"Question {i + 1} of {len(self.qs)}   ·   {q['points']} points   ·   "
                                     f"{q.get('type', '')}   ·   suggested ≈{round(q['points'] * 0.65)} min")
        qmode = self.modes[q["id"]]
        self.mode_btn.configure(text=("All parts: CODE  (switch to text)" if qmode == "code" else
                                      "All parts: TEXT  (switch to code)"))
        for w in self.inner.winfo_children():
            w.destroy()
        self.boxes = []
        parts = q["_parts"]
        n = len(parts)
        base = 18 if n == 1 else (9 if n <= 3 else (6 if n <= 5 else 2))
        for part in parts:
            fr = tk.Frame(self.inner, bg=th["bg"], padx=12, pady=6)
            fr.pack(fill="x")
            mode = self.mode_of(q, part)
            row = tk.Frame(fr, bg=th["bg"])
            row.pack(fill="x")
            tk.Label(row, text=label_of(part), bg=th["bg"], fg=th["bar_fg"],
                     font=(self.tfont.actual("family"), self.cfg["font_size"], "bold")).pack(side="left")
            self._btn(row, "Code  (switch to text)" if mode == "code" else "Text  (switch to code)",
                      lambda p=part: self.toggle_part(p)).pack(side="right")
            txt = self.answers[q["id"]].get(part, "")
            lines = txt.count("\n") + 2
            box = tk.Text(fr, height=max(base, min(lines, 40)), undo=True, maxundo=-1, relief="flat",
                          borderwidth=0, padx=10, pady=8, highlightthickness=1,
                          highlightbackground=th["gutter"], highlightcolor=th["sel"],
                          bg=th["q_bg"], fg=th["fg"], insertbackground=th["cursor"], selectbackground=th["sel"],
                          insertwidth=2)
            if mode == "code":
                box.configure(wrap="word", font=self.mono, tabs=(self.mono.measure("    "),))
                box.bind("<Tab>", lambda e, b=box: self.code_tab(b))
                box.bind("<Shift-Tab>", lambda e, b=box: self.code_dedent(b))
                box.bind("<Return>", lambda e, b=box: self.code_return(b))
                box.bind("<braceright>", lambda e, b=box: self.code_close_brace(b))
            else:
                box.configure(wrap="word", font=self.tfont)
                box.bind("<Tab>", lambda e, b=box: (b.tk_focusNext().focus_set(), "break")[1])
            box.bind("<Shift-Tab>", lambda e, b=box, m=mode: (self.code_dedent(b) if m == "code"
                                                      else (b.tk_focusPrev().focus_set(), "break")[1]))
            box.insert("1.0", txt)
            box.edit_reset()
            status = tk.Label(fr, text="", bg=th["bg"], fg=th["gutter_fg"], font=self.small, anchor="w",
                              justify="left")
            box.pack(fill="x", expand=True)
            status.pack(fill="x", anchor="w")
            box.bind("<KeyRelease>", lambda e, b=box, s=status: self.on_edit(b, s))
            self.boxes.append((part, box, status))
            self.check_box(box, status)
        self.canvas.yview_moveto(0)
        self.q.yview_moveto(0)
        self.refresh_buttons()
        if self.boxes:
            first = self.boxes[0][1]
            first.focus_set()
            first.mark_set("insert", "end-1c")

    def refresh_buttons(self):
        th = self.th
        for i, (q, b) in enumerate(zip(self.qs, self.qbtns)):
            done = any(v.strip() and v.strip() != given_stub(q).strip() for v in self.answers[q["id"]].values())
            label = f"Q{i + 1}" + (" ✓" if done else "")
            b.configure(text=label, bg=th["sel"] if i == self.cur else th["q_bg"],
                        fg=th["ok"] if done and i != self.cur else th["bar_fg"])
        self.prev_btn.configure(state="normal" if self.cur > 0 else "disabled")
        self.next_btn.configure(state="normal" if self.cur < len(self.qs) - 1 else "disabled")

    def mode_of(self, q, part):
        return self.modes.get(f"{q['id']}/{part}", self.modes[q["id"]])

    def toggle_mode(self):
        q = self.qs[self.cur]
        self.collect()
        self.modes[q["id"]] = "text" if self.modes[q["id"]] == "code" else "code"
        for part in q["_parts"]:
            self.modes.pop(f"{q['id']}/{part}", None)
        self.boxes = []
        self.show(self.cur)
        self.dirty = True

    def toggle_part(self, part):
        q = self.qs[self.cur]
        self.collect()
        self.modes[f"{q['id']}/{part}"] = "text" if self.mode_of(q, part) == "code" else "code"
        self.boxes = []
        self.show(self.cur)
        self.dirty = True

    def show_instructions(self):
        self.q.configure(state="normal")
        self.q.delete("1.0", "end")
        self.q.insert("1.0", f"{self.mock.get('title', '')}\n\n{self.mock.get('instructions', '')}\n\n"
                             "(Click a question number or an arrow to go back to the questions.)")
        self.q.configure(state="disabled")

    # ------------------------------------------------------------ editing
    def on_edit(self, box, status):
        self.dirty = True
        self.saved_lbl.configure(text="● unsaved", fg=self.th["gutter_fg"])
        lines = int(box.index("end-1c").split(".")[0]) + 1
        if lines > int(box.cget("height")) and lines <= 40:
            box.configure(height=lines)
        if hasattr(box, "_job"):
            self.root.after_cancel(box._job)
        box._job = self.root.after(250, lambda: self.check_box(box, status))

    def check_box(self, box, status):
        text = box.get("1.0", "end-1c")
        msgs = []
        for cand in tree_candidates(text):
            ok, msg = check_tree(cand)
            short = cand if len(cand) <= 40 else cand[:37] + "..."
            msgs.append((ok, f"{'✓' if ok else '⚠'} {short}  →  {msg}"))
        if not msgs:
            status.configure(text="")
            return
        bad = [m for ok, m in msgs if not ok]
        status.configure(wraplength=max(box.winfo_width() - 20, 300))
        status.configure(text="\n".join(m for _, m in msgs), fg=self.th["warn"] if bad else self.th["ok"])

    def code_tab(self, b):
        try:
            a, z = b.index("sel.first"), b.index("sel.last")
            la, lz = int(a.split(".")[0]), int(z.split(".")[0])
            for ln in range(la, lz + 1):
                b.insert(f"{ln}.0", "    ")
        except tk.TclError:
            col = int(b.index("insert").split(".")[1])
            b.insert("insert", " " * (4 - col % 4))
        return "break"

    def code_dedent(self, b):
        try:
            la, lz = (int(b.index(x).split(".")[0]) for x in ("sel.first", "sel.last"))
        except tk.TclError:
            la = lz = int(b.index("insert").split(".")[0])
        for ln in range(la, lz + 1):
            lead = re.match(r" *", b.get(f"{ln}.0", f"{ln}.end")).group()
            if lead:
                b.delete(f"{ln}.0", f"{ln}.{min(4, len(lead))}")
        return "break"

    def code_return(self, b):
        before = b.get("insert linestart", "insert")
        indent = re.match(r"[ \t]*", before).group()
        extra = "    " if before.rstrip().endswith("{") else ""
        b.insert("insert", "\n" + indent + extra)
        b.see("insert")
        self.on_edit(b, next(s for _, bx, s in self.boxes if bx is b))
        return "break"

    def code_close_brace(self, b):
        before = b.get("insert linestart", "insert")
        if before and not before.strip():
            b.delete(f"insert-{min(4, len(before))}c", "insert")
        return None

    # ------------------------------------------------------------ theme / zoom
    def flip_theme(self):
        self.collect()
        self.cfg["theme"] = "light" if self.cfg.get("theme") == "dark" else "dark"
        editor.save_settings(self.cfg)
        self.th = editor.THEMES[self.cfg["theme"]]
        for w in self.root.winfo_children():
            w.destroy()
        self.boxes = []
        self._build()
        self.show(self.cur)

    def zoom(self, d):
        size = max(8, min(32, self.cfg["font_size"] + d))
        self.cfg["font_size"] = size
        for f, off in ((self.mono, 0), (self.tfont, 0), (self.qfont, -1), (self.small, -2)):
            f.configure(size=max(9, size + off))
        editor.save_settings(self.cfg)
        return "break"

    # ------------------------------------------------------------ timer / saving
    def tick(self):
        el = int(time.time() - self.start)
        left = int(self.minutes * 60) - el
        m, s = divmod(abs(left), 60)
        if left >= 0:
            txt = f"{m:02d}:{s:02d} left"
            color = self.th["warn"] if left < 5 * 60 else self.th["bar_fg"]
        else:
            txt, color = f"TIME UP  -{m:02d}:{s:02d}", self.th["warn"]
        self.timer.configure(text=txt, fg=color)
        self.root.after(1000, self.tick)

    def to_markdown(self):
        out = [f"# {self.mock.get('title', '')} - answers", ""]
        for i, q in enumerate(self.qs, 1):
            out += [f"### Question {i} ({q['id']}) [{q['points']} pts]", ""]
            for part in q["_parts"]:
                txt = self.answers[q["id"]].get(part, "").rstrip()
                if part:
                    out.append(f"{label_of(part)}")
                code = self.mode_of(q, part) == "code"
                if txt and code:
                    out += ["```cpp", txt, "```"]
                else:
                    out.append(txt or "(blank)")
                out.append("")
        return "\n".join(out) + "\n"

    def save(self):
        if self.boxes:
            self.collect()
        state = {"mock": self.mock.get("id"), "answers": self.answers, "modes": self.modes,
                 "current": self.cur, "elapsed": int(time.time() - self.start)}
        for path, content in ((self.out, json.dumps(state, indent=1, ensure_ascii=False)),
                              (self.md, self.to_markdown())):
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_text(content, encoding="utf-8", newline="\n")
            tmp.replace(path)
        self.dirty = False
        self.saved_lbl.configure(text=f"saved {time.strftime('%H:%M:%S')}", fg=self.th["ok"])
        self.refresh_buttons()

    def autosave(self):
        if self.dirty:
            try:
                self.save()
            except OSError:
                pass
        self.root.after(4000, self.autosave)

    def submit(self):
        self.collect()
        empty = [f"Q{i + 1}" for i, q in enumerate(self.qs)
                 if not any(v.strip() and v.strip() != given_stub(q).strip() for v in self.answers[q["id"]].values())]
        msg = "Submit the whole exam now?"
        if empty:
            msg += f"\n\nNo answer yet for: {', '.join(empty)}"
        if not messagebox.askyesno("Submit exam", msg, parent=self.root):
            return
        self.save()
        self.status = "submitted"
        self.root.destroy()

    def on_close(self):
        self.save()
        self.status = "closed"
        self.root.destroy()

    def run(self):
        self.root.mainloop()
        return {"status": self.status, "seconds": int(time.time() - self.start), "file": str(self.md)}


def main():
    ap = argparse.ArgumentParser(description="Mock-exam window")
    ap.add_argument("mock")
    ap.add_argument("out")
    ap.add_argument("--minutes", type=float)
    ap.add_argument("--elapsed", type=int, default=0, help="seconds already used (resume a paused exam)")
    ap.add_argument("--place", help="screen region for the window (Windows), e.g. left60")
    a = ap.parse_args()
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
    try:
        ui = MockUI(a.mock, a.out, a.minutes, a.elapsed, a.place)
    except tk.TclError as e:
        print(json.dumps({"status": "error", "error": f"cannot open a window ({e})"}))
        sys.exit(2)
    print(json.dumps(ui.run()))


if __name__ == "__main__":
    main()
