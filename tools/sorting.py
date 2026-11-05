"""Sorting trace engine that follows the Weiss textbook (4th ed., Ch. 7) and the professor's examples.

Quicksort / quickselect partition methods:
  hoare (DEFAULT - textbook 7.7.2, HW7 7.19, the "Hoare Partitioning Example" handout, the slides):
      1. choose the pivot (median-of-3 of a[left], a[center], a[right] with center = (left+right)/2,
         or a given index, or first/last/middle) and SWAP IT WITH THE LAST ELEMENT a[right]
      2. i = left, j = right-1
      3. loop: move i right while a[i] < pivot; move j left while a[j] > pivot (j never goes below left);
               both STOP on elements EQUAL to the pivot;
               if i < j: swap a[i], a[j], then i++, j--; else break
      4. swap a[i] with the pivot at a[right]
  code (textbook Fig. 7.16/7.17 C++): median3 SORTS a[left], a[center], a[right], then hides the pivot at
      right-1; i = left, j = right-1; while a[++i] < pivot; while pivot < a[--j]; swap or break;
      swap a[i], a[right-1]. (Only differs from `hoare` in the median-of-3 side effects / where the pivot hides.)
  lomuto: pivot chosen as above and swapped to a[right]; i = left-1; for j = left..right-1: if a[j] <= pivot:
      i++, swap a[i], a[j]; finally swap a[i+1], a[right]. (The professor said "Lomuto?" - may not be tested.)
Cutoff: a subarray with size <= cutoff is insertion-sorted instead of partitioned (HW7: cutoff 3).
  The textbook code's `if (left + CUTOFF <= right)` is the same thing: partition only when size >= CUTOFF+1.
Median-of-3 tie rule (not specified by the book): prefer the center index, then left, then right.

Quickselect (Fig. 7.19 in the 4th ed. text): k is 1-based (k-th smallest). After partitioning around index i:
  k <= i -> recurse left (left..i-1); k == i+1 -> pivot is the answer; else recurse right (i+1..right).
Mergesort (Fig. 7.11/7.12): center = (left+right)/2, sort a[left..center], sort a[center+1..right], merge;
  merge takes from the LEFT run on ties (<=) so it is stable.
Insertion sort: pass p = 1..n-1 slides a[p] left past larger elements (strict <, so it is stable).
"""

import random


def parse(s):
    return [int(v) for v in s.replace(" ", "").replace(";", ",").split(",") if v != ""]


def fmt(a, lo=None, hi=None):
    out = []
    for k, v in enumerate(a):
        cell = str(v)
        if lo is not None and k == lo:
            cell = "[" + cell
        if hi is not None and k == hi:
            cell = cell + "]"
        out.append(cell)
    return " ".join(out)


# ---------------------------------------------------------------- insertion sort

def insertion_sort(a, left=0, right=None, steps=None, label_prefix=""):
    a = a if steps is not None else list(a)
    steps = [] if steps is None else steps
    right = len(a) - 1 if right is None else right
    for p in range(left + 1, right + 1):
        tmp = a[p]
        j = p
        moved = 0
        while j > left and tmp < a[j - 1]:
            a[j] = a[j - 1]
            j -= 1
            moved += 1
        a[j] = tmp
        steps.append({"kind": "insertion", "label": f"{label_prefix}insertion pass p={p}: {tmp} moves left "
                                                   f"{moved} place(s) to index {j}", "array": list(a),
                      "lo": left, "hi": right, "mark": {j: "moved"}})
    return a, steps


def inversions(a):
    return [(a[i], a[j]) for i in range(len(a)) for j in range(i + 1, len(a)) if a[i] > a[j]]


# ---------------------------------------------------------------- mergesort

def mergesort(values):
    a = list(values)
    tmp = [None] * len(a)
    steps = []

    def merge(left, center, right):
        L, R = a[left:center + 1], a[center + 1:right + 1]
        lp, rp, out = 0, 0, []
        while lp < len(L) and rp < len(R):
            if L[lp] <= R[rp]:
                out.append(L[lp]); lp += 1
            else:
                out.append(R[rp]); rp += 1
        out += L[lp:] + R[rp:]
        a[left:right + 1] = out
        steps.append({"kind": "merge", "label": f"merge {L} + {R} -> {out}  (indices {left}..{right})",
                      "array": list(a), "lo": left, "hi": right, "mark": {}})

    def ms(left, right):
        if left < right:
            center = (left + right) // 2
            ms(left, center)
            ms(center + 1, right)
            merge(left, center, right)
    _ = tmp
    ms(0, len(a) - 1)
    return a, steps


# ---------------------------------------------------------------- pivot choice

def median3_index(a, left, right):
    center = (left + right) // 2
    trio = sorted([(a[left], 1, left), (a[center], 0, center), (a[right], 2, right)])
    med_val = trio[1][0]
    for idx in (center, left, right):     # tie rule: center, then left, then right
        if a[idx] == med_val:
            return idx, center


def choose_pivot(a, left, right, how, given=None):
    if how == "median3":
        idx, center = median3_index(a, left, right)
        return idx, (f"median-of-3: a[{left}]={a[left]}, a[{center}]={a[center]} (center), a[{right}]={a[right]} "
                     f"-> pivot {a[idx]}")
    if how == "first":
        return left, f"first element -> pivot {a[left]}"
    if how == "last":
        return right, f"last element -> pivot {a[right]}"
    if how == "middle":
        c = (left + right) // 2
        return c, f"middle element (index {c}) -> pivot {a[c]}"
    if how == "index":
        return given, f"given pivot index {given} -> pivot {a[given]}"
    raise ValueError(how)


# ---------------------------------------------------------------- partitions

def partition_hoare(a, left, right, how="median3", given=None, steps=None):
    steps = [] if steps is None else steps
    pidx, why = choose_pivot(a, left, right, how, given)
    pivot = a[pidx]
    if pidx != right:
        a[pidx], a[right] = a[right], a[pidx]
        steps.append({"kind": "pivot", "label": f"{why}; swap it with the last element a[{right}]",
                      "array": list(a), "lo": left, "hi": right, "mark": {right: "pivot", pidx: "moved"}})
    else:
        steps.append({"kind": "pivot", "label": f"{why}; it is already the last element", "array": list(a),
                      "lo": left, "hi": right, "mark": {right: "pivot"}})
    i, j = left, right - 1
    while True:
        while a[i] < pivot:
            i += 1
        while j > left and a[j] > pivot:
            j -= 1
        if i < j:
            a[i], a[j] = a[j], a[i]
            steps.append({"kind": "swap", "label": f"i stops at index {i}, j stops at index {j}: swap {a[j]} and {a[i]}",
                          "array": list(a), "lo": left, "hi": right, "mark": {i: "i", j: "j", right: "pivot"}})
            i += 1
            j -= 1
        else:
            steps.append({"kind": "cross", "label": f"i stops at index {i} ({a[i]}), j at index {j}"
                                                   f"{' (' + str(a[j]) + ')' if j >= left else ''}: "
                                                   f"crossed, no swap", "array": list(a), "lo": left, "hi": right,
                          "mark": {i: "i", **({j: "j"} if j >= left and j != i else {}), right: "pivot"}})
            break
    a[i], a[right] = a[right], a[i]
    steps.append({"kind": "restore", "label": f"swap a[{i}] with the pivot: pivot {pivot} is now at index {i} "
                                             f"(left part {left}..{i - 1}, right part {i + 1}..{right})",
                  "array": list(a), "lo": left, "hi": right, "mark": {i: "pivot"}})
    return i


def partition_code(a, left, right, steps=None):
    """Fig. 7.16 median3 + Fig. 7.17 loop. Needs right - left >= 2."""
    steps = [] if steps is None else steps
    center = (left + right) // 2
    if a[center] < a[left]:
        a[left], a[center] = a[center], a[left]
    if a[right] < a[left]:
        a[left], a[right] = a[right], a[left]
    if a[right] < a[center]:
        a[center], a[right] = a[right], a[center]
    a[center], a[right - 1] = a[right - 1], a[center]
    pivot = a[right - 1]
    steps.append({"kind": "pivot", "label": f"median3 sorts a[{left}], a[{center}], a[{right}] and hides pivot {pivot} "
                                           f"at a[{right - 1}]", "array": list(a), "lo": left, "hi": right,
                  "mark": {right - 1: "pivot", left: "moved", right: "moved"}})
    i, j = left, right - 1
    while True:
        i += 1
        while a[i] < pivot:
            i += 1
        j -= 1
        while pivot < a[j]:
            j -= 1
        if i < j:
            a[i], a[j] = a[j], a[i]
            steps.append({"kind": "swap", "label": f"i={i}, j={j}: swap {a[j]} and {a[i]}", "array": list(a),
                          "lo": left, "hi": right, "mark": {i: "i", j: "j", right - 1: "pivot"}})
        else:
            steps.append({"kind": "cross", "label": f"i={i}, j={j}: crossed, no swap", "array": list(a),
                          "lo": left, "hi": right, "mark": {i: "i", j: "j", right - 1: "pivot"}})
            break
    a[i], a[right - 1] = a[right - 1], a[i]
    steps.append({"kind": "restore", "label": f"swap a[{i}] with a[{right - 1}]: pivot {pivot} at index {i}",
                  "array": list(a), "lo": left, "hi": right, "mark": {i: "pivot"}})
    return i


def partition_lomuto(a, left, right, how="last", given=None, steps=None):
    steps = [] if steps is None else steps
    pidx, why = choose_pivot(a, left, right, how, given)
    if pidx != right:
        a[pidx], a[right] = a[right], a[pidx]
    pivot = a[right]
    steps.append({"kind": "pivot", "label": f"{why}; pivot at a[{right}] (Lomuto)", "array": list(a),
                  "lo": left, "hi": right, "mark": {right: "pivot"}})
    i = left - 1
    for j in range(left, right):
        if a[j] <= pivot:
            i += 1
            if i != j:
                a[i], a[j] = a[j], a[i]
                steps.append({"kind": "swap", "label": f"a[{j}] <= {pivot}: i -> {i}, swap a[{i}] and a[{j}]",
                              "array": list(a), "lo": left, "hi": right, "mark": {i: "i", j: "j", right: "pivot"}})
            else:
                steps.append({"kind": "swap", "label": f"a[{j}] <= {pivot}: i -> {i} (no move needed)",
                              "array": list(a), "lo": left, "hi": right, "mark": {i: "i", right: "pivot"}})
    a[i + 1], a[right] = a[right], a[i + 1]
    steps.append({"kind": "restore", "label": f"swap a[{i + 1}] with the pivot: pivot {pivot} at index {i + 1}",
                  "array": list(a), "lo": left, "hi": right, "mark": {i + 1: "pivot"}})
    return i + 1


def partition(a, left, right, method="hoare", how="median3", given=None, steps=None):
    if method == "hoare":
        return partition_hoare(a, left, right, how, given, steps)
    if method == "code":
        return partition_code(a, left, right, steps)
    if method == "lomuto":
        return partition_lomuto(a, left, right, how, given, steps)
    raise ValueError(method)


# ---------------------------------------------------------------- quicksort / quickselect

def quicksort(values, method="hoare", how="median3", cutoff=3, given=None):
    """given = pivot index for the FIRST partition only (like the handout); later ones use `how`
    (median3 if how == 'index')."""
    a = list(values)
    steps = []
    later_how = "median3" if how == "index" else how
    first = [True]

    def qs(left, right, depth):
        size = right - left + 1
        if size <= 1:
            return
        if size <= max(cutoff, 2 if method == "code" else 1):
            insertion_sort(a, left, right, steps, f"size {size} <= cutoff {cutoff} at {left}..{right}: ")
            if size > 1 and not any(s.get("lo") == left and s["kind"] == "insertion" for s in steps[-(size - 1):]):
                pass
            return
        steps.append({"kind": "call", "label": f"quicksort({left}, {right})  depth {depth}", "array": list(a),
                      "lo": left, "hi": right, "mark": {}})
        h = how if first[0] else later_how
        g = given if first[0] else None
        first[0] = False
        i = partition(a, left, right, method, h, g, steps)
        qs(left, i - 1, depth + 1)
        qs(i + 1, right, depth + 1)
    qs(0, len(a) - 1, 0)
    return a, steps


def quickselect(values, k, method="hoare", how="median3", cutoff=3, given=None):
    a = list(values)
    steps = []
    left, right = 0, len(a) - 1
    first = True
    while True:
        size = right - left + 1
        if size <= max(cutoff, 1):
            insertion_sort(a, left, right, steps, f"size {size} <= cutoff {cutoff} at {left}..{right}: ")
            steps.append({"kind": "answer", "label": f"k = {k}: answer a[{k - 1}] = {a[k - 1]}", "array": list(a),
                          "lo": left, "hi": right, "mark": {k - 1: "pivot"}})
            return a[k - 1], a, steps
        steps.append({"kind": "call", "label": f"quickSelect({left}, {right}, k={k})", "array": list(a),
                      "lo": left, "hi": right, "mark": {}})
        h = how if first or how != "index" else "median3"
        g = given if first else None
        first = False
        i = partition(a, left, right, method, h, g, steps)
        if k <= i:
            steps.append({"kind": "side", "label": f"k = {k} <= i = {i} -> recurse LEFT on {left}..{i - 1}",
                          "array": list(a), "lo": left, "hi": i - 1, "mark": {}})
            right = i - 1
        elif k == i + 1:
            steps.append({"kind": "answer", "label": f"k = {k} == i + 1 = {i + 1} -> the pivot {a[i]} is the answer",
                          "array": list(a), "lo": left, "hi": right, "mark": {i: "pivot"}})
            return a[i], a, steps
        else:
            steps.append({"kind": "side", "label": f"k = {k} > i + 1 = {i + 1} -> recurse RIGHT on {i + 1}..{right}",
                          "array": list(a), "lo": i + 1, "hi": right, "mark": {}})
            left = i + 1


# ---------------------------------------------------------------- display

COLORS = {"pivot": "#8250df", "i": "#0969da", "j": "#cf222e", "moved": "#bf8700"}


def array_row(a, lo=None, hi=None, mark=None):
    mark = mark or {}
    cells = []
    for k, v in enumerate(a):
        style = "text-align:center;min-width:32px;"
        if lo is not None and (k < lo or k > hi):
            style += "opacity:.35;"
        tag = ""
        if k in mark:
            style += f"background:{COLORS.get(mark[k], '#888')};color:#fff;"
            tag = mark[k]
        cells.append(f"<td style='{style}'><b>{v}</b><div class='muted' style='color:inherit'>{k}{' ' + tag if tag else ''}</div></td>")
    return "<table><tr>" + "".join(cells) + "</tr></table>"


def steps_text(steps):
    lines = []
    for s in steps:
        lines.append(f"{s['label']}\n    {fmt(s['array'], s.get('lo'), s.get('hi'))}")
    return "\n".join(lines)


def steps_html(title, start, steps):
    out = [f"<h1>{title}</h1>",
           "<p class='muted'>Colours: <b style='color:#8250df'>pivot</b> · <b style='color:#0969da'>i</b> · "
           "<b style='color:#cf222e'>j</b> · <b style='color:#bf8700'>moved</b>. Faded cells are outside the "
           "current subarray.</p>",
           "<h2>Start</h2>", array_row(start)]
    for k, s in enumerate(steps, 1):
        out.append(f"<h2>{k}. {s['label']}</h2>")
        out.append(array_row(s["array"], s.get("lo"), s.get("hi"), s.get("mark")))
    return "\n".join(out)


# ---------------------------------------------------------------- random problems

def random_problem(kind, seed):
    rng = random.Random(seed)
    if kind == "partition":
        n = rng.randint(9, 13)
        vals = rng.sample(range(1, 40), n)
        if rng.random() < 0.4:  # a given pivot index, like the handout
            return {"op": "partition", "values": vals, "how": "index", "given": rng.randrange(n)}
        return {"op": "partition", "values": vals, "how": "median3"}
    if kind == "quicksort":
        n = rng.randint(9, 12)
        vals = [rng.randint(1, 9) for _ in range(n)] if rng.random() < 0.3 else rng.sample(range(1, 30), n)
        return {"op": "quicksort", "values": vals, "cutoff": 3}
    if kind == "quickselect":
        n = rng.randint(9, 13)
        vals = rng.sample(range(1, 50), n)
        return {"op": "quickselect", "values": vals, "k": rng.randint(1, n), "cutoff": 3}
    if kind == "mergesort":
        return {"op": "mergesort", "values": rng.sample(range(1, 60), rng.randint(7, 10))}
    if kind == "insertion":
        return {"op": "insertion", "values": rng.sample(range(1, 60), rng.randint(6, 8))}
    raise ValueError(kind)


def describe(p):
    v = ", ".join(map(str, p["values"]))
    if p["op"] == "partition":
        if p["how"] == "index":
            return (f"Array (0-indexed): {v}\nShow the result of Hoare partitioning (textbook 7.7.2) around the pivot at "
                    f"index {p['given']} (value {p['values'][p['given']]}). Show the array after moving the pivot "
                    f"and after every swap, and the final array.")
        return (f"Array (0-indexed): {v}\nUsing median-of-three pivot selection and the Hoare partitioning strategy "
                f"from textbook 7.7.2, show the pivot and the array after moving the pivot, after every swap, and "
                f"after the partition is complete.")
    if p["op"] == "quicksort":
        return (f"Sort {v} using quicksort with median-of-three partitioning and a cutoff of {p['cutoff']} "
                f"(partitions of size <= {p['cutoff']} are insertion-sorted). Use the textbook 7.7.2 Hoare "
                f"partition; i and j both stop on elements equal to the pivot. Show the array after each partition.")
    if p["op"] == "quickselect":
        return (f"Use quickselect (median-of-three, Hoare partition, cutoff {p['cutoff']}) to find the "
                f"k = {p['k']} smallest element of {v}. Show each partition, which side you recurse on and why, "
                f"and the answer.")
    if p["op"] == "mergesort":
        return f"Sort {v} with the textbook (top-down) mergesort. Show the result of every merge, in order."
    if p["op"] == "insertion":
        return f"Sort {v} with insertion sort. Show the array after each pass, and count the inversions."
    return str(p)


def solve(p):
    op = p["op"]
    if op == "partition":
        a = list(p["values"])
        steps = []
        i = partition_hoare(a, 0, len(a) - 1, p["how"], p.get("given"), steps)
        return {"final": a, "steps": steps, "extra": f"pivot ends at index {i}"}
    if op == "quicksort":
        a, steps = quicksort(p["values"], "hoare", "median3", p.get("cutoff", 3))
        return {"final": a, "steps": steps, "extra": ""}
    if op == "quickselect":
        ans, a, steps = quickselect(p["values"], p["k"], "hoare", "median3", p.get("cutoff", 3))
        return {"final": a, "steps": steps, "extra": f"answer: {ans}"}
    if op == "mergesort":
        a, steps = mergesort(p["values"])
        return {"final": a, "steps": steps, "extra": ""}
    if op == "insertion":
        a, steps = insertion_sort(list(p["values"]))
        inv = inversions(p["values"])
        return {"final": a, "steps": steps, "extra": f"{len(inv)} inversions: {inv}"}
    raise ValueError(op)
