"""Pieces shared by both study-browser engines (Windows WebView2 and Linux Qt):
allowlist policy, the idle page, and notes rendering. No GUI imports here."""

import html
import json
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, unquote
from urllib.request import url2pathname

from pagestyle import page

ROOT = Path(__file__).resolve().parent.parent
ALLOWLIST = Path(__file__).resolve().parent / "allowlist.json"
CACHE = ROOT / ".focus" / "browser"
CMD_FILE = ROOT / ".focus" / "browser_cmd.json"
PID_FILE = ROOT / ".focus" / "browser.pid"


def file_url(path):
    return Path(path).resolve().as_uri()


def strip(url):
    p = urlsplit(url)
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path, "", ""))


def load_allowlist():
    with open(ALLOWLIST, encoding="utf-8") as f:
        data = json.load(f)
    prefixes = [ln["url"] for sec in data["sections"] for ln in sec["links"]] + data.get("extra_prefixes", [])
    local = ROOT / ".focus" / "allowlist_local.json"   # per-machine additions (docs only)
    try:
        with open(local, encoding="utf-8") as f:
            prefixes += json.load(f).get("extra_prefixes", [])
    except (OSError, ValueError):
        pass
    return data, [strip(p) for p in prefixes]


def allowed(url, prefixes):
    """True if `url` may be opened as a page."""
    scheme = urlsplit(url).scheme.lower()
    if scheme in ("data", "about", "blob", "chrome-extension", "edge", "qrc"):
        return scheme != "edge" or url.startswith("edge://pdf")
    if scheme == "file":
        try:
            local = Path(url2pathname(unquote(urlsplit(url).path))).resolve()
            local.relative_to(ROOT)
            return True
        except (ValueError, OSError):
            return False
    if scheme in ("http", "https"):
        u = strip(url)
        alt = u.replace("http://", "https://", 1)
        return any(u.startswith(p) or alt.startswith(p) for p in prefixes)
    return False


def render_markdown(md_path):
    text = Path(md_path).read_text(encoding="utf-8")
    try:
        import markdown
        body = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists", "toc"])
    except ImportError:
        body = f"<pre>{html.escape(text)}</pre>"
    out = CACHE / "notes" / (Path(md_path).stem + ".html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page(Path(md_path).stem, body), encoding="utf-8")
    return out


def build_home(data):
    """The idle page. Deliberately NOT a hub of links (that invites wandering off): the browser only
    shows what the tutor opens."""
    CACHE.mkdir(parents=True, exist_ok=True)
    home = CACHE / "home.html"
    home.write_text(page("Study browser", "<div class='blocked'><h1>Study browser</h1>"
                         "<p class='muted'>Claude will open pages here when it shows you something.</p></div>"),
                    encoding="utf-8")
    return home


def blocked_html(url, home):
    return page("Blocked", f"<div class='blocked'><h1>Blocked — focus mode</h1><p class='muted'>{html.escape(url)}</p>"
                "<p>This page isn't on the study list. If you really need it for studying, ask Claude to add it.</p>"
                "<p class='muted'>Alt + &larr; goes back to the page you were on.</p></div>")


def resolve_target(target, home):
    """Turn a URL / repo path / '' into a URL string (rendering .md notes)."""
    import re
    if not target:
        return file_url(home)
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", target):
        return target
    frag = ""
    if "#" in target:
        target, frag = target.split("#", 1)
        frag = "#" + frag
    p = Path(target)
    if not p.is_absolute():
        p = ROOT / target
    if p.exists():
        if p.suffix.lower() == ".md":
            p = render_markdown(p)
        return file_url(p) + frag
    return "https://" + target + frag
