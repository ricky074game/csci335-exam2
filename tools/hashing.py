"""Hash table engine that follows the Weiss textbook (4th ed., sections 5.1-5.6) and the professor's HW5 answers.

Hash function: hash(x) = x mod TableSize (integers). For other keys, give the hash values directly.
Collision strategies (h_i(x) = (hash(x) + f(i)) mod TableSize, i = 0, 1, 2, ...):
  chain     separate chaining - new items are push_back'ed to the END of the bucket's list (textbook code)
  linear    f(i) = i
  quadratic f(i) = i*i
  double    f(i) = i * hash2(x),  hash2(x) = R - (x mod R), R a prime smaller than TableSize (default 7)
Probing gives up after TableSize probes ("cannot place", as in HW5 5.1d).

Rehashing (only if asked, --rehash): textbook thresholds
  probing:  if ++currentSize > TableSize / 2 (load factor > 0.5)  -> rehash
  chaining: if ++currentSize > TableSize     (load factor > 1)    -> rehash
  new TableSize = nextPrime(2 * old TableSize); old items are re-inserted in old index order
  (for chaining: bucket 0 front to back, then bucket 1, ...). The new hash function is x mod newSize
  unless --new-mod is given (HW5 5.2 used x % 23).
Lazy deletion (probing): remove marks the cell DELETED. Textbook findPos skips DELETED cells, so a later
insert goes to the first EMPTY cell (it does NOT reuse deleted cells) unless reuse_deleted=True (Exercise 5.7).
"""

import random

EMPTY, ACTIVE, DELETED = "EMPTY", "ACTIVE", "DELETED"


def is_prime(n):
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def next_prime(n):
    if n % 2 == 0:
        n += 1
    while not is_prime(n):
        n += 2
    return n


def prev_prime_below(n):
    k = n - 1
    while k > 1 and not is_prime(k):
        k -= 1
    return k


class Table:
    def __init__(self, size, method="linear", R=None, rehash=False, reuse_deleted=False, mod=None):
        self.size = size
        self.method = method
        self.R = R if R is not None else (7 if size > 7 else prev_prime_below(size))
        self.rehash_on = rehash
        self.reuse_deleted = reuse_deleted
        self.mod = mod or size          # the hash function's modulus
        self.count = 0                  # textbook currentSize (counts DELETED cells too for probing)
        if method == "chain":
            self.buckets = [[] for _ in range(size)]
        else:
            self.cells = [None] * size
            self.info = [EMPTY] * size
        self.log = []

    # ------------------------------------------------------------ hashing
    def h(self, x):
        return x % self.mod % self.size

    def h2(self, x):
        return self.R - (x % self.R)

    def f(self, i, x):
        if self.method == "linear":
            return i
        if self.method == "quadratic":
            return i * i
        if self.method == "double":
            return i * self.h2(x)
        raise ValueError(self.method)

    # ------------------------------------------------------------ operations
    def insert(self, x, quiet=False):
        if self.method == "chain":
            b = self.h(x)
            if x in self.buckets[b]:
                msg = f"insert {x}: hash {x} mod {self.mod} = {b}; already present, not inserted"
                self.log.append(msg)
                return msg
            self.buckets[b].append(x)
            self.count += 1
            msg = f"insert {x}: hash = {x} mod {self.mod} = {b} -> appended to bucket {b}'s list"
            self.log.append(msg)
            if self.rehash_on and self.count > self.size:
                self.log.append(f"   load factor {self.count}/{self.size} > 1 -> rehash")
                self._rehash()
            return msg
        home = self.h(x)
        probes = []
        first_deleted = None
        for i in range(self.size):
            pos = (home + self.f(i, x)) % self.size
            probes.append(pos)
            st = self.info[pos]
            if st == ACTIVE and self.cells[pos] == x:
                msg = f"insert {x}: already present at {pos}, not inserted"
                self.log.append(msg)
                return msg
            if st == DELETED and self.reuse_deleted and first_deleted is None:
                first_deleted = pos
            if st == EMPTY or (st == DELETED and self.cells[pos] == x):
                break
        else:
            pos = None
        if first_deleted is not None:
            pos = first_deleted
            probes = probes[:probes.index(pos) + 1]
        if pos is None:
            extra = f"; hash2({x}) = {self.R} - ({x} mod {self.R}) = {self.h2(x)}" if self.method == "double" else ""
            msg = (f"insert {x}: home {home}{extra}; probed {', '.join(map(str, probes))} - all occupied "
                   f"-> CANNOT PLACE {x}")
            self.log.append(msg)
            return msg
        # textbook Fig 5.17: ++currentSize on every successful insert (remove never decrements it, so
        # DELETED cells keep counting toward the rehash threshold). The Exercise 5.7 variant counts only new cells.
        if not (self.reuse_deleted and self.info[pos] == DELETED):
            self.count += 1
        self.cells[pos] = x
        self.info[pos] = ACTIVE
        detail = f"hash = {x} mod {self.mod} = {home}"
        if self.method == "double" and len(probes) > 1:
            detail += f"; hash2 = {self.R} - ({x} mod {self.R}) = {self.h2(x)}"
        coll = ""
        if len(probes) > 1:
            coll = f"; collisions at {', '.join(map(str, probes[:-1]))}; tried " + ", ".join(
                f"h{i}={p}" for i, p in enumerate(probes))
        msg = f"insert {x}: {detail}{coll} -> placed at {pos}"
        self.log.append(msg)
        if self.rehash_on and self.count > self.size // 2:
            self.log.append(f"   currentSize {self.count} > TableSize/2 = {self.size // 2} -> rehash")
            self._rehash()
        return msg

    def contains(self, x):
        if self.method == "chain":
            b = self.h(x)
            return x in self.buckets[b], [b]
        home = self.h(x)
        probes = []
        for i in range(self.size):
            pos = (home + self.f(i, x)) % self.size
            probes.append(pos)
            if self.info[pos] == EMPTY:
                return False, probes
            if self.cells[pos] == x:
                return self.info[pos] == ACTIVE, probes
        return False, probes

    def remove(self, x):
        if self.method == "chain":
            b = self.h(x)
            if x in self.buckets[b]:
                self.buckets[b].remove(x)
                self.count -= 1
                msg = f"remove {x}: bucket {b} -> erased from the list"
            else:
                msg = f"remove {x}: not found in bucket {b}"
            self.log.append(msg)
            return msg
        found, probes = self.contains(x)
        if found:
            pos = probes[-1]
            self.info[pos] = DELETED
            msg = f"remove {x}: probed {', '.join(map(str, probes))} -> found at {pos}, marked DELETED (lazy deletion)"
        else:
            msg = f"remove {x}: probed {', '.join(map(str, probes))} -> not found"
        self.log.append(msg)
        return msg

    def _rehash(self):
        old = self.items_in_order()
        old_size = self.size
        self.size = next_prime(2 * old_size)
        self.mod = self.size
        self.R = self.R  # keep R unless the caller changes it
        self.count = 0
        if self.method == "chain":
            self.buckets = [[] for _ in range(self.size)]
        else:
            self.cells = [None] * self.size
            self.info = [EMPTY] * self.size
        self.log.append(f"   REHASH: new TableSize = nextPrime(2*{old_size}) = {self.size}; "
                        f"re-inserting {old} in old-table order with hash = x mod {self.size}")
        saved = self.rehash_on
        self.rehash_on = False
        for x in old:
            self.insert(x)
        self.rehash_on = saved

    def items_in_order(self):
        if self.method == "chain":
            return [x for b in self.buckets for x in b]
        return [self.cells[i] for i in range(self.size) if self.info[i] == ACTIVE]

    def load_factor(self):
        n = len(self.items_in_order())
        return n / self.size

    # ------------------------------------------------------------ display
    def snapshot(self):
        if self.method == "chain":
            return [list(b) for b in self.buckets]
        return [(self.cells[i] if self.info[i] == ACTIVE else ("D" if self.info[i] == DELETED else None))
                for i in range(self.size)]

    def text(self):
        lines = []
        for i, v in enumerate(self.snapshot()):
            if self.method == "chain":
                lines.append(f"{i:>3}: " + (" -> ".join(map(str, v)) if v else "-"))
            else:
                lines.append(f"{i:>3}: " + ("" if v is None else ("(deleted)" if v == "D" else str(v))))
        return "\n".join(lines)

    def answer_line(self):
        """Compact: 0:9679 1:4371 ... (probing) or 1:[4371] 3:[1323,6173] (chaining)."""
        out = []
        for i, v in enumerate(self.snapshot()):
            if self.method == "chain":
                if v:
                    out.append(f"{i}:[{','.join(map(str, v))}]")
            elif v is not None:
                out.append(f"{i}:{v}")
        return " ".join(out)


def run(keys, size, method, R=None, rehash=False, ops=None, reuse_deleted=False, mod=None):
    """keys: list of ints to insert, or ops: list of ('insert'|'remove'|'find', x). Returns (table, frames)."""
    t = Table(size, method, R, rehash, reuse_deleted, mod)
    frames = [("start (empty)", t.snapshot(), t.size)]
    ops = ops or [("insert", k) for k in keys]
    for op, x in ops:
        n_before = len(t.log)
        if op == "insert":
            t.insert(x)
        elif op == "remove":
            t.remove(x)
        else:
            found, probes = t.contains(x)
            t.log.append(f"find {x}: probed {', '.join(map(str, probes))} -> {'found' if found else 'not found'}")
        frames.append((" | ".join(t.log[n_before:]), t.snapshot(), t.size))
    return t, frames


def parse_ops(s):
    """'4371,1323,-6173,?99' -> insert 4371, insert 1323, remove 6173, find 99."""
    ops = []
    for part in s.replace(" ", "").split(","):
        if not part:
            continue
        if part.startswith("-"):
            ops.append(("remove", int(part[1:])))
        elif part.startswith("?"):
            ops.append(("find", int(part[1:])))
        else:
            ops.append(("insert", int(part)))
    return ops


def table_html(snap, method, hl=None):
    hl = hl or set()
    rows = []
    for i, v in enumerate(snap):
        style = " style='background:#2da44e33'" if i in hl else ""
        if method == "chain":
            cell = " &rarr; ".join(f"<span class='card' style='padding:2px 8px'>{x}</span>" for x in v) or "&nbsp;"
        else:
            cell = "" if v is None else ("<i class='muted'>deleted</i>" if v == "D" else f"<b>{v}</b>")
        rows.append(f"<tr{style}><td class='muted'>{i}</td><td style='min-width:90px'>{cell}</td></tr>")
    return "<table>" + "".join(rows) + "</table>"


def frames_html(title, frames, method):
    out = [f"<h1>{title}</h1>"]
    prev = None
    # one wide row of columns, like the HW5 answer sheet, then the step log
    head = "".join(f"<th>{'Start' if k == 0 else 'Step ' + str(k)}</th>" for k in range(len(frames)))
    size = max(len(s) for _, s, _ in frames)
    body = []
    for i in range(size):
        cells = []
        for k, (_, snap, _) in enumerate(frames):
            v = snap[i] if i < len(snap) else ""
            changed = prev is not None and k > 0 and (i >= len(frames[k - 1][1]) or frames[k - 1][1][i] != v)
            if method == "chain":
                txt = ",".join(map(str, v)) if v else ""
            else:
                txt = "" if v in (None, "") else ("del" if v == "D" else str(v))
            style = " style='background:#2da44e33'" if changed and txt else ""
            cells.append(f"<td{style}>{txt}</td>")
            prev = True
        body.append(f"<tr><td class='muted'>{i}</td>{''.join(cells)}</tr>")
    out.append(f"<table><tr><th>#</th>{head}</tr>{''.join(body)}</table>")
    out.append("<h2>What happened at each step</h2><ol>")
    for k, (label, _, _) in enumerate(frames[1:], 1):
        out.append(f"<li><code>{label}</code></li>")
    out.append("</ol>")
    return "\n".join(out)


METHOD_TEXT = {"chain": "separate chaining", "linear": "linear probing", "quadratic": "quadratic probing",
               "double": "double hashing"}


def random_problem(method, seed):
    rng = random.Random(seed)
    size = rng.choice([10, 11, 13]) if method != "double" else rng.choice([10, 11, 13])
    n = rng.randint(6, 8)
    keys = []
    # force a few collisions
    homes = rng.sample(range(size), max(2, n // 2))
    while len(keys) < n:
        base = rng.choice(homes) if rng.random() < 0.6 else rng.randrange(size)
        k = base + size * rng.randint(1, 9 if size < 12 else 7)
        if k not in keys:
            keys.append(k)
    R = 7 if size > 7 else 5
    return {"method": method, "size": size, "keys": keys, "R": R}


def describe(p):
    extra = f", hash2(x) = {p['R']} - (x mod {p['R']})" if p["method"] == "double" else ""
    return (f"Insert {', '.join(map(str, p['keys']))} (in that order) into a hash table of size {p['size']} using "
            f"hash(x) = x mod {p['size']} and {METHOD_TEXT[p['method']]}{extra}. Show the table after each "
            f"insertion (or at least the final table), and say where each collision happened.")
