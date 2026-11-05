"""Diagram pages for the study browser: `study viz KIND ...`.

Every function returns (name, title, body_html); study.py writes the page with write_view() and shows it.
All pictures are inline SVG (no network, works in light and dark mode).

Kinds:
  memory    VALUES                     vector block vs list nodes vs set tree, with costs
  erase     VALUES --at I              one erase: vector shifts left (O(n)) vs list unlinks (O(1))
  eraseloop VALUES --remove odd        step-through of the erase-in-loop bug (or --fixed), --container list
  overwriter VALUES --remove odd       the O(n) two-iterator removal on a vector
  move      --op ctor|ctor-copy|ctor-no-null|assign|assign-no-delete|self  [--members "a_:int,..."]
  loops     [--kinds linear,square,triangle,log,nlogn] [--n 8]   Big-O loop counting as dot grids
  iterators                            iterator categories: jump vs walk, which container has which
  costs                                STL cost sheet (vector / list / set) with the reason for each
  bst       TREE insert|remove X       plain BST walk (no rebalancing), path highlighted
  page      FILE.html|.svg|.md         wrap your own snippet in the study page style
"""

import html
import math
from pathlib import Path

import avl

C = {"blue": "#0969da", "green": "#2da44e", "red": "#cf222e", "amber": "#bf8700",
     "purple": "#8250df", "grey": "#8c959f"}

SVG_CSS = ("<style>.t{font:14px 'Segoe UI',sans-serif;fill:currentColor}"
           ".m{font:600 15px Consolas,monospace;fill:currentColor;text-anchor:middle}"
           ".s{font:12px 'Segoe UI',sans-serif;fill:#8c959f}"
           ".b{font:700 14px 'Segoe UI',sans-serif;fill:currentColor}"
           ".box{fill:none;stroke:currentColor;stroke-width:1.6}"
           ".ln{stroke:currentColor;stroke-width:1.7;fill:none}</style>")

PAGE_CSS = ("<style>.keybox{border-left:4px solid #0969da;padding:6px 12px;background:var(--card);border-radius:4px}"
            ".pill{display:inline-block;padding:1px 8px;border-radius:10px;font-size:.85em;color:#fff}"
            "td.ok{color:#2da44e;font-weight:600} td.bad{color:#cf222e;font-weight:600}"
            "td.mid{color:#bf8700;font-weight:600}</style>")


def esc(s):
    return html.escape(str(s))


def _defs():
    out = ["<defs>"]
    for name, col in [("ah", "currentColor")] + [(f"ah-{k}", v) for k, v in C.items()]:
        out.append(f"<marker id='{name}' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='7' markerHeight='7' "
                   f"orient='auto-start-reverse'><path d='M0,0 L10,5 L0,10 z' fill='{col}'/></marker>")
    out.append("</defs>")
    return "".join(out)


def svg(w, h, parts):
    w, h = int(w), int(h)
    return f"<svg width='{w}' height='{h}' viewBox='0 0 {w} {h}'>{SVG_CSS}{_defs()}{''.join(parts)}</svg>"


def rect(x, y, w, h, color=None, fill=None, dash=False, rx=4, width=None):
    st = ""
    if color:
        st += f"stroke:{C.get(color, color)};"
    if fill:
        st += f"fill:{C.get(fill, fill)}33;" if fill in C else f"fill:{fill};"
    if width:
        st += f"stroke-width:{width};"
    da = " stroke-dasharray='5 4'" if dash else ""
    return f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='{rx}' class='box' style='{st}'{da}/>"


def text(x, y, s, cls="t", color=None, anchor=None, weight=None, size=None):
    st = []
    if color:
        st.append(f"fill:{C.get(color, color)}")
    if anchor:
        st.append(f"text-anchor:{anchor}")
    if weight:
        st.append(f"font-weight:{weight}")
    if size:
        st.append(f"font-size:{size}px")
    return f"<text x='{x}' y='{y}' class='{cls}' style='{';'.join(st)}'>{esc(s)}</text>"


def arrow(x1, y1, x2, y2, color=None, dash=False, curve=0, both=False, vertical=False):
    mk = f"ah-{color}" if color else "ah"
    col = C[color] if color else "currentColor"
    if curve and vertical:
        d = f"M{x1},{y1} C{x1},{y1 + curve} {x2},{y2 - curve} {x2},{y2}"
    elif curve:
        d = f"M{x1},{y1} C{x1 + curve},{y1} {x2 - curve},{y2} {x2},{y2}"
    else:
        d = f"M{x1},{y1} L{x2},{y2}"
    da = " stroke-dasharray='5 4'" if dash else ""
    start = f" marker-start='url(#{mk})'" if both else ""
    return f"<path d='{d}' class='ln' style='stroke:{col}' marker-end='url(#{mk})'{start}{da}/>"


def frames_html(title, intro, frames, extra=""):
    body = [PAGE_CSS, f"<h1>{esc(title)}</h1>"]
    if intro:
        body.append(f"<p>{intro}</p>")
    if extra:
        body.append(extra)
    for i, (head, pic, txt) in enumerate(frames, 1):
        body.append(f"<h2>{i} · {head}</h2><p>{txt}</p><div class='pic'>{pic}</div>")
    return "\n".join(body)


def parse_values(s):
    if not s:
        raise ValueError("give the values, e.g. 7,-2,5,9,4")
    return [int(v) for v in s.replace(" ", "").split(",") if v]


def make_pred(spec):
    """'odd' | 'even' | 'neg' | 'pos' | '<N' | '>N' | '=N' | 'N'  ->  (predicate, description)."""
    s = (spec or "odd").strip().lower()
    if s == "odd":
        return (lambda x: x % 2 != 0), "odd"
    if s == "even":
        return (lambda x: x % 2 == 0), "even"
    if s in ("neg", "negative", "<0"):
        return (lambda x: x < 0), "negative"
    if s in ("pos", "positive", ">0"):
        return (lambda x: x > 0), "positive"
    if s.startswith("<"):
        n = int(s[1:])
        return (lambda x: x < n), f"less than {n}"
    if s.startswith(">"):
        n = int(s[1:])
        return (lambda x: x > n), f"greater than {n}"
    n = int(s.lstrip("="))
    return (lambda x: x == n), f"equal to {n}"


# ------------------------------------------------------------------ vector row / list row primitives

CW, CH = 50, 40


def vec_row(values, x0, y0, colors=None, ghost=(), end=True, idx=True, labels=None):
    colors = colors or {}
    parts = []
    for i, v in enumerate(values):
        x = x0 + i * CW
        c = colors.get(i)
        parts.append(rect(x, y0, CW, CH, color=c, fill=c, dash=i in ghost, rx=0, width=2.4 if c else None))
        parts.append(text(x + CW / 2, y0 + CH / 2 + 5, v, "m", color="grey" if i in ghost else None))
        if idx:
            parts.append(text(x + CW / 2, y0 + CH + 16, labels[i] if labels else f"[{i}]", "s", anchor="middle"))
    if end:
        x = x0 + len(values) * CW
        parts.append(rect(x, y0, CW, CH, color="grey", dash=True, rx=0))
        parts.append(text(x + CW / 2, y0 + CH / 2 + 5, "end()", "s", anchor="middle"))
    return parts


def pointer(x0, y0, i, label="it", color="blue", below=False):
    cx = x0 + i * CW + CW / 2
    if below:
        return [text(cx, y0 + CH + 62, label, "b", color=color, anchor="middle"),
                arrow(cx, y0 + CH + 48, cx, y0 + CH + 22, color=color)]
    return [text(cx, y0 - 30, label, "b", color=color, anchor="middle"),
            arrow(cx, y0 - 25, cx, y0 - 3, color=color)]


NW, NGAP = 50, 34


def list_row(values, x0, y0, colors=None, end=True):
    colors = colors or {}
    parts = []
    step = NW + NGAP
    for i, v in enumerate(values):
        x = x0 + i * step
        c = colors.get(i)
        parts.append(rect(x, y0, NW, CH, color=c, fill=c, rx=8, width=2.4 if c else None))
        parts.append(text(x + NW / 2, y0 + CH / 2 + 5, v, "m"))
        if i + 1 < len(values) or end:
            parts.append(arrow(x + NW + 2, y0 + CH / 2, x + step - 2, y0 + CH / 2, both=True))
    if end:
        x = x0 + len(values) * step
        parts.append(rect(x, y0, NW, CH, color="grey", dash=True, rx=8))
        parts.append(text(x + NW / 2, y0 + CH / 2 + 5, "end()", "s", anchor="middle"))
    return parts


def list_pointer(x0, y0, i, label="it", color="blue"):
    cx = x0 + i * (NW + NGAP) + NW / 2
    return [text(cx, y0 - 30, label, "b", color=color, anchor="middle"),
            arrow(cx, y0 - 25, cx, y0 - 3, color=color)]


# ------------------------------------------------------------------ memory: vector vs list vs set

def memory(values):
    vals = values
    x0 = 20
    # vector: one contiguous block with addresses
    w = x0 * 2 + (len(vals) + 1) * CW + 40
    p = [text(x0, 22, "vector: ONE contiguous block (elements side by side)", "b")]
    p += vec_row(vals, x0, 56, labels=[f"{1000 + 4 * i}" for i in range(len(vals))])
    p.append(text(x0, 128, "addresses 1000, 1004, 1008 ... so element k is at 1000 + 4k: jump straight there", "s"))
    vec_svg = svg(max(w, 640), 140, p)

    # list: nodes scattered in memory, each with prev/next pointers
    step = NW + NGAP + 10
    ys = [60, 110, 40, 120, 70, 30, 100, 55]
    p = [text(x0, 20, "list: separate NODES scattered in memory, linked by prev/next pointers", "b")]
    for i, v in enumerate(vals):
        x, y = x0 + i * step, ys[i % len(ys)]
        p.append(rect(x, y, NW, CH, rx=8))
        p.append(text(x + NW / 2, y + CH / 2 + 5, v, "m"))
        if i + 1 < len(vals):
            x2, y2 = x0 + (i + 1) * step, ys[(i + 1) % len(ys)]
            p.append(arrow(x + NW + 2, y + CH / 2, x2 - 2, y2 + CH / 2, both=True))
    p.append(text(x0, 186, "to reach element k you must follow k next-pointers: walk, no jumping", "s"))
    list_svg = svg(max(x0 * 2 + len(vals) * step, 640), 196, p)

    # set: balanced BST of nodes
    t = None
    for v in sorted(set(vals), key=vals.index):
        t, _, _ = avl.trace_insert(t, v)
    set_svg = avl.svg(t, show_balance=False)

    rows = [("access element k (<code>v[k]</code>)", "O(1) jump", "O(n) walk", "n/a (no index)"),
            ("find a value", "O(n) <code>std::find</code>", "O(n) <code>std::find</code>", "O(log n) <code>s.find</code>"),
            ("insert/erase at the end", "amortized O(1) <code>push_back</code>", "O(1)", "O(log n)"),
            ("insert/erase at the front", "O(n) (everything shifts)", "O(1)", "O(log n)"),
            ("insert/erase in the middle, given an iterator", "O(n) (shift the rest)", "O(1) (relink 2 pointers)", "O(log n)"),
            ("iterator category", "random access (<code>it + 5</code>)", "bidirectional (<code>++</code>/<code>--</code>)",
             "bidirectional")]
    table = ("<table><tr><th>operation</th><th>vector</th><th>list</th><th>set</th></tr>" +
             "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td><td>{d}</td></tr>" for a, b, c, d in rows) + "</table>")
    body = (PAGE_CSS + "<h1>Where the data lives: vector vs list vs set</h1>"
            "<p class='keybox'><b>Block → jump (random access).</b> <b>Nodes → walk (bidirectional).</b> "
            "<b>Tree → halve each step (log n).</b></p>"
            f"<h2>vector</h2><div class='pic'>{vec_svg}</div>"
            f"<h2>list</h2><div class='pic'>{list_svg}</div>"
            "<h2>set</h2><p class='muted'>a balanced binary search TREE of nodes (kept sorted, no duplicates): each "
            "step goes left or right, halving what is left → O(log n)</p>"
            f"<div class='pic'>{set_svg}</div>"
            f"<h2>What that means for the costs</h2>{table}")
    return "memory", "vector vs list vs set", body


# ------------------------------------------------------------------ one erase: shift vs unlink

def erase(values, at):
    if not 0 <= at < len(values):
        raise ValueError(f"--at must be an index 0..{len(values) - 1}")
    after = values[:at] + values[at + 1:]
    x0, yb, ya = 20, 50, 170
    p = [text(x0, 22, f"vector: erase(v.begin() + {at})  removes {values[at]}", "b")]
    p += vec_row(values, x0, yb, colors={at: "red"})
    p += vec_row(after, x0, ya, colors={k: "amber" for k in range(at, len(after))})
    for k in range(at, len(after)):
        p.append(arrow(x0 + (k + 1) * CW + CW / 2, yb + CH + 20, x0 + k * CW + CW / 2, ya - 4, color="amber",
                       curve=30, vertical=True))
    n_shift = len(after) - at
    p.append(text(x0, ya + CH + 40, f"{n_shift} element(s) shifted one slot LEFT  →  O(n) per erase", "t", color="amber"))
    p.append(text(x0, ya + CH + 60, "every iterator at or after the erased slot is now invalid", "s"))
    vec_svg = svg(x0 * 2 + (len(values) + 1) * CW + 60, ya + CH + 72, p)

    step = NW + NGAP
    p = [text(x0, 22, f"list: L.erase(it)  removes {values[at]}", "b")]
    p += list_row(values, x0, 50, colors={at: "red"})
    # after: node lifted out, neighbours linked directly
    y2 = 190
    for i, v in enumerate(values):
        x = x0 + i * step
        if i == at:
            p.append(rect(x, y2 + 50, NW, CH, color="grey", dash=True, rx=8))
            p.append(text(x + NW / 2, y2 + 50 + CH / 2 + 5, v, "m", color="grey"))
            p.append(text(x + NW / 2, y2 + 50 + CH + 16, "deleted", "s", anchor="middle"))
            continue
        p.append(rect(x, y2, NW, CH, rx=8))
        p.append(text(x + NW / 2, y2 + CH / 2 + 5, v, "m"))
        nxt = i + 1 if i + 1 != at else i + 2
        if nxt < len(values):
            if nxt == i + 2:
                xa, xb = x + NW / 2, x0 + nxt * step + NW / 2
                p.append(f"<path d='M{xa},{y2 - 2} C{xa},{y2 - 46} {xb},{y2 - 46} {xb},{y2 - 2}' class='ln' "
                         f"style='stroke:{C['green']}' marker-end='url(#ah-green)' marker-start='url(#ah-green)'/>")
            else:
                p.append(arrow(x + NW + 2, y2 + CH / 2, x + step - 2, y2 + CH / 2, both=True))
    p.append(text(x0, y2 + 130, "only the two neighbours' pointers change (green)  →  O(1); nothing moves", "t", color="green"))
    p.append(text(x0, y2 + 150, "only iterators to the deleted node become invalid", "s"))
    list_svg = svg(x0 * 2 + (len(values) + 1) * step + 20, y2 + 160, p)
    body = (PAGE_CSS + f"<h1>One erase: vector vs list</h1>"
            "<p class='keybox'><b>vector erase = O(n)</b> (shift the rest left). <b>list erase = O(1)</b> (relink two "
            "pointers). So erasing k items in a loop: vector O(n·k) → up to O(n²); list O(n).</p>"
            f"<h2>vector</h2><div class='pic'>{vec_svg}</div><h2>list</h2><div class='pic'>{list_svg}</div>")
    return f"erase-{at}", "vector vs list erase", body


# ------------------------------------------------------------------ erase-in-loop step-through

def _vec_pic(v, i, colors=None, past=False, extra_ptr=None):
    x0, y0 = 20, 50
    p = vec_row(v, x0, y0, colors=colors)
    if past:  # a garbage cell after end(): memory that is not part of the vector
        x = x0 + (len(v) + 1) * CW
        p.append(rect(x, y0, CW, CH, color="red", dash=True, rx=0))
        p.append(text(x + CW / 2, y0 + CH / 2 + 5, "??", "m", color="red"))
        p.append(text(x + CW / 2, y0 + CH + 16, "not yours", "s", anchor="middle", color="red"))
    p += pointer(x0, y0, i, color="red" if past else "blue")
    if extra_ptr:
        p += pointer(x0, y0, extra_ptr[0], label=extra_ptr[1], color="green", below=True)
    return svg(x0 * 2 + (len(v) + 3) * CW, y0 + CH + 76, p)


def _list_pic(v, i, colors=None, freed=None, chase=False):
    """freed = (value, slot): draw the deleted node below the row; `it` points at it if i is None."""
    x0, y0 = 20, 50
    p = list_row(v, x0, y0, colors=colors)
    step = NW + NGAP
    h = y0 + CH + 30
    if freed is not None:
        val, slot = freed
        fx, fy = x0 + slot * step - step / 2, y0 + CH + 50
        p.append(rect(fx, fy, NW, CH, color="red", dash=True, rx=8))
        p.append(text(fx + NW / 2, fy + CH / 2 + 5, val, "m", color="grey"))
        p.append(text(fx + NW + 8, fy + CH / 2 + 5, "freed memory", "s", color="red"))
        h = fy + CH + 20
        if i is None:
            cx = fx + NW / 2
            p.append(text(cx - 60, fy + CH / 2 + 5, "it", "b", color="red"))
            p.append(arrow(cx - 44, fy + CH / 2, fx - 3, fy + CH / 2, color="red"))
        if chase:  # ++it follows the freed node's next pointer into nowhere
            p.append(arrow(fx + NW / 2, fy + CH + 2, fx + NW / 2 + 60, fy + CH + 40, color="red", dash=True))
            p.append(text(fx + NW / 2 + 68, fy + CH + 46, "next = ???  (garbage)", "t", color="red", size=13))
            h = fy + CH + 60
    if i is not None:
        p += list_pointer(x0, y0, i)
    return svg(x0 * 2 + (len(v) + 2) * step, h, p)


def erase_loop(values, spec="odd", container="vector", fixed=False):
    pred, desc = make_pred(spec)
    name = "nums" if container == "vector" else "L"
    if fixed:
        code = (f"for (auto it = {name}.begin(); it != {name}.end(); ) {{\n"
                f"    if (/* *it is {desc} */)\n        it = {name}.erase(it);   // erase returns the NEXT element\n"
                f"    else\n        ++it;                    // advance ONLY when nothing was erased\n}}")
    else:
        code = (f"for (auto it = {name}.begin(); it != {name}.end(); ++it) {{   // ++it runs EVERY time\n"
                f"    if (/* *it is {desc} */)\n        {name}.erase(it);          // it is now INVALID\n}}")
    expected = [x for x in values if not pred(x)]
    frames = []
    v = list(values)
    if container == "vector":
        i = 0
        frames.append(("Start", _vec_pic(v, 0), f"Remove every <b>{desc}</b> number. <code>it</code> starts at "
                                                f"<code>begin()</code>."))
        for _ in range(60):
            if i == len(v):
                frames.append(("it == end(): the loop stops", _vec_pic(v, i), "The loop condition is false."))
                break
            if i > len(v):
                frames.append(("it went PAST end()", _vec_pic(v, i, past=True),
                               "<code>it</code> stepped over <code>end()</code>, so <code>it != end()</code> is never "
                               "false. The loop keeps reading memory after the array: <b>crash or garbage "
                               "(undefined behaviour)</b>."))
                v = None
                break
            x = v[i]
            if pred(x):
                frames.append((f"*it is {x}: erase it", _vec_pic(v, i, {i: "red"}),
                               f"{x} is {desc}, so <code>{name}.erase(it)</code> runs."))
                del v[i]
                shifted = {k: "amber" for k in range(i, len(v))}
                nxt = v[i] if i < len(v) else "end()"
                if fixed:
                    frames.append(("it = erase(it)", _vec_pic(v, i, shifted),
                                   f"The {len(v) - i} element(s) after it shifted one slot LEFT (amber, O(n)). "
                                   f"<code>erase</code> returned an iterator to the next element (<b>{nxt}</b>) and we "
                                   f"do <b>not</b> <code>++it</code>, so nothing is skipped."))
                else:
                    frames.append(("after erase(it)", _vec_pic(v, i, shifted),
                                   f"The element(s) after it shifted one slot LEFT (amber). <code>it</code> is now "
                                   f"<b>invalidated</b>; in practice it still points at slot [{i}], which now holds "
                                   f"<b>{nxt}</b>."))
                    i += 1
                    if i - 1 < len(v):
                        skipped = v[i - 1]
                        frames.append(("++it skips an element", _vec_pic(v, i, {i - 1: "purple"}),
                                       f"The loop's <code>++it</code> jumps over <b>{skipped}</b> (purple): it is "
                                       f"never checked." + (f" {skipped} is {desc} too, so it <b>survives</b>!"
                                                            if pred(skipped) else
                                                            " It happens to be a keeper, so the bug is hidden here.")))
            else:
                frames.append((f"*it is {x}: keep it", _vec_pic(v, i, {i: "blue"}),
                               f"{x} is not {desc}: <code>++it</code>."))
                i += 1
    else:  # list
        i = 0
        frames.append(("Start", _list_pic(v, 0), f"Remove every <b>{desc}</b> number. Each element is a separate "
                                                 f"node."))
        for _ in range(60):
            if i == len(v):
                frames.append(("it == end(): the loop stops", _list_pic(v, i), "Done."))
                break
            x = v[i]
            if pred(x):
                frames.append((f"*it is {x}: erase it", _list_pic(v, i, {i: "red"}),
                               f"{x} is {desc}, so <code>L.erase(it)</code> runs."))
                del v[i]
                if fixed:
                    nxt = v[i] if i < len(v) else "end()"
                    frames.append(("it = erase(it)", _list_pic(v, i, freed=(x, i)),
                                   f"The node is deleted and its neighbours are relinked: O(1), nothing shifts. "
                                   f"<code>it</code> now holds the returned iterator to <b>{nxt}</b>; no "
                                   f"<code>++it</code>."))
                else:
                    frames.append(("after erase(it): it points at freed memory", _list_pic(v, None, freed=(x, i)),
                                   "The node was <b>deleted</b>. <code>it</code> still holds its address: it is "
                                   "<b>invalidated</b>."))
                    frames.append(("++it reads freed memory", _list_pic(v, None, freed=(x, i), chase=True),
                                   "<code>++it</code> follows the deleted node's <code>next</code> pointer, which lives "
                                   "in freed memory: <b>crash or garbage (undefined behaviour)</b>. Unlike the vector, "
                                   "there is no 'lucky' behaviour."))
                    v = None
                    break
            else:
                frames.append((f"*it is {x}: keep it", _list_pic(v, i, {i: "blue"}), f"{x} is not {desc}: <code>++it</code>."))
                i += 1
    if v is not None:
        ok = v == expected
        verdict = ("<b style='color:#2da44e'>Correct.</b>" if ok else
                   f"<b style='color:#cf222e'>WRONG:</b> should be {expected}, got {v}.")
        frames.append(("Result", _vec_pic(v, len(v)) if container == "vector" else _list_pic(v, len(v)),
                       f"Final contents {v}. {verdict}"))
    title = f"{'Fixed' if fixed else 'Buggy'} erase loop on a {container}"
    intro = f"<pre><code>{esc(code)}</code></pre>"
    name_ = f"eraseloop-{container}-{'fixed' if fixed else 'bug'}"
    return name_, title, frames_html(title, intro, frames)


# ------------------------------------------------------------------ overwriter (two iterators, O(n))

def overwriter(values, spec="odd"):
    pred, desc = make_pred(spec)
    v = list(values)
    ow = 0
    code = ("auto ow = nums.begin();                       // where the next keeper goes\n"
            "for (auto it = nums.begin(); it != nums.end(); ++it)\n"
            f"    if (!(/* *it is {desc} */)) {{ *ow = *it; ++ow; }}   // copy keepers forward\n"
            "nums.erase(ow, nums.end());                   // ONE erase chops the tail")
    frames = [("Start", _vec_pic(v, 0, extra_ptr=(0, "ow")),
               "Both start at the front. <code>it</code> (blue, above) reads every element; <code>ow</code> "
               "(green, below) marks where the next keeper is written.")]
    for i in range(len(v)):
        x = v[i]
        if not pred(x):
            v[ow] = x
            frames.append((f"keep {x}", _vec_pic(v, i, {ow: "green", i: "blue"}, extra_ptr=(ow + 1, "ow")),
                           f"{x} is a keeper: write it at slot [{ow}], then <code>++ow</code>." +
                           (" (Same slot, so it just stays.)" if ow == i else "")))
            ow += 1
        else:
            frames.append((f"skip {x}", _vec_pic(v, i, {i: "red"}, extra_ptr=(ow, "ow")),
                           f"{x} is {desc}: skip it; <code>ow</code> stays."))
    tail = {k: "grey" for k in range(ow, len(v))}
    frames.append(("erase(ow, end()): chop the tail once", _vec_pic(v, len(v), tail, extra_ptr=(ow, "ow")),
                   f"Slots [{ow}..{len(v) - 1}] are leftovers. One range erase removes them (nothing after them to "
                   f"shift)."))
    frames.append(("Result", _vec_pic(v[:ow], ow), f"{v[:ow]}: one pass + one erase = <b>O(n)</b>, instead of O(n²) "
                                                   f"for erase-in-a-loop."))
    title = "Overwriter: remove from a vector in O(n)"
    return "overwriter", title, frames_html(title, f"<pre><code>{esc(code)}</code></pre>", frames)


# ------------------------------------------------------------------ move semantics: objects, pointers, heap

PRIMS = {"int", "double", "float", "char", "bool", "long", "short", "size_t", "unsigned", "unsigned int"}
DEFAULT_MEMBERS = "syllabus_:std::string,roster_:std::vector<Student>,courseNumber_:int,gradeData_:int*[]"


def parse_members(spec):
    parts, depth, cur = [], 0, ""
    for ch in spec or DEFAULT_MEMBERS:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    out = []
    for p in parts:
        name, typ = (s.strip() for s in p.split(":", 1))
        if typ.endswith("[]"):
            kind, base = "array", typ[:-2].rstrip("*").strip()
        elif typ.endswith("*"):
            kind, base = "single", typ[:-1].strip()
        elif typ in PRIMS:
            kind, base = "prim", typ
        else:
            kind, base = "nested", typ
        out.append({"name": name, "type": typ, "kind": kind, "base": base})
    return out


def _type_label(m):
    if m["kind"] == "array":
        return f"{m['base']}*  (array)"
    if m["kind"] == "single":
        return f"{m['base']}*  (one object)"
    return m["type"]


def _block_label(m, owner):
    short = m["base"].replace("std::", "")
    if m["kind"] == "nested":
        what = "characters" if "string" in short else ("elements" if "<" in short else "data")
        return f"{owner}'s {m['name']} {what}"
    if m["kind"] == "array":
        return f"{owner}'s {short}[ ] array"
    return f"{owner}'s {short} object"


def _render_move(objects, blocks, notes=None):
    """objects: [(title, [(member, state)])], state = ('val', s) | ('ptr', bid, color) | ('null',) | ('empty',) | ('unset',)
    blocks: {bid: (label, status)}, status in ok|new|copy|leak|double|freed|dangling."""
    notes = notes or {}
    LBL_W, VAL_W, ROW = 200, 100, 34
    ox = 20
    hx = ox + LBL_W + VAL_W + 110
    BW, BH = 230, 30
    p, anchors = [], []
    y = 30
    for title, fields in objects:
        p.append(text(ox, y, title, "b"))
        y += 10
        p.append(rect(ox, y, LBL_W + VAL_W, ROW * len(fields), rx=6))
        for r, (m, st) in enumerate(fields):
            ry = y + r * ROW
            if r:
                p.append(f"<line x1='{ox}' y1='{ry}' x2='{ox + LBL_W + VAL_W}' y2='{ry}' class='ln' style='opacity:.3'/>")
            p.append(text(ox + 8, ry + 15, m["name"], "t", weight="600"))
            p.append(text(ox + 8, ry + 29, _type_label(m), "s"))
            vx = ox + LBL_W
            p.append(f"<line x1='{vx}' y1='{ry}' x2='{vx}' y2='{ry + ROW}' class='ln' style='opacity:.3'/>")
            cx, cy = vx + VAL_W / 2, ry + ROW / 2 + 5
            kind = st[0]
            if kind == "val":
                p.append(text(cx, cy, st[1], "m", color=st[2] if len(st) > 2 else None))
            elif kind == "ptr":
                p.append(f"<circle cx='{cx}' cy='{ry + ROW / 2}' r='5' style='fill:{C.get(st[2], 'currentColor')}'/>")
                anchors.append((cx + 6, ry + ROW / 2, st[1], st[2]))
            elif kind == "null":
                p.append(text(cx, cy, "nullptr", "m", color="green"))
            elif kind == "empty":
                p.append(text(cx, cy, "(empty)", "m", color="grey"))
            else:
                p.append(text(cx, cy, "?", "m", color="grey"))
        y += ROW * len(fields) + 40
    obj_h = y
    # heap blocks
    p.append(text(hx, 30, "HEAP (dynamically allocated memory)", "b"))
    pos = {}
    by = 50
    for bid, (label, status) in blocks.items():
        col = {"ok": None, "new": "green", "copy": "amber", "leak": "red", "double": "red", "freed": "grey",
               "dangling": "red"}[status]
        p.append(rect(hx, by, BW, BH, color=col, fill=col if status in ("copy", "leak", "double", "new") else None,
                      dash=status in ("freed", "dangling"), rx=3, width=2.2 if col else None))
        p.append(text(hx + 8, by + 20, label, "t", color="grey" if status == "freed" else None, size=13))
        note = notes.get(bid) or {"copy": "new COPY: O(size)", "leak": "LEAK: nobody points here",
                                  "double": "2 owners → double delete", "freed": "freed",
                                  "dangling": "freed, but still pointed to!"}.get(status)
        if note:
            p.append(text(hx + BW + 8, by + 20, note, "t", color=col or "grey", size=13, weight="600"))
        pos[bid] = by + BH / 2
        by += BH + 22
    for x1, y1, bid, color in anchors:
        if bid in pos:
            p.append(arrow(x1, y1, hx - 3, pos[bid], color=color if color in C else None, curve=70))
    return svg(hx + BW + 260, max(obj_h, by + 20), p)


def move(op="ctor", members_spec=None, cls="AlgorithmsCourse"):
    ms = parse_members(members_spec)
    ptrs = [m for m in ms if m["kind"] in ("array", "single")]
    nested = [m for m in ms if m["kind"] == "nested"]

    def bid(owner, m):
        return f"{owner}:{m['name']}"

    def prim_val(m, owner):
        base = {"int": 335, "double": 3.5, "bool": "true", "char": "'A'"}.get(m["base"], 7)
        return str(base if owner == "rhs" else ({"int": 101}.get(m["base"], 0)))

    def full(owner, color=None):
        out = []
        for m in ms:
            if m["kind"] == "prim":
                out.append((m, ("val", prim_val(m, owner))))
            else:
                out.append((m, ("ptr", bid(owner, m), color)))
        return out

    def blocks_of(owner, status="ok"):
        return {bid(owner, m): (_block_label(m, owner), status) for m in ms if m["kind"] != "prim"}

    frames = []
    is_assign = op.startswith("assign") or op == "self"
    if op == "self":
        target = ptrs[0] if ptrs else None
        if target is None:
            raise ValueError("self-assignment demo needs a pointer member")
        d = "delete[]" if target["kind"] == "array" else "delete"
        fa = full("a")
        bl = blocks_of("a")
        frames.append(("Before: a = std::move(a)", _render_move([("a  (this and rhs are the SAME object)", fa)], bl),
                       "With no <code>if (this != &rhs)</code> check, the body runs on one object."))
        b2 = dict(bl)
        b2[bid("a", target)] = (bl[bid("a", target)][0], "dangling")
        f2 = [(m, ("ptr", s[1], "red") if m is target else s) for m, s in fa]
        frames.append((f"{d} {target['name']};", _render_move([("a", f2)], b2),
                       f"The object frees its OWN {target['name']}... which is also rhs's."))
        frames.append((f"{target['name']} = rhs.{target['name']};", _render_move([("a", f2)], b2),
                       "Copies the same (now dangling) address back into itself."))
        f4 = [(m, ("null",) if m is target else s) for m, s in fa]
        b4 = dict(bl)
        b4[bid("a", target)] = (bl[bid("a", target)][0], "freed")
        frames.append((f"rhs.{target['name']} = nullptr;", _render_move([("a", f4)], b4),
                       f"rhs <b>is</b> a, so a's own pointer becomes nullptr: <b>a has lost its data</b>. "
                       f"That is why move assignment starts with <code>if (this != &rhs)</code>."))
        title = "Self-move without the check"
        return "move-self", title, frames_html(title, "", frames)

    # before
    this_before = full("this") if is_assign else [(m, ("unset",)) for m in ms]
    blocks = (blocks_of("this") if is_assign else {})
    blocks.update(blocks_of("rhs"))
    title_this = "this  (already exists, owns its own data)" if is_assign else "this  (being constructed, empty)"
    frames.append(("Before", _render_move([(title_this, this_before), ("rhs", full("rhs"))], blocks),
                   ("<code>this</code> already owns data, which must not leak." if is_assign else
                    "The new object has nothing yet.") + " <code>rhs</code> owns the heap data on the right."))

    # after
    this_after, rhs_after = [], []
    b = {}
    notes = {}
    if is_assign:
        for m in nested:
            b[bid("this", m)] = (_block_label(m, "old this"), "freed")
            notes[bid("this", m)] = f"freed by {m['base'].replace('std::', '').split('<')[0]}'s own move="
        for m in ptrs:
            d = "delete[]" if m["kind"] == "array" else "delete"
            if op == "assign-no-delete":
                b[bid("this", m)] = (_block_label(m, "old this"), "leak")
            else:
                b[bid("this", m)] = (_block_label(m, "old this"), "freed")
                notes[bid("this", m)] = f"freed by YOUR {d} {m['name']};"
    for m in ms:
        k = m["kind"]
        if k == "prim":
            this_after.append((m, ("val", prim_val(m, "rhs"), "green")))
            rhs_after.append((m, ("val", prim_val(m, "rhs"))))
        elif k == "nested":
            if op == "ctor-copy":
                cid = f"copy:{m['name']}"
                b[cid] = (f"copy of {m['name']} data", "copy")
                this_after.append((m, ("ptr", cid, "amber")))
                rhs_after.append((m, ("ptr", bid("rhs", m), None)))
            else:
                this_after.append((m, ("ptr", bid("rhs", m), "green")))
                rhs_after.append((m, ("empty",)))
        else:
            this_after.append((m, ("ptr", bid("rhs", m), "red" if op == "ctor-no-null" else "green")))
            rhs_after.append((m, ("ptr", bid("rhs", m), "red") if op == "ctor-no-null" else ("null",)))
    for m in ms:
        if m["kind"] == "prim":
            continue
        if op == "ctor-copy" and m["kind"] == "nested":
            b[bid("rhs", m)] = (_block_label(m, "rhs"), "ok")
        elif op == "ctor-no-null" and m["kind"] != "nested":
            b[bid("rhs", m)] = (_block_label(m, "rhs") + " (now shared)", "double")
        else:
            b[bid("rhs", m)] = (_block_label(m, "rhs").replace("rhs's", "now this's"), "new")
            notes[bid("rhs", m)] = "moved: pointer copied, O(1)"
    explain = {
        "ctor": "Ints were copied, every pointer was copied (green), nested objects moved themselves with "
                "<code>std::move</code>, and rhs's raw pointers are <code>nullptr</code>, so rhs's destructor frees "
                "nothing. Total cost <b>O(1)</b>, however big the data is.",
        "ctor-copy": "Without <code>std::move</code> on the nested objects, <code>rhs.x_</code> is an lvalue (it has a "
                     "name), so the <b>copy</b> constructor ran: brand-new copies (amber), <b>O(size)</b>. The move "
                     "was pointless for those members.",
        "ctor-no-null": "Forgot <code>rhs.ptr = nullptr;</code>: two objects own the same array (red). When rhs is "
                        "destroyed it frees it, this is left pointing at freed memory, and when this is destroyed "
                        "it is freed <b>again</b>: <b>double delete, crash</b>.",
        "assign": "Same as the constructor, plus: the old nested data was freed by their own move assignments, and "
                  "the old raw-pointer data was freed by <b>your</b> <code>delete</code>/<code>delete[]</code> before "
                  "the pointer was overwritten. Then <code>return *this;</code>.",
        "assign-no-delete": "Overwrote the pointer without deleting first: the old block (red) has no owner any more: "
                            "a <b>memory leak</b>. Free every owning pointer first (<code>delete[]</code> for arrays, "
                            "<code>delete</code> for single objects).",
    }[op]
    frames.append(("After", _render_move([("this", this_after), ("rhs  (moved-from)", rhs_after)], b, notes), explain))
    if op == "ctor-no-null":
        b3 = {k: (lbl, "dangling" if st == "double" else st) for k, (lbl, st) in b.items()}
        frames.append(("Then rhs is destroyed", _render_move([("this", this_after)], b3),
                       "rhs's destructor ran <code>delete[]</code> on the shared array. <code>this</code> now points at "
                       "freed memory; its own destructor will free it a second time."))
    code = _move_code(cls, ms, op)
    title = {"ctor": "Move constructor", "ctor-copy": "Move constructor without std::move on objects",
             "ctor-no-null": "Move constructor that forgets nullptr", "assign": "Move assignment",
             "assign-no-delete": "Move assignment that forgets delete"}[op]
    return f"move-{op}", title, frames_html(title, f"<pre><code>{esc(code)}</code></pre>", frames)


def _move_code(cls, ms, op):
    lines = []
    assign = op.startswith("assign")
    if assign:
        lines.append(f"{cls}& {cls}::operator=({cls}&& rhs) {{")
        lines.append("    if (this != &rhs) {")
        ind = "        "
    else:
        lines.append(f"{cls}::{cls}({cls}&& rhs) {{")
        ind = "    "
    for m in ms:
        n = m["name"]
        if m["kind"] == "prim":
            lines.append(f"{ind}{n} = rhs.{n};                 // primitive: copy")
        elif m["kind"] == "nested":
            if op == "ctor-copy":
                lines.append(f"{ind}{n} = rhs.{n};                 // WRONG: copies (rhs.{n} is an lvalue)")
            else:
                lines.append(f"{ind}{n} = std::move(rhs.{n});      // object: its own move")
        else:
            if assign and op != "assign-no-delete":
                d = "delete[]" if m["kind"] == "array" else "delete"
                lines.append(f"{ind}{d} {n};                   // free MY old data first")
            elif op == "assign-no-delete":
                lines.append(f"{ind}// (missing: delete the old {n})")
            lines.append(f"{ind}{n} = rhs.{n};                 // pointer: copy the address")
            if op == "ctor-no-null":
                lines.append(f"{ind}// (missing: rhs.{n} = nullptr;)")
            else:
                lines.append(f"{ind}rhs.{n} = nullptr;            // source must not free it")
    if assign:
        lines.append("    }")
        lines.append("    return *this;")
    lines.append("}")
    has_cmt = [l for l in lines if "//" in l and not l.strip().startswith("//")]
    col = max((len(l.split("//")[0].rstrip()) for l in has_cmt), default=0) + 3
    return "\n".join(l.split("//")[0].rstrip().ljust(col) + "//" + l.split("//", 1)[1] if l in has_cmt else l
                     for l in lines)


# ------------------------------------------------------------------ Big-O loops as dot grids

LOOP_CODE = {
    "linear": ("for (i = 0; i < n; ++i)\n    ++sum;", lambda n: n, "n"),
    "square": ("for (i = 0; i < n; ++i)\n    for (j = 0; j < n; ++j)\n        ++sum;", lambda n: n * n, "n²"),
    "triangle": ("for (i = 0; i < n; ++i)\n    for (j = 0; j < i; ++j)\n        ++sum;",
                 lambda n: n * (n - 1) // 2, "0+1+…+(n−1) = n(n−1)/2 → O(n²), half of the square"),
    "log": ("for (i = 1; i < n; i *= 2)\n    ++sum;", lambda n: max(0, math.ceil(math.log2(n))) if n > 1 else 0,
            "log₂ n (i doubles each time)"),
    "nlogn": ("for (i = 0; i < n; ++i)\n    for (j = 1; j < n; j *= 2)\n        ++sum;",
              lambda n: n * (math.ceil(math.log2(n)) if n > 1 else 0), "n · log₂ n"),
    "cubic": ("for (i = 0; i < n; ++i)\n    for (j = 0; j < n * n; ++j)\n        ++sum;", lambda n: n ** 3, "n · n² = n³"),
}


def _dots(kind, n):
    R, S = 5, 17
    p = []
    x0, y0 = 30, 26
    if kind == "linear":
        for i in range(n):
            p.append(f"<circle cx='{x0 + i * S}' cy='{y0 + 10}' r='{R}' style='fill:{C['blue']}'/>")
        p.append(text(x0 - 8, y0 + 40, "one dot per ++sum", "s"))
        return svg(x0 * 2 + n * S, y0 + 52, p)
    if kind == "log":
        W = 26
        for v in range(1, n + 1):
            p.append(text(x0 + (v - 1) * W, y0 + 44, v, "s", anchor="middle"))
        p.append(f"<line x1='{x0}' y1='{y0 + 26}' x2='{x0 + (n - 1) * W}' y2='{y0 + 26}' class='ln' style='opacity:.4'/>")
        v = 1
        while v < n:
            p.append(f"<circle cx='{x0 + (v - 1) * W}' cy='{y0 + 26}' r='{R + 1}' style='fill:{C['blue']}'/>")
            if v * 2 < n:
                a, b2 = x0 + (v - 1) * W, x0 + (2 * v - 1) * W
                p.append(f"<path d='M{a},{y0 + 18} Q{(a + b2) / 2},{y0 - 14} {b2},{y0 + 18}' class='ln' "
                         f"style='stroke:{C['blue']}' marker-end='url(#ah-blue)'/>")
            v *= 2
        return svg(x0 * 2 + n * W, y0 + 56, p)
    rows = n
    for i in range(rows):
        if kind == "square" or kind == "cubic":
            cols = n
        elif kind == "triangle":
            cols = i
        else:
            cols = math.ceil(math.log2(n)) if n > 1 else 0
        for j in range(n if kind in ("square", "triangle", "cubic") else cols):
            filled = j < cols
            col = C["blue"] if filled else "none"
            stroke = "" if filled else f";stroke:{C['grey']};stroke-dasharray:2 2"
            p.append(f"<circle cx='{x0 + j * S}' cy='{y0 + i * S}' r='{R}' style='fill:{col}{stroke}'/>")
        p.append(text(6, y0 + i * S + 4, f"i={i}", "s", size=10))
    p.append(text(x0, y0 + rows * S + 12, "row = one outer iteration, dot = one ++sum (hollow = not run)", "s"))
    return svg(max(x0 * 2 + n * S + 20, 440), y0 + rows * S + 24, p)


def loops(kinds=None, n=8):
    kinds = kinds or ["linear", "log", "nlogn", "triangle", "square"]
    body = [PAGE_CSS, "<h1>Counting loop steps (Big-O)</h1>",
            "<p class='keybox'>Count how many times the innermost line runs. <b>Nested loops multiply, one-after-another "
            "loops add.</b> log n appears <b>only</b> when the loop variable is multiplied or divided "
            "(<code>i *= 2</code>, <code>i /= 2</code>).</p>"]
    for k in kinds:
        code, f, formula = LOOP_CODE[k]
        pic = _dots(k, n) if k != "cubic" else "<p class='muted'>(n blocks of n² dots each: too many to draw)</p>"
        body.append(f"<h2>{esc(k)}: {esc(formula)}</h2><pre><code>{esc(code)}</code></pre>"
                    f"<p>n = {n}: <b>{f(n)}</b> steps.</p><div class='pic'>{pic}</div>")
    ns = [10, 100, 1000, 10 ** 6]
    rows = "".join(f"<tr><td>{esc(LOOP_CODE[k][2])}</td>" + "".join(f"<td>{LOOP_CODE[k][1](v):,}</td>" for v in ns)
                   + "</tr>" for k in ["log", "linear", "nlogn", "triangle", "square", "cubic"])
    body.append("<h2>How fast they grow</h2><table><tr><th>steps</th>" + "".join(f"<th>n = {v:,}</th>" for v in ns)
                + f"</tr>{rows}</table>")
    return "loops", "Big-O loop counting", "\n".join(body)


# ------------------------------------------------------------------ iterator categories

def iterators():
    x0 = 20
    p = [text(x0, 22, "random access (vector): it + 3 jumps straight there, O(1)", "b")]
    vals = [10, 20, 30, 40, 50, 60]
    p += vec_row(vals, x0, 50, colors={0: "blue", 3: "green"})
    p.append(f"<path d='M{x0 + CW / 2},{48} Q{x0 + 2 * CW},{4} {x0 + 3 * CW + CW / 2},{48}' class='ln' "
             f"style='stroke:{C['green']}' marker-end='url(#ah-green)'/>")
    p.append(text(x0 + 2 * CW, 18 + 2, "", "s"))
    jump = svg(x0 * 2 + 8 * CW, 120, p)
    p = [text(x0, 22, "bidirectional (list, set, map): only ++ and --, so 'it + 3' means walking 3 steps, O(n)", "b")]
    p += list_row(vals, x0, 50, colors={0: "blue", 3: "green"}, end=False)
    step = NW + NGAP
    for k in range(3):
        a, b2 = x0 + k * step + NW / 2, x0 + (k + 1) * step + NW / 2
        p.append(f"<path d='M{a},{100} Q{(a + b2) / 2},{122} {b2},{100}' class='ln' style='stroke:{C['amber']}' "
                 f"marker-end='url(#ah-amber)'/>")
        p.append(text((a + b2) / 2, 136, "++", "s", anchor="middle", color="amber"))
    walk = svg(x0 * 2 + 7 * step, 148, p)
    ladder = [("input", "read once, ++, ==, !=", "(istream iterators)"),
              ("forward", "+ multi-pass", "forward_list"),
              ("bidirectional", "+ --", "list, set, map"),
              ("random access", "+ it+n, it−n, it[n], it2−it1, <, >", "vector, deque, array")]
    p = []
    for k, (name, adds, who) in enumerate(ladder):
        y = 20 + k * 52
        x = 20 + k * 40
        p.append(rect(x, y, 230, 38, color="blue", fill="blue", rx=6))
        p.append(text(x + 10, y + 24, name, "b"))
        p.append(text(x + 245, y + 17, adds, "t", size=13))
        p.append(text(x + 245, y + 33, who, "s"))
    ladder_svg = svg(760, 20 + 4 * 52 + 10, p)
    body = (PAGE_CSS + "<h1>Iterator categories</h1>"
            "<p class='keybox'><b>Contiguous block → random access. Separate nodes (chain or tree) → bidirectional.</b> "
            "Each category can do everything the one above it can (output iterators are a separate write-only "
            "branch).</p>"
            f"<div class='pic'>{ladder_svg}</div><h2>Jump vs walk</h2><div class='pic'>{jump}</div>"
            f"<div class='pic'>{walk}</div>"
            "<h2>Why std::sort(L.begin(), L.end()) fails on a list</h2>"
            "<p><code>std::sort</code> jumps to positions (<code>first + n</code>, <code>last - first</code>) and "
            "compares iterators with <code>&lt;</code>: those need <b>random access</b>. A list iterator is only "
            "bidirectional, so it does not compile. <code>L.sort()</code> is the list's own merge sort that relinks "
            "nodes: <b>O(n log n)</b>, like every comparison sort.</p>")
    return "iterators", "Iterator categories", body


# ------------------------------------------------------------------ STL cost sheet

def costs():
    rows = [
        ("vector", "v[k], v.at(k)", "O(1)", "ok", "block: address = start + k"),
        ("vector", "push_back / pop_back", "amortized O(1)", "ok", "free slot at the end; rare doubling copies all, averages out"),
        ("vector", "insert / erase in the middle or front", "O(n)", "bad", "every later element shifts one slot"),
        ("vector", "std::find(v.begin(), v.end(), x)", "O(n)", "bad", "walks the block from the start"),
        ("vector", "erase-in-a-loop removing k items", "O(n·k), up to O(n²)", "bad", "each erase shifts the rest"),
        ("list", "push_front / push_back / pop_*", "O(1)", "ok", "relink pointers at an end"),
        ("list", "insert / erase given an iterator", "O(1)", "ok", "relink the two neighbours"),
        ("list", "reach element k / std::find", "O(n)", "bad", "follow next pointers one by one"),
        ("list", "L.sort()", "O(n log n)", "mid", "merge sort; every comparison sort is n log n"),
        ("set", "insert / erase / find / count", "O(log n)", "mid", "balanced tree: halve each step"),
        ("set", "lower_bound / upper_bound (member)", "O(log n)", "mid", "same tree walk"),
        ("set", "walk m elements with ++", "O(m)", "ok", "after one log n search: O(log n + m)"),
        ("map", "insert / erase / find / operator[]", "O(log n)", "mid", "a set of (key, value) pairs: same tree"),
        ("unordered_set/map", "insert / erase / find / count / operator[]", "avg O(1), worst O(n)", "ok",
         "hash to a bucket, scan its short list; all keys in one bucket = n"),
        ("unordered_set/map", "iterate all elements", "O(n)", "ok", "visits every bucket + element (no order!)"),
        ("unordered_set/map", "insert that triggers a rehash", "O(n) once, amortized O(1)", "mid",
         "table doubles to the next prime; every element re-hashed"),
        ("unordered_set/map", "min / max / range / sorted order", "O(n) (or sort: n log n)", "bad",
         "hashes are unordered: no lower_bound, no begin() = smallest"),
        ("priority_queue", "push", "O(log n) worst, O(1) avg", "mid", "percolate up a complete tree"),
        ("priority_queue", "pop (deleteMax)", "O(log n)", "mid", "percolate down from the root"),
        ("priority_queue", "top", "O(1)", "ok", "the root, index 0/1"),
        ("binary heap", "buildHeap / make_heap of n items", "O(n)", "ok", "sum of node heights is < n"),
        ("binary heap", "find / remove an arbitrary value", "O(n)", "bad", "heap order says nothing about siblings"),
        ("any", "std::sort", "O(n log n)", "mid", "introsort; needs random-access iterators (vector, not list)"),
        ("sort", "insertion sort", "O(n²) worst/avg, O(n) sorted", "bad", "one shift per inversion"),
        ("sort", "mergesort", "O(n log n) always, O(n) extra space", "mid", "log n levels × O(n) merge per level"),
        ("sort", "heapsort", "O(n log n) always, in place", "mid", "buildHeap O(n) + n deleteMax × O(log n)"),
        ("sort", "quicksort", "avg O(n log n), worst O(n²)", "mid", "worst = pivot always min/max (bad pivot choice)"),
        ("select", "quickselect (k-th smallest)", "avg O(n), worst O(n²)", "ok", "recurse into ONE side only"),
        ("select", "heap selection: buildHeap + k deleteMin", "O(n + k log n)", "mid", "median: O(n log n)"),
    ]
    tr = "".join(f"<tr><td>{c}</td><td><code>{esc(op)}</code></td><td class='{cls}'>{esc(cost)}</td><td>{esc(why)}</td></tr>"
                 for c, op, cost, cls, why in rows)
    body = (PAGE_CSS + "<h1>Cost sheet: STL containers, heaps, sorts</h1>"
            "<p class='keybox'><b>Block → jump O(1), shift O(n).</b> <b>Nodes → relink O(1), walk O(n).</b> "
            "<b>Tree → O(log n).</b> <b>Hash → O(1) average, O(n) worst.</b> <b>Heap → O(log n) per push/pop, "
            "O(n) to build.</b> <b>Sort → O(n log n).</b></p>"
            f"<table><tr><th>container</th><th>operation</th><th>cost</th><th>why (picture it)</th></tr>{tr}</table>"
            "<p class='muted'>Pictures: <code>study viz memory 7,2,5,9,4</code> · <code>study viz erase 7,2,5,9,4 "
            "--at 1</code></p>")
    return "costs", "STL cost sheet", body


# ------------------------------------------------------------------ plain BST walk

def bst(tree_text, op, x):
    t = avl.parse(tree_text)
    path, n = [], t
    while n is not None:
        path.append(n.key)
        if x == n.key:
            break
        n = n.left if x < n.key else n.right
    steps = []
    n = t
    while n is not None and n.key != x:
        steps.append(f"{x} {'&lt;' if x < n.key else '&gt;'} {n.key} → go {'left' if x < n.key else 'right'}")
        n = n.left if x < n.key else n.right
    frames = [("Start", avl.svg(t, {k: "path" for k in path if k != x} | ({x: "target"} if op == "remove" else {}),
                                show_balance=False),
               "Compare at every node, starting at the root: " + "; ".join(steps) + ".")]
    if op == "insert":
        t2 = avl.bst_insert_only(t, x)
        frames.append((f"After inserting {x}", avl.svg(t2, {**{k: "path" for k in path}, x: "new"}, show_balance=False),
                       f"{x} becomes a new leaf where the walk fell off the tree. No rebalancing in a plain BST."))
    else:
        node = avl.find(t, x)
        if node is None:
            raise ValueError(f"{x} is not in the tree")
        how = ("a leaf: just remove it" if not (node.left or node.right) else
               "one child: the child moves up" if not (node.left and node.right) else
               f"two children: copy the smallest key of the right subtree ({avl.find_min(node.right).key}) into it, "
               f"then remove that key from the right subtree")
        t2 = avl.bst_remove_only(t, x)
        frames.append((f"After removing {x}", avl.svg(t2, show_balance=False), f"{x} has {how}."))
    title = f"BST {op} {x}"
    return f"bst-{op}-{x}", title, frames_html(title, "", frames)


# ------------------------------------------------------------------ your own snippet

def page(path, title=None):
    f = Path(path)
    raw = f.read_text(encoding="utf-8")
    if f.suffix == ".md":
        try:
            import markdown
            raw = markdown.markdown(raw, extensions=["tables", "fenced_code"])
        except ImportError:
            raw = f"<pre>{esc(raw)}</pre>"
    return f"page-{f.stem}", title or f.stem, PAGE_CSS + (f"<h1>{esc(title)}</h1>" if title else "") + raw
