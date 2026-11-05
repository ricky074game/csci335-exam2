"""Shared page styling for the study browser and generated "show me" pages."""

import html

CSS = """
:root { color-scheme: light dark; --bg:#ffffff; --fg:#1f2328; --muted:#59636e; --card:#f6f8fa; --line:#d1d9e0;
        --accent:#0969da; --code:#eff1f3; }
@media (prefers-color-scheme: dark) { :root { --bg:#0d1117; --fg:#e6edf3; --muted:#9198a1; --card:#151b23;
        --line:#3d444d; --accent:#4493f8; --code:#1f2428; } }
body { background:var(--bg); color:var(--fg); font:16px/1.6 -apple-system,"Segoe UI",Ubuntu,Roboto,sans-serif;
       max-width: 980px; margin: 0 auto; padding: 24px 28px 80px; }
a { color: var(--accent); text-decoration: none; } a:hover { text-decoration: underline; }
h1 { font-size: 1.7em; border-bottom: 1px solid var(--line); padding-bottom: .3em; }
h2 { font-size: 1.35em; border-bottom: 1px solid var(--line); padding-bottom: .25em; margin-top: 1.6em; }
code { background: var(--code); padding: .1em .35em; border-radius: 4px; font: 14px/1.5 Consolas,"DejaVu Sans Mono",monospace; }
pre { background: var(--code); padding: 12px 14px; border-radius: 6px; overflow-x: auto; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; margin: 12px 0; display:block; overflow-x:auto; }
th, td { border: 1px solid var(--line); padding: 5px 10px; text-align: left; vertical-align: top; }
th { background: var(--card); }
blockquote { border-left: 4px solid var(--line); margin: 0; padding: 0 1em; color: var(--muted); }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 10px; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 8px; padding: 10px 14px; }
.muted { color: var(--muted); font-size: .92em; }
.blocked { margin-top: 15vh; text-align: center; }
"""


def page(title, body):
    return (f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title>"
            f"<style>{CSS}</style></head><body>{body}</body></html>")


