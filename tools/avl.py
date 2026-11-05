"""AVL tree engine that follows the Weiss textbook (4th ed., section 4.4) exactly.

Conventions (same as the textbook and the professor):
  * height(nullptr) = -1, a single leaf has height 0
  * ALLOWED_IMBALANCE = 1
  * balance() is called on every node on the path back to the root
  * ties in balance() pick the SINGLE rotation (uses >=)
  * remove() with two children copies findMin(right subtree) into the node

Tree text notation (used for input and output):
    38(5(1,22(12,31)),56(,79))
  key, then optionally "(left,right)"; an empty side is left blank.
"""

import random
import re


class Node:
    __slots__ = ("key", "left", "right", "height")

    def __init__(self, key, left=None, right=None):
        self.key = key
        self.left = left
        self.right = right
        self.height = 0


def height(t):
    return -1 if t is None else t.height


def fix_height(t):
    t.height = max(height(t.left), height(t.right)) + 1


def fix_all_heights(t):
    if t is None:
        return -1
    t.height = max(fix_all_heights(t.left), fix_all_heights(t.right)) + 1
    return t.height


# ---------------------------------------------------------------- rotations
# Names use the professor's vocabulary:
#   left-left   -> single clockwise rotation         (textbook case 1, rotateWithLeftChild)
#   right-right -> single counter-clockwise rotation (textbook case 4, rotateWithRightChild)
#   left-right  -> double rotation                   (textbook case 2, doubleWithLeftChild)
#   right-left  -> double rotation                   (textbook case 3, doubleWithRightChild)

def rotate_with_left_child(k2):
    k1 = k2.left
    k2.left = k1.right
    k1.right = k2
    fix_height(k2)
    fix_height(k1)
    return k1


def rotate_with_right_child(k1):
    k2 = k1.right
    k1.right = k2.left
    k2.left = k1
    fix_height(k1)
    fix_height(k2)
    return k2


def double_with_left_child(k3):
    k3.left = rotate_with_right_child(k3.left)
    return rotate_with_left_child(k3)


def double_with_right_child(k1):
    k1.right = rotate_with_left_child(k1.right)
    return rotate_with_right_child(k1)


CASE_TEXT = {
    "left-left": "single rotation (clockwise), textbook rotateWithLeftChild",
    "right-right": "single rotation (counter-clockwise), textbook rotateWithRightChild",
    "left-right": "double rotation, textbook doubleWithLeftChild",
    "right-left": "double rotation, textbook doubleWithRightChild",
}


def balance(t, log):
    """Textbook balance(). Appends (key, case_or_None) to log for every node checked."""
    if t is None:
        return t
    key = t.key
    case = None
    if height(t.left) - height(t.right) > 1:
        if height(t.left.left) >= height(t.left.right):
            case, t = "left-left", rotate_with_left_child(t)
        else:
            case, t = "left-right", double_with_left_child(t)
    elif height(t.right) - height(t.left) > 1:
        if height(t.right.right) >= height(t.right.left):
            case, t = "right-right", rotate_with_right_child(t)
        else:
            case, t = "right-left", double_with_right_child(t)
    fix_height(t)
    log.append((key, case))
    return t


def insert(t, x, log):
    if t is None:
        return Node(x)  # the new leaf itself is not reported as "checked"
    if x < t.key:
        t.left = insert(t.left, x, log)
    elif x > t.key:
        t.right = insert(t.right, x, log)
    else:
        return t  # duplicate: textbook does nothing (balance still runs, but it is a no-op)
    return balance(t, log)


def find_min(t):
    while t.left is not None:
        t = t.left
    return t


def remove(t, x, log):
    if t is None:
        return t
    if x < t.key:
        t.left = remove(t.left, x, log)
    elif x > t.key:
        t.right = remove(t.right, x, log)
    elif t.left is not None and t.right is not None:
        t.key = find_min(t.right).key
        t.right = remove(t.right, t.key, log)
    else:
        return t.left if t.left is not None else t.right
    return balance(t, log)


# ---------------------------------------------------------------- whole-tree helpers

def build(keys):
    root = None
    for k in keys:
        root = insert(root, k, [])
    return root


def copy(t):
    if t is None:
        return None
    n = Node(t.key, copy(t.left), copy(t.right))
    n.height = t.height
    return n


def size(t):
    return 0 if t is None else 1 + size(t.left) + size(t.right)


def keys_inorder(t, out=None):
    out = [] if out is None else out
    if t is not None:
        keys_inorder(t.left, out)
        out.append(t.key)
        keys_inorder(t.right, out)
    return out


def preorder(t, out=None):
    out = [] if out is None else out
    if t is not None:
        out.append(t.key)
        preorder(t.left, out)
        preorder(t.right, out)
    return out


def postorder(t, out=None):
    out = [] if out is None else out
    if t is not None:
        postorder(t.left, out)
        postorder(t.right, out)
        out.append(t.key)
    return out


def level_order(t):
    out, q = [], [t] if t else []
    while q:
        n = q.pop(0)
        out.append(n.key)
        q.extend(c for c in (n.left, n.right) if c)
    return out


def same_shape(a, b):
    if a is None or b is None:
        return a is b
    return a.key == b.key and same_shape(a.left, b.left) and same_shape(a.right, b.right)


def check(t):
    """Return a list of problems (empty list = valid AVL tree)."""
    problems = []

    def walk(n, lo, hi):
        if n is None:
            return -1
        if (lo is not None and n.key <= lo) or (hi is not None and n.key >= hi):
            problems.append(f"{n.key} breaks the BST ordering")
        hl = walk(n.left, lo, n.key)
        hr = walk(n.right, n.key, hi)
        if abs(hl - hr) > 1:
            problems.append(f"{n.key} is imbalanced (left height {hl}, right height {hr})")
        return max(hl, hr) + 1

    walk(t, None, None)
    return problems


def min_nodes(h):
    """Smallest AVL tree of height h: S(h) = S(h-1) + S(h-2) + 1, S(0)=1, S(1)=2."""
    a, b = 1, 2
    if h == 0:
        return 1
    for _ in range(h - 1):
        a, b = b, a + b + 1
    return b


# ---------------------------------------------------------------- text notation

def to_text(t):
    if t is None:
        return ""
    if t.left is None and t.right is None:
        return str(t.key)
    return f"{t.key}({to_text(t.left)},{to_text(t.right)})"


def parse(s):
    """Parse '38(5(1,22(12,31)),56(,79))'. Raises ValueError on bad input."""
    s = re.sub(r"\s+", "", s)
    pos = 0

    def node():
        nonlocal pos
        m = re.match(r"-?\d+", s[pos:])
        if not m:
            return None
        pos += m.end()
        n = Node(int(m.group()))
        if pos < len(s) and s[pos] == "(":
            pos += 1
            n.left = node()
            if pos >= len(s) or s[pos] != ",":
                raise ValueError(f"expected ',' at position {pos} in {s!r}")
            pos += 1
            n.right = node()
            if pos >= len(s) or s[pos] != ")":
                raise ValueError(f"expected ')' at position {pos} in {s!r}")
            pos += 1
        return n

    root = node()
    if pos != len(s):
        raise ValueError(f"unexpected text at position {pos} in {s!r}")
    fix_all_heights(root)
    return root


# ---------------------------------------------------------------- drawing

def draw(t):
    """Top-down ASCII drawing of a tree."""
    if t is None:
        return "(empty tree)"

    def build_lines(n):
        # returns (lines, width, root_center)
        label = str(n.key)
        if n.left is None and n.right is None:
            return [label], len(label), len(label) // 2
        if n.left is not None:
            ll, lw, lc = build_lines(n.left)
        else:
            ll, lw, lc = [], 0, 0
        if n.right is not None:
            rl, rw, rc = build_lines(n.right)
        else:
            rl, rw, rc = [], 0, 0
        gap = 3
        lw_eff = lw if n.left is not None else 1
        rw_eff = rw if n.right is not None else 1
        width = lw_eff + gap + rw_eff
        center = lw_eff + gap // 2
        top = " " * (center - len(label) // 2) + label
        branch = [" "] * width
        if n.left is not None:
            branch[lc + (center - lc) // 2] = "/"
        if n.right is not None:
            rstart = lw_eff + gap
            branch[center + (rstart + rc - center + 1) // 2] = "\\"
        lines = [top.ljust(width), "".join(branch)]
        for i in range(max(len(ll), len(rl))):
            left_part = ll[i] if i < len(ll) else ""
            right_part = rl[i] if i < len(rl) else ""
            lines.append(left_part.ljust(lw_eff) + " " * gap + right_part.ljust(rw_eff))
        width = max(width, len(top))
        return [ln.ljust(width) for ln in lines], width, center

    lines, _, _ = build_lines(t)
    return "\n".join(ln.rstrip() for ln in lines)


# ---------------------------------------------------------------- traces

def trace_insert(t, x):
    """Insert into a COPY. Returns (new_tree, checked_keys, rotation) where rotation is
    (key_of_imbalanced_node, case) or None."""
    t2 = copy(t)
    log = []
    t2 = insert(t2, x, log)
    rot = next(((k, c) for k, c in log if c), None)
    return t2, [k for k, _ in log], rot


def trace_remove(t, x):
    t2 = copy(t)
    log = []
    t2 = remove(t2, x, log)
    rots = [(k, c) for k, c in log if c]
    return t2, [k for k, _ in log], rots


def random_insert_problem(rng=None, want=None, n_range=(7, 12)):
    """Random AVL tree + a key whose insertion causes a rotation.
    want: None (any rotation), 'single', 'double', or 'none' (no rotation needed)."""
    rng = rng or random.Random()
    for _ in range(5000):
        n = rng.randint(*n_range)
        keys = rng.sample(range(1, 100), n)
        t = build(keys)
        present = set(keys_inorder(t))
        candidates = [x for x in range(1, 100) if x not in present]
        rng.shuffle(candidates)
        for x in candidates:
            _, _, rot = trace_insert(t, x)
            kind = None if rot is None else ("double" if rot[1] in ("left-right", "right-left") else "single")
            if want == "none" and rot is None:
                return t, x
            if want in (None, "single", "double") and rot is not None and (want is None or want == kind):
                return t, x
    raise RuntimeError("could not generate a problem")


def random_remove_problem(rng=None, want_rotation=True, n_range=(8, 14)):
    rng = rng or random.Random()
    for _ in range(5000):
        n = rng.randint(*n_range)
        keys = rng.sample(range(1, 100), n)
        t = build(keys)
        ks = keys_inorder(t)
        rng.shuffle(ks)
        for x in ks:
            _, _, rots = trace_remove(t, x)
            if bool(rots) == want_rotation:
                return t, x
    raise RuntimeError("could not generate a problem")


# ---------------------------------------------------------------- pictures (SVG) for "show me"

def bst_insert_only(t, x):
    """Plain BST insert on a copy, NO rebalancing (to show the tree right before the rotation)."""
    t = copy(t)

    def ins(n):
        if n is None:
            return Node(x)
        if x < n.key:
            n.left = ins(n.left)
        elif x > n.key:
            n.right = ins(n.right)
        return n
    t = ins(t)
    fix_all_heights(t)
    return t


def bst_remove_only(t, x):
    """Textbook BST remove (min of right subtree for two children) on a copy, NO rebalancing."""
    t = copy(t)

    def rem(n, x):
        if n is None:
            return None
        if x < n.key:
            n.left = rem(n.left, x)
        elif x > n.key:
            n.right = rem(n.right, x)
        elif n.left is not None and n.right is not None:
            n.key = find_min(n.right).key
            n.right = rem(n.right, n.key)
        else:
            return n.left if n.left is not None else n.right
        return n
    t = rem(t, x)
    fix_all_heights(t)
    return t


def find(t, k):
    while t is not None and t.key != k:
        t = t.left if k < t.key else t.right
    return t


SVG_FILL = {"new": "#2da44e", "path": "#0969da", "bad": "#cf222e", "moved": "#bf8700", "target": "#8250df"}


def svg(t, colors=None, show_balance=True, caption=""):
    """SVG drawing. colors: {key: 'new'|'path'|'bad'|'moved'|'target'}."""
    colors = colors or {}
    if t is None:
        return "<svg width='200' height='60'><text x='10' y='35'>(empty tree)</text></svg>"
    pos, order = {}, []

    def walk(n, d):
        if n is None:
            return
        walk(n.left, d + 1)
        pos[id(n)] = (len(order), d)
        order.append(n)
        walk(n.right, d + 1)
    walk(t, 0)
    dx, dy, r, pad = 46, 74, 17, 30
    depth = max(d for _, d in pos.values())
    W = pad * 2 + dx * (len(order) - 1) + 2 * r
    H = pad * 2 + dy * depth + 2 * r + 24

    def xy(n):
        i, d = pos[id(n)]
        return pad + r + i * dx, pad + r + d * dy

    parts = []
    for n in order:
        x1, y1 = xy(n)
        for c in (n.left, n.right):
            if c is not None:
                x2, y2 = xy(c)
                parts.append(f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' class='edge'/>")
    for n in order:
        x, y = xy(n)
        kind = colors.get(n.key)
        style = f" style='fill:{SVG_FILL[kind]};stroke:{SVG_FILL[kind]}'" if kind else ""
        txt = " style='fill:#fff'" if kind else ""
        parts.append(f"<circle cx='{x}' cy='{y}' r='{r}' class='node'{style}/>"
                     f"<text x='{x}' y='{y + 5}' class='key'{txt}>{n.key}</text>")
        if show_balance:
            bf = height(n.left) - height(n.right)
            cls = "bf bad" if abs(bf) > 1 else "bf"
            parts.append(f"<text x='{x + r + 3}' y='{y - r + 4}' class='{cls}'>{bf:+d}</text>")
    cap = f"<text x='{pad}' y='{H - 6}' class='cap'>{caption}</text>" if caption else ""
    style = ("<style>.edge{stroke:currentColor;stroke-width:1.6;opacity:.55}"
             ".node{fill:var(--bg,#fff);stroke:currentColor;stroke-width:1.8}"
             ".key{font:600 14px Consolas,monospace;text-anchor:middle;fill:currentColor}"
             ".bf{font:11px Consolas,monospace;fill:#8c959f}.bf.bad{fill:#cf222e;font-weight:700}"
             ".cap{font:13px sans-serif;fill:#8c959f}</style>")
    return f"<svg width='{W}' height='{H}' viewBox='0 0 {W} {H}'>" + style + "".join(parts) + cap + "</svg>"


LEGEND = ("<p class='muted'>Colours: <b style='color:#2da44e'>new node</b> · <b style='color:#0969da'>path checked</b>"
          " · <b style='color:#cf222e'>lowest imbalanced node</b> · <b style='color:#bf8700'>nodes that move in the "
          "rotation</b> · <b style='color:#8250df'>node being deleted</b>. Small numbers = balance factor "
          "height(left) &minus; height(right); &plusmn;2 means imbalanced.</p>")


def rotation_nodes(t_before, key, case):
    """Keys of k1/k2/k3 for a rotation at `key` (in the tree right before rotating)."""
    n = find(t_before, key)
    if n is None or case is None:
        return []
    if case == "left-left":
        return [n.key, n.left.key]
    if case == "right-right":
        return [n.key, n.right.key]
    if case == "left-right":
        return [n.key, n.left.key, n.left.right.key]
    return [n.key, n.right.key, n.right.left.key]


def steps_html(t, op, x):
    """Step-by-step HTML for an insert/remove: start, before rebalancing, after."""
    frames = []
    if op == "insert":
        mid = bst_insert_only(t, x)
        after, checked, rot = trace_insert(t, x)
        frames.append(("1 · Start", svg(t), f"Insert <b>{x}</b>. Walk down like a BST search to find where it goes."))
        colors = {k: "path" for k in checked}
        colors[x] = "new"
        moved = []
        if rot:
            colors[rot[0]] = "bad"
        txt = (f"{x} is inserted as a leaf. Now check balance from its <b>parent</b> up to the root, in order: "
               f"<b>{', '.join(map(str, checked))}</b>.")
        if rot:
            moved = rotation_nodes(mid, rot[0], rot[1])
            txt += (f" The lowest imbalanced node is <b>{rot[0]}</b> (balance factor &plusmn;2): a <b>{rot[1]}</b> "
                    f"case &rarr; {CASE_TEXT[rot[1]]}.")
        else:
            txt += " Every node is within &plusmn;1, so no rotation is needed (heights just get updated)."
        frames.append(("2 · After the insert, before rebalancing", svg(mid, colors), txt))
        if rot:
            frames.append(("3 · After the rotation", svg(after, {k: "moved" for k in moved}),
                           f"Nodes that moved: <b>{', '.join(map(str, moved))}</b>. "
                           f"Result: <code>{to_text(after)}</code>"))
    else:
        mid = bst_remove_only(t, x)
        after, checked, rots = trace_remove(t, x)
        frames.append(("1 · Start", svg(t, {x: "target"}), f"Delete <b>{x}</b>."))
        n = find(t, x)
        how = "no children (a leaf), so it is simply removed"
        if n is not None and n.left and n.right:
            how = (f"two children, so it is replaced by the smallest key of its right subtree "
                   f"(<b>{find_min(n.right).key}</b>), which is then removed from the right subtree")
        elif n is not None and (n.left or n.right):
            how = "one child, so its child moves up into its place"
        colors = {k: "path" for k in checked}
        for k, _ in rots:
            colors[k] = "bad"
        txt = (f"{x} has {how}. Check balance on the way back up: "
               f"<b>{', '.join(map(str, checked)) or '(none)'}</b>.")
        if rots:
            txt += " Rotations needed: " + "; ".join(f"<b>{k}</b>: {c}" for k, c in rots) + "."
        else:
            txt += " No rotation needed."
        frames.append(("2 · After the delete, before rebalancing", svg(mid, colors), txt))
        if rots:
            frames.append(("3 · After rebalancing", svg(after), f"Result: <code>{to_text(after)}</code>"))
    body = [f"<h1>AVL {op} {x}</h1>", LEGEND]
    for title, pic, text in frames:
        body.append(f"<h2>{title}</h2><p>{text}</p><div class='pic'>{pic}</div>")
    return "\n".join(body)
