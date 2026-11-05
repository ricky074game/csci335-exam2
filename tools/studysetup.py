"""First-time setup helpers for `study setup ...` (driven by the /setup slash command).

  check              what is installed / missing, with the fix for each item
  name NAME          store the student's name (and --hours per day) in progress/progress.json
  textbook PDF       copy the Weiss textbook PDF in and extract the in-scope chapters (5.1-5.6, 6.1-6.4, 7)
  material ZIP...    unpack Brightspace zips, keeping ONLY Exam 2 files (hashing/STL/heaps/sorting slides,
                     HW5+, HW5 solutions, the Exam 2 materials folder) and convert them to text
  browser            install the locked-down study browser into .venv (Windows: WebView2, Linux/macOS: Qt)
  allowlist          regenerate tools/allowlist.json from every doc link in notes/, bank/, mocks/, material/
  repo-info          git remotes + how to make your own private progress repo
"""

import html
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
MAT = ROOT / "material"
TEXT = MAT / "text"
TB = MAT / "textbook"
IS_WIN = os.name == "nt"


def ok(flag):
    return "[ok]" if flag else "[--]"


def _run(cmd, **kw):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, **kw)
    except (OSError, subprocess.SubprocessError):
        return None


# ---------------------------------------------------------------- check

def check(progress):
    lines = []
    py_ok = sys.version_info >= (3, 8)
    lines.append(f"{ok(py_ok)} Python {sys.version.split()[0]} ({sys.executable})")
    try:
        import tkinter  # noqa: F401
        tk_ok = True
    except Exception:  # noqa: BLE001
        tk_ok = False
    lines.append(f"{ok(tk_ok)} Tk (exam editor + mock window)" + ("" if tk_ok else
                 "  -> Ubuntu: sudo apt install python3-tk | Fedora: sudo dnf install python3-tkinter | "
                 "macOS: brew install python-tk"))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    venv = ROOT / ".venv"
    br = browser_installed()
    lines.append(f"{ok(br)} study browser (.venv)" + ("" if br else "  -> study setup browser"))
    gpp = shutil.which("g++")
    arm = shutil.which("arm-none-eabi-g++")
    clang = shutil.which("clang++")
    lines.append(f"{ok(gpp or clang or arm)} C++ compiler for checking code answers: "
                 f"{gpp or clang or arm or 'none (optional: install g++ / MinGW / Xcode CLT)'}")
    tb = sorted(p.name for p in TB.glob("ch*.txt")) if TB.exists() else []
    lines.append(f"{ok(len(tb) >= 3)} textbook chapters: {', '.join(tb) or 'missing'}" +
                 ("" if tb else "  -> study setup textbook <path to Weiss DataStructures.pdf> (optional but best)"))
    mats = sorted(p.name for p in TEXT.glob("*.txt")) if TEXT.exists() else []
    lines.append(f"{ok(bool(mats))} course material text files: {len(mats)}" +
                 ("" if mats else "  -> study setup material <Brightspace zip(s)>"))
    name = progress.get("student", {}).get("name")
    lines.append(f"{ok(bool(name))} student name: {name or 'not set  -> study setup name \"Your Name\"'}")
    try:
        import focus
        loc = focus.load_local()
        lines.append(f"{ok(True)} focus mode: {'enabled' if loc['enabled'] else 'disabled'} "
                     f"(study focus config show)")
    except Exception as e:  # noqa: BLE001
        lines.append(f"{ok(False)} focus mode: {e}")
    git = shutil.which("git")
    remote = _run(["git", "-C", str(ROOT), "remote", "-v"]) if git else None
    rtxt = (remote.stdout.strip().splitlines()[0] if remote and remote.stdout.strip() else "no remote")
    lines.append(f"{ok(bool(git))} git: {rtxt}")
    gh = shutil.which("gh")
    lines.append(f"{ok(bool(gh))} GitHub CLI (gh): {'installed' if gh else 'missing (optional: for your own private progress repo)'}")
    tts = "Windows voice" if IS_WIN else (shutil.which("spd-say") or shutil.which("espeak-ng") or
                                         shutil.which("say") or "none (optional)")
    lines.append(f"[..] voice: {tts}")
    _ = venv
    return "\n".join(lines)


# ---------------------------------------------------------------- name

def set_name(progress, name, hours=None):
    st = progress.setdefault("student", {})
    st["name"] = name
    if hours:
        st["hours_per_day"] = hours
    return f"student name set to {name}" + (f", ~{hours:g} h/day" if hours else "")


# ---------------------------------------------------------------- text extraction

def pdf_to_text(pdf, out, layout=True):
    """pdftotext if present, else PyMuPDF, else pypdf. Returns the tool used or raises."""
    exe = shutil.which("pdftotext")
    if exe:
        r = _run([exe] + (["-layout"] if layout else []) + [str(pdf), str(out)])
        if r and r.returncode == 0:
            return "pdftotext"
    try:
        import pymupdf as fitz  # noqa: F401
    except ImportError:
        try:
            import fitz  # noqa: F401
        except ImportError:
            fitz = None
    if fitz is not None:
        doc = fitz.open(str(pdf))
        Path(out).write_text("\n".join(p.get_text() for p in doc), encoding="utf-8")
        return "pymupdf"
    try:
        from pypdf import PdfReader
        r = PdfReader(str(pdf))
        Path(out).write_text("\n".join((p.extract_text() or "") for p in r.pages), encoding="utf-8")
        return "pypdf"
    except ImportError:
        raise RuntimeError("no PDF text tool: install poppler (pdftotext) or `python -m pip install --user pymupdf`")


def html_to_text(src, out):
    t = Path(src).read_text(encoding="utf-8", errors="replace")
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", t, flags=re.S)
    t = re.sub(r"<br\s*/?>|</p>|</li>|</h\d>|</div>|</tr>", "\n", t)
    t = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>', r"[LINK: \1] ", t)
    t = re.sub(r"<[^>]+>", "", t)
    Path(out).write_text(re.sub(r"\n\s*\n+", "\n", html.unescape(t)).strip() + "\n", encoding="utf-8")


# ---------------------------------------------------------------- textbook

# (output file, start regex, end regex) - searched after the table of contents
SPLITS = [
    ("ch5_hashing_5.1-5.6.txt", r"^\s*5\.1\s+General Idea\s*$", r"^\s*5\.7\s+Hash Tables with Worst-Case"),
    ("ch5_exercises.txt", r"^\s*5\.1\s+Given input \{4371", r"^\s*References\s*$"),
    ("ch6_heaps_6.1-6.4.txt", r"^\s*6\.1\s+Model\s*$", r"^\s*6\.5\s+d-Heaps"),
    ("ch6_exercises.txt", r"^\s*6\.1\s+Can both insert and findMin", r"^\s*References\s*$"),
    ("ch7_sorting.txt", r"^\s*7\.1\s+Preliminaries\s*$", r"The Disjoint Sets Class\s*$"),
]


def textbook(pdf):
    pdf = Path(pdf).expanduser()
    if not pdf.exists():
        return f"no such file: {pdf}"
    TB.mkdir(parents=True, exist_ok=True)
    dest = TB / "DataStructures.pdf"
    if pdf.resolve() != dest.resolve():
        shutil.copyfile(pdf, dest)
    full = TB / "textbook.txt"
    tool = pdf_to_text(dest, full)
    lines = full.read_text(encoding="utf-8", errors="replace").splitlines()
    # skip the table of contents: start searching after the first "Chapter 1" body text (~ first 3% of lines)
    skip = max(200, len(lines) // 40)
    report = [f"extracted {len(lines)} lines with {tool}"]
    for name, start_re, end_re in SPLITS:
        s = next((i for i in range(skip, len(lines)) if re.search(start_re, lines[i])), None)
        if s is None:
            report.append(f"  {name}: start marker not found - use textbook.txt directly")
            continue
        e = next((i for i in range(s + 5, len(lines)) if re.search(end_re, lines[i])), min(len(lines), s + 4000))
        (TB / name).write_text("\n".join(lines[max(0, s - 2):e]) + "\n", encoding="utf-8")
        report.append(f"  {name}: lines {s}-{e} ({e - s} lines)")
    report.append("textbook stays on this machine only (material/textbook/ is git-ignored - it is copyrighted)")
    return "\n".join(report)


# ---------------------------------------------------------------- course material

EXAM1_ONLY = re.compile(r"Move Semantics|Algorithm Analysis|Asymptotic Complexity|Iterator|Self Balancing|AVL|"
                        r"splay_Btrees|Exam 1|HW 3 answer|Homework [1-4]\b", re.I)
SLIDES = re.compile(r"Associative Arrays and Hashing|C\+\+ STL|Leetcode Hashing|^Heaps|Sorting", re.I)
HW = re.compile(r"^Homework (\d+)", re.I)
SOL = re.compile(r"solution|Hash Insertions", re.I)


def _dest_for(name, zip_is_exam2):
    base = Path(name).name
    if base.lower() == "table of contents.html":
        return None
    if zip_is_exam2:
        return "exam2"
    if EXAM1_ONLY.search(base):
        return None
    m = HW.match(base)
    if m:
        n = int(m.group(1))
        if n < 5:
            return None
        return "solutions" if SOL.search(base) else "hw"
    if SOL.search(base):
        return "solutions"
    if SLIDES.search(base):
        return "slides"
    return None


def material(zips):
    out = []
    TEXT.mkdir(parents=True, exist_ok=True)
    for z in zips:
        z = Path(z).expanduser()
        if not z.exists():
            out.append(f"no such file: {z}")
            continue
        with zipfile.ZipFile(z) as zf:
            names = zf.namelist()
            toc = next((n for n in names if n.lower().endswith("table of contents.html")), None)
            toc_text = zf.read(toc).decode("utf-8", "replace") if toc else ""
            is_exam2 = "Exam 2" in toc_text
            kept, skipped = [], []
            for n in names:
                if n.endswith("/"):
                    continue
                d = _dest_for(n, is_exam2)
                if d is None:
                    skipped.append(Path(n).name)
                    continue
                target = MAT / d / Path(n).name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(zf.read(n))
                stem = f"{d}_{target.stem.replace(' ', '_')}.txt"
                try:
                    if target.suffix.lower() == ".pdf":
                        pdf_to_text(target, TEXT / stem)
                    elif target.suffix.lower() in (".html", ".htm"):
                        html_to_text(target, TEXT / stem)
                except Exception as e:  # noqa: BLE001
                    out.append(f"  could not convert {target.name}: {e}")
                kept.append(f"{d}/{target.name}")
        out.append(f"{z.name}: kept {len(kept)}" + (f" -> {', '.join(kept)}" if kept else "") +
                   (f"; skipped {len(skipped)} (Exam 1 / not needed)" if skipped else ""))
    return "\n".join(out)


# ---------------------------------------------------------------- study browser install

def browser_installed():
    py = ROOT / ".venv" / ("Scripts/python.exe" if IS_WIN else "bin/python")
    if not py.exists():
        return False
    mod = "webview" if IS_WIN else "PyQt6.QtWebEngineWidgets"
    r = _run([str(py), "-c", f"import {mod}, markdown"])
    return bool(r and r.returncode == 0)


def browser():
    if browser_installed():
        return "study browser already installed (.venv)"
    venv = ROOT / ".venv"
    log = []
    if IS_WIN:
        req = ROOT / "requirements-windows.txt"
        uv = shutil.which("uv")
        if not uv:
            r = _run([sys.executable, "-m", "pip", "install", "--user", "uv"])
            log.append("installed uv" if r and r.returncode == 0 else "could not pip-install uv")
            uv_cmd = [sys.executable, "-m", "uv"]
        else:
            uv_cmd = [uv]
        # pywebview's pythonnet needs a Python it supports - uv fetches 3.12 if needed
        r = _run(uv_cmd + ["venv", "--python", "3.12", str(venv)], cwd=str(ROOT))
        if not r or r.returncode != 0:
            log.append("uv venv failed: " + ((r.stderr or "")[-300:] if r else "uv not runnable"))
            r = _run([sys.executable, "-m", "venv", str(venv)])
            log.append("made .venv with this Python instead" if r and r.returncode == 0 else "venv failed")
            pip = [str(venv / "Scripts/python.exe"), "-m", "pip", "install", "-r", str(req)]
        else:
            pip = uv_cmd + ["pip", "install", "--python", str(venv / "Scripts/python.exe"), "-r", str(req)]
        r = _run(pip, cwd=str(ROOT))
        log.append("installed pywebview + markdown" if r and r.returncode == 0 else
                   "package install failed: " + ((r.stderr or r.stdout or "")[-400:] if r else "?"))
    else:
        req = ROOT / "requirements.txt"
        r = _run([sys.executable, "-m", "venv", str(venv)])
        if not r or r.returncode != 0:
            return ("could not create .venv" + ((": " + r.stderr[-300:]) if r else "") +
                    "\nUbuntu/Debian: sudo apt install python3-venv  (then run study setup browser again)")
        r = _run([str(venv / "bin/python"), "-m", "pip", "install", "-r", str(req)], cwd=str(ROOT))
        log.append("installed PyQt6 + PyQt6-WebEngine + markdown" if r and r.returncode == 0 else
                   "package install failed: " + ((r.stderr or "")[-400:] if r else "?"))
    log.append("study browser ready" if browser_installed() else
               "study browser NOT ready - the tutor still works; links just won't open in the locked-down browser")
    return "\n".join(log)


# ---------------------------------------------------------------- allowlist

DOC_HOSTS = {
    "cplusplus.com": "C++ reference",
    "www.cplusplus.com": "C++ reference",
    "legacy.cplusplus.com": "C++ reference",
    "en.cppreference.com": "C++ reference",
    "leetcode.com": "Practice problems (HW / slides)",
    "www.cs.usfca.edu": "Visualizations",
    "opendsa-server.cs.vt.edu": "Visualizations",
    "visualgo.net": "Visualizations",
    "en.wikipedia.org": "Reference articles",
    "www.javatpoint.com": "Reference articles",
    "stackoverflow.com": "Reference articles",
    "www.geeksforgeeks.org": "Reference articles",
}
ALWAYS = [
    "https://en.cppreference.com/", "https://cplusplus.com/reference/", "https://www.cplusplus.com/reference/",
    "https://legacy.cplusplus.com/reference/", "https://www.cs.usfca.edu/~galles/visualization/",
    "https://opendsa-server.cs.vt.edu/embed/",
]
URL_RE = re.compile(r"https?://[^\s\"'<>)\]]+")


def _unwrap(url):
    if "safelinks.protection.outlook.com" in url:
        q = parse_qs(urlsplit(url).query).get("url")
        if q:
            return unquote(q[0])
    return url.rstrip(".,;")


def allowlist():
    found = {}
    files = []
    for d, pats in ((ROOT / "notes", ["*.md"]), (ROOT / "bank", ["*.json"]), (ROOT / "mocks", ["*.json"]),
                    (TEXT, ["*.txt"]), (ROOT, ["CLAUDE.md"])):
        for pat in pats:
            files += sorted(d.glob(pat)) if d.exists() else []
    for f in files:
        for u in URL_RE.findall(f.read_text(encoding="utf-8", errors="replace")):
            u = _unwrap(u)
            host = urlsplit(u).netloc.lower()
            if host in DOC_HOSTS:
                if host == "leetcode.com":   # one problem page (and its tabs), not the whole site
                    m = re.match(r"(https://leetcode\.com/problems/[^/]+/)", u + ("/" if not u.endswith("/") else ""))
                    if not m:
                        continue
                    u = m.group(1)
                found.setdefault(DOC_HOSTS[host], set()).add(u)
    sections = []
    for title in sorted(found):
        links = [{"name": urlsplit(u).path.strip("/").split("/")[-1].replace("-", " ").replace("_", " ") or u,
                  "url": u} for u in sorted(found[title])]
        sections.append({"title": title, "links": links})
    data = {"_comment": "GENERATED by `study setup allowlist` from the links in notes/, bank/, mocks/ and material/. "
                        "Each entry is a URL prefix the study browser may open. Personal additions go in "
                        ".focus/allowlist_local.json ({\"extra_prefixes\": [...]}) - documentation only.",
            "sections": sections, "extra_prefixes": ALWAYS}
    path = ROOT / "tools" / "allowlist.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    n = sum(len(s["links"]) for s in sections)
    return f"wrote tools/allowlist.json: {n} links in {len(sections)} sections + {len(ALWAYS)} always-allowed prefixes"


# ---------------------------------------------------------------- repo

def repo_info():
    lines = []
    r = _run(["git", "-C", str(ROOT), "remote", "-v"])
    lines.append("git remotes:\n" + ((r.stdout.strip() if r and r.stdout.strip() else "  (none)")))
    r = _run(["gh", "auth", "status"])
    lines.append("gh: " + ("logged in" if r and r.returncode == 0 else "not logged in / not installed"))
    lines.append("To keep your progress in your OWN private repo (so it syncs between computers):\n"
                 "  gh repo create <your-user>/csci335-exam2-study --private --source . --remote origin --push\n"
                 "  (if origin already points at the shared template: git remote rename origin upstream first;\n"
                 "   later `git pull upstream main` brings in new questions/fixes)")
    return "\n".join(lines)
