"""Binary heap engine that follows the Weiss textbook (4th ed.) exactly.

Chapter 6 BinaryHeap (min-heap by default):
  * array[0] is NOT part of the heap. The root is array[1]; children of i are 2i and 2i+1, parent i/2.
  * insert: hole = ++currentSize; array[0] = x (the value being moved);
            while x < array[hole/2]: array[hole] = array[hole/2]; hole /= 2   (strict <: ties stop)
            array[hole] = array[0]
  * deleteMin: array[1] = array[currentSize--]; percolateDown(1)
  * percolateDown(hole): tmp = array[hole]  (the professor shows tmp in index 0)
            child = 2*hole; if child != currentSize and array[child+1] < array[child]: child++
            (ties between children go LEFT); if array[child] < tmp: move child up, else stop (ties stop)
  * buildHeap: for i = currentSize/2 down to 1: percolateDown(i)
  * decreaseKey(p, d): array[p] -= d, percolate up;  increaseKey(p, d): array[p] += d, percolate down
  * remove(p): decreaseKey(p, infinity) then deleteMin
  With kind="max" every comparison is reversed (max-heap, deleteMax).

Chapter 7 heapsort (Fig. 7.10) is DIFFERENT: a 0-indexed MAX-heap inside the array being sorted.
  leftChild(i) = 2i+1; buildHeap: for i = n/2-1 down to 0: percDown(a, i, n)
  for j = n-1 down to 1: swap(a[0], a[j]); percDown(a, 0, j)
  percDown: child = 2i+1; if child != n-1 and a[child] < a[child+1]: child++ ; if tmp < a[child]: move, else stop

Every operation returns a list of steps: (label, snapshot) where snapshot is a list. For the Ch. 6 heap the
snapshot includes index 0 (the value being moved, or None) and None marks the hole.
"""

import random

HOLE = None


def _lt(kind):
    return (lambda a, b: a < b) if kind == "min" else (lambda a, b: a > b)


def fmt(arr, start=1, show0=True):
    """Ch.6 array as text: [0]=8 | _ 5 6 ... (index 0 = value being moved)."""
    cells = ["_" if v is None else str(v) for v in arr[start:]]
    zero = arr[0] if arr else None
    head = f"[0]={'-' if zero is None else zero} | " if show0 else ""
    return head + " ".join(cells)


def plain(arr):
    """Heap contents from index 1, comma separated (the usual answer format)."""
    return ",".join(str(v) for v in arr[1:])


def from_list(values):
    """User values (root first) -> internal array with index 0 empty."""
    return [None] + list(values)


# ---------------------------------------------------------------- chapter 6 operations

def insert(arr, x, kind="min", steps=None):
    lt = _lt(kind)
    a = list(arr)
    steps = [] if steps is None else steps
    a.append(HOLE)
    hole = len(a) - 1
    a[0] = x
    steps.append((f"insert {x}: hole created at index {hole}; {x} stored in index 0", list(a)))
    while hole > 1 and lt(x, a[hole // 2]):
        p = hole // 2
        a[hole] = a[p]
        a[p] = HOLE
        steps.append((f"{x} < parent {a[hole]} (index {p}) -> slide {a[hole]} down to index {hole}; hole moves to {p}"
                      if kind == "min" else
                      f"{x} > parent {a[hole]} (index {p}) -> slide {a[hole]} down to index {hole}; hole moves to {p}",
                      list(a)))
        hole = p
    a[hole] = x
    a[0] = None
    why = "hole is the root" if hole == 1 else f"parent {a[hole // 2]} is not {'larger' if kind == 'min' else 'smaller'}"
    steps.append((f"place {x} in index {hole} ({why})", list(a)))
    return a, steps


def percolate_down(a, hole, kind="min", steps=None, size=None):
    """In place on the Ch.6 array a (index 0 used for tmp). size = currentSize (default len(a)-1)."""
    lt = _lt(kind)
    steps = [] if steps is None else steps
    n = len(a) - 1 if size is None else size
    tmp = a[hole]
    a[0] = tmp
    a[hole] = HOLE
    steps.append((f"percolateDown({hole}): {tmp} moved to index 0, hole at {hole}", list(a)))
    while hole * 2 <= n:
        child = hole * 2
        if child != n and lt(a[child + 1], a[child]):
            child += 1
        if lt(a[child], tmp):
            a[hole] = a[child]
            a[child] = HOLE
            steps.append((f"{'smaller' if kind == 'min' else 'larger'} child {a[hole]} (index {child}) beats {tmp} "
                          f"-> slide it up to index {hole}; hole moves to {child}", list(a)))
            hole = child
        else:
            steps.append((f"best child {a[child]} (index {child}) does not beat {tmp} -> stop", list(a)))
            break
    a[hole] = tmp
    a[0] = None
    steps.append((f"place {tmp} in index {hole}", list(a)))
    return a, steps


def delete_min(arr, kind="min", steps=None):
    a = list(arr)
    steps = [] if steps is None else steps
    if len(a) <= 1:
        raise ValueError("heap is empty")
    top = a[1]
    last = a.pop()
    if len(a) == 1:
        steps.append((f"delete{'Min' if kind == 'min' else 'Max'} {top}: heap is now empty", list(a)))
        return a, top, steps
    a[0] = last
    a[1] = HOLE
    steps.append((f"delete{'Min' if kind == 'min' else 'Max'}: remove {top} from the root (hole at 1); "
                  f"last element {last} goes to index 0; size {len(a) - 1}", list(a)))
    a[1] = last          # percolate_down re-stores it in index 0 and makes the hole again
    sub = []
    percolate_down(a, 1, kind, sub)
    steps.extend(sub[1:])  # skip the duplicate 'moved to index 0' frame
    return a, top, steps


def build_heap(values, kind="min", steps=None, detail=False):
    a = from_list(values)
    steps = [] if steps is None else steps
    n = len(a) - 1
    steps.append((f"start (size {n}); percolateDown from i = {n // 2} down to 1", list(a)))
    for i in range(n // 2, 0, -1):
        before = a[i]
        sub = []
        percolate_down(a, i, kind, sub)
        if detail:
            steps.extend(sub)
        else:
            steps.append((f"after percolateDown({i}) (value {before})", list(a)))
    return a, steps


def percolate_up_at(a, hole, kind="min", steps=None):
    lt = _lt(kind)
    steps = [] if steps is None else steps
    x = a[hole]
    a[0] = x
    a[hole] = HOLE
    while hole > 1 and lt(x, a[hole // 2]):
        p = hole // 2
        a[hole] = a[p]
        a[p] = HOLE
        steps.append((f"slide parent {a[hole]} down to index {hole}", list(a)))
        hole = p
    a[hole] = x
    a[0] = None
    steps.append((f"place {x} in index {hole}", list(a)))
    return a, steps


def decrease_key(arr, p, delta, kind="min", steps=None):
    a = list(arr)
    steps = [] if steps is None else steps
    a[p] = a[p] - delta if kind == "min" else a[p] + delta
    steps.append((f"{'decreaseKey' if kind == 'min' else 'increaseKey'}({p}, {delta}): index {p} becomes {a[p]}", list(a)))
    return percolate_up_at(a, p, kind, steps)


def increase_key(arr, p, delta, kind="min", steps=None):
    a = list(arr)
    steps = [] if steps is None else steps
    a[p] = a[p] + delta if kind == "min" else a[p] - delta
    steps.append((f"{'increaseKey' if kind == 'min' else 'decreaseKey'}({p}, {delta}): index {p} becomes {a[p]}", list(a)))
    return percolate_down(a, p, kind, steps)


def remove_at(arr, p, kind="min", steps=None):
    """remove(p) = decreaseKey(p, infinity) + deleteMin. Shown with the value conceptually -inf."""
    a = list(arr)
    steps = [] if steps is None else steps
    gone = a[p]
    lt = _lt(kind)
    # percolate the 'infinitely small' value to the root
    hole = p
    a[hole] = HOLE
    steps.append((f"remove({p}): {gone} becomes -infinity (decreaseKey by infinity) and percolates up", list(a)))
    while hole > 1:
        q = hole // 2
        a[hole] = a[q]
        a[q] = HOLE
        steps.append((f"slide parent {a[hole]} down to index {hole}", list(a)))
        hole = q
    a[1] = "-inf" if kind == "min" else "+inf"
    steps.append(("the -infinity value is at the root; now deleteMin removes it" if kind == "min"
                  else "the +infinity value is at the root; now deleteMax removes it", list(a)))
    a2, _, sub = delete_min(a, kind)
    steps.extend(sub[1:] if len(sub) > 1 else sub)
    return a2, gone, steps


def is_heap(arr, kind="min"):
    lt = _lt(kind)
    n = len(arr) - 1
    bad = []
    for i in range(2, n + 1):
        if lt(arr[i], arr[i // 2]):
            bad.append(f"index {i} ({arr[i]}) {'<' if kind == 'min' else '>'} its parent index {i // 2} ({arr[i // 2]})")
    return bad


# ---------------------------------------------------------------- chapter 7 heapsort (0-indexed max-heap)

def perc_down0(a, i, n, steps=None, label=""):
    steps = [] if steps is None else steps
    tmp = a[i]
    start = i
    while 2 * i + 1 < n:
        child = 2 * i + 1
        if child != n - 1 and a[child] < a[child + 1]:
            child += 1
        if tmp < a[child]:
            a[i] = a[child]
            i = child
        else:
            break
    a[i] = tmp
    if label is not None:
        steps.append((label or f"percDown(a, {start}, {n}): {tmp} ends at index {i}", list(a)))
    return a, steps


def heapsort(values, steps=None):
    a = list(values)
    steps = [] if steps is None else steps
    n = len(a)
    steps.append((f"start (n = {n}); buildHeap: percDown from i = {n // 2 - 1} down to 0 (MAX-heap, 0-indexed)", list(a)))
    for i in range(n // 2 - 1, -1, -1):
        perc_down0(a, i, n, steps, f"buildHeap: after percDown(a, {i}, {n}) (value {a[i]})")
    steps.append(("== heap built ==", list(a)))
    for j in range(n - 1, 0, -1):
        mx = a[0]
        a[0], a[j] = a[j], a[0]
        perc_down0(a, 0, j, steps, f"deleteMax {mx}: swap a[0] with a[{j}], then percDown(a, 0, {j}) "
                                   f"-> heap = a[0..{j - 1}], sorted = a[{j}..{n - 1}]")
    return a, steps


# ---------------------------------------------------------------- pictures

def to_tree(arr, start=1):
    """Array heap -> avl.Node tree for drawing (start=1 for Ch.6, 0 for heapsort)."""
    import avl
    vals = arr[start:]
    nodes = [None if v is None else avl.Node(v) for v in vals]
    # holes are drawn as '_' nodes so the shape stays complete
    for k, v in enumerate(vals):
        if nodes[k] is None:
            nodes[k] = avl.Node("_")
    for k in range(len(vals)):
        l, r = 2 * k + 1, 2 * k + 2
        if l < len(vals):
            nodes[k].left = nodes[l]
        if r < len(vals):
            nodes[k].right = nodes[r]
    return nodes[0] if nodes else None


def array_html(arr, start=1, hl=None, sorted_from=None):
    """Boxes with indices. hl = {index: css-color}."""
    hl = hl or {}
    cells = []
    for i, v in enumerate(arr):
        if i < start and start == 1 and i == 0:
            txt = "" if v is None else str(v)
            cells.append(f"<td style='border-style:dashed;color:#8250df'>{txt}<div class='muted'>[0] tmp</div></td>")
            continue
        txt = "_" if v is None else str(v)
        style = ""
        if sorted_from is not None and i >= sorted_from:
            style = "background:#2da44e33"
        if i in hl:
            style = f"background:{hl[i]};color:#fff"
        cells.append(f"<td style='text-align:center;min-width:34px;{style}'><b>{txt}</b><div class='muted'>{i}</div></td>")
    return "<table><tr>" + "".join(cells) + "</tr></table>"


def steps_html(title, steps, start=1, tree=True, sorted_tail=False):
    import avl
    out = [f"<h1>{title}</h1>",
           "<p class='muted'>Index 0 (dashed) holds the value being moved, as in the textbook. "
           "<b>_</b> = the hole.</p>" if start == 1 else
           "<p class='muted'>Heapsort uses a 0-indexed MAX-heap; green cells are the sorted part at the end.</p>"]
    n0 = None
    for k, (label, snap) in enumerate(steps):
        out.append(f"<h2>Step {k}: {label}</h2>")
        sorted_from = None
        if sorted_tail:
            import re
            m = re.search(r"sorted = a\[(\d+)\.\.", label)
            sorted_from = int(m.group(1)) if m else (len(snap) if n0 is None else None)
        holes = {i: "#bf8700" for i, v in enumerate(snap) if v is None and i >= start and i > 0}
        out.append(array_html(snap, start, holes, sorted_from))
        if tree:
            heap_part = snap if not sorted_tail or sorted_from is None else snap[:sorted_from]
            t = to_tree(heap_part, start)
            if t is not None:
                colors = {"_": "moved"}
                out.append(f"<div class='pic'>{avl.svg(t, colors, show_balance=False)}</div>")
    return "\n".join(out)


# ---------------------------------------------------------------- random problems

def random_heap(rng, n, kind="min", lo=1, hi=60):
    vals = rng.sample(range(lo, hi), n)
    a = None
    a = from_list([])
    for v in vals:
        a, _ = insert(a, v, kind)
    return a


def random_problem(kind_of_problem, seed):
    """Returns (description, data) for gen ids: heap-ins, heap-del, heap-build, heapsort, heap-mix."""
    rng = random.Random(seed)
    if kind_of_problem == "heap-ins":
        a = random_heap(rng, rng.randint(6, 10))
        used = set(a[1:])
        xs = [v for v in rng.sample(range(1, 60), 12) if v not in used][:rng.randint(1, 3)]
        return {"op": "insert", "heap": a[1:], "xs": xs}
    if kind_of_problem == "heap-del":
        a = random_heap(rng, rng.randint(8, 12))
        return {"op": "deleteMin", "heap": a[1:], "count": rng.randint(1, 2)}
    if kind_of_problem == "heap-build":
        return {"op": "buildHeap", "values": rng.sample(range(1, 40), rng.randint(9, 13))}
    if kind_of_problem == "heapsort":
        return {"op": "heapsort", "values": rng.sample(range(1, 99), rng.randint(6, 8))}
    if kind_of_problem == "heap-max":
        return {"op": "buildHeapMax", "values": rng.sample(range(1, 40), rng.randint(8, 11))}
    raise ValueError(kind_of_problem)


def solve(problem):
    """Returns (final_array_text, steps, extra) for a random_problem dict."""
    op = problem["op"]
    if op == "insert":
        a = from_list(problem["heap"])
        steps = []
        for x in problem["xs"]:
            a, _ = insert(a, x, "min", steps)
        return plain(a), steps, ""
    if op == "deleteMin":
        a = from_list(problem["heap"])
        steps, outs = [], []
        for _ in range(problem["count"]):
            a, top, _ = delete_min(a, "min", steps)
            outs.append(top)
        return plain(a), steps, f"removed: {outs}"
    if op == "buildHeap":
        a, steps = build_heap(problem["values"], "min")
        return plain(a), steps, ""
    if op == "buildHeapMax":
        a, steps = build_heap(problem["values"], "max")
        return plain(a), steps, ""
    if op == "heapsort":
        a, steps = heapsort(problem["values"])
        return ",".join(map(str, a)), steps, ""
    raise ValueError(op)


def describe(problem):
    op = problem["op"]
    if op == "insert":
        return (f"Min-heap (array from index 1, textbook layout): {', '.join(map(str, problem['heap']))}\n"
                f"Insert {', '.join(map(str, problem['xs']))} (in that order). Show the array after each step of "
                f"percolate up (use index 0 for the value being inserted, as in the textbook) and the final heap.")
    if op == "deleteMin":
        return (f"Min-heap (array from index 1): {', '.join(map(str, problem['heap']))}\n"
                f"Perform {problem['count']} deleteMin operation(s). Show the array after each step "
                f"(index 0 holds the value being moved) and the final heap.")
    if op == "buildHeap":
        return (f"Use the linear-time buildHeap (textbook) to build a MIN-heap from: "
                f"{', '.join(map(str, problem['values']))}\nShow the array after each percolateDown and the final heap.")
    if op == "buildHeapMax":
        return (f"Use the linear-time buildHeap to build a MAX-heap from: "
                f"{', '.join(map(str, problem['values']))}\nShow the array after each percolateDown and the final heap.")
    if op == "heapsort":
        return (f"Sort {', '.join(map(str, problem['values']))} with the textbook heapsort (Fig. 7.10: 0-indexed "
                f"max-heap). Show the array after buildHeap and after each deleteMax.")
    return str(problem)
