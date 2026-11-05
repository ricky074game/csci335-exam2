#!/usr/bin/env python3
"""CSCI 335 Exam 2 study tracker (hashing, heaps, sorting + cumulative complexity/coding).

Everything the tutor (Claude Code) needs to pick questions, record grades and show progress.
Progress lives in progress/progress.json, which is committed and pushed to GitHub so a
`git pull` on any machine resumes where you left off.

Run `python tools/study.py -h` (or `python3 ...` on Linux) for the command list.
"""

import argparse
import json
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hashing  # noqa: E402
import heap  # noqa: E402
import sorting  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parent.parent
BANK_DIR = ROOT / "bank"
MOCK_DIR = ROOT / "mocks"
PROGRESS = ROOT / "progress" / "progress.json"

EXAM_NAME = "CSCI 335 Exam 2"
EXAM_TIME = datetime(2026, 11, 19, 14, 30)

# weight = rough share of the exam; notes = the study guide for the topic
TOPICS = {
    "analysis":   {"title": "Complexity Analysis & DS Design (cumulative)", "weight": 20, "notes": "notes/07-complexity-design.md"},
    "hashing":    {"title": "Hashing (Ch 5.1-5.6)",                       "weight": 17, "notes": "notes/01-hashing.md"},
    "quicksort":  {"title": "Quicksort, Quickselect, Partitioning",       "weight": 16, "notes": "notes/05-quicksort-quickselect.md"},
    "heaps":      {"title": "Binary Heaps & Priority Queues (Ch 6.1-6.4)", "weight": 15, "notes": "notes/03-heaps.md"},
    "coding":     {"title": "Coding with STL (hash containers, heaps...)", "weight": 14, "notes": "notes/02-stl-hash-coding.md"},
    "heapsort":   {"title": "Heapsort & Introsort",                       "weight": 9,  "notes": "notes/06-heapsort-introsort.md"},
    "sortbasics": {"title": "Insertion/Merge Sort & Lower Bounds",        "weight": 9,  "notes": "notes/04-sorting-basics.md"},
}

# generated-problem id prefix -> topic (for `record gen:...`)
GEN_TOPIC = {"heap-ins": "heaps", "heap-del": "heaps", "heap-build": "heaps", "heap-max": "heaps",
             "heapsort": "heapsort", "hash-chain": "hashing", "hash-linear": "hashing", "hash-quadratic": "hashing",
             "hash-double": "hashing", "partition": "quicksort", "quicksort": "quicksort",
             "quickselect": "quicksort", "mergesort": "sortbasics", "insertion": "sortbasics"}

QTYPES = ("coding", "trace", "analysis", "knowledge", "proof")

# Leitner boxes -> days until the next review. Box 0 = review again this session.
INTERVALS = [0, 1, 2, 4, 7]

SCORE_MEANING = {
    0: "blank / wrong idea",
    1: "major errors",
    2: "partially right",
    3: "minor slip only",
    4: "full credit",
}


# ---------------------------------------------------------------- storage

def today():
    return date.today()


def load_progress():
    if PROGRESS.exists():
        with open(PROGRESS, encoding="utf-8") as f:
            p = json.load(f)
    else:
        p = {}
    p.setdefault("version", 1)
    p.setdefault("exam", {"name": EXAM_NAME, "time": EXAM_TIME.isoformat(timespec="minutes")})
    p.setdefault("questions", {})
    p.setdefault("generated", [])
    p.setdefault("topics", {})
    p.setdefault("weak_spots", [])
    p.setdefault("mocks", [])
    p.setdefault("sessions", [])
    p.setdefault("learner", [])
    p.setdefault("student", {})
    p.setdefault("settings", {})
    for t in TOPICS:
        p["topics"].setdefault(t, {"notes_studied": None, "learn_sessions": 0})
    return p


def save_progress(p):
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    tmp = PROGRESS.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(p, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    tmp.replace(PROGRESS)


def load_bank():
    """Returns {question_id: question} with 'topic' filled in."""
    qs = {}
    for path in sorted(BANK_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for q in data["questions"]:
            q = dict(q)
            q.setdefault("topic", data["topic"])
            q["_file"] = path.name
            qs[q["id"]] = q
    return qs


def load_mocks():
    mocks = {}
    for path in sorted(MOCK_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        mocks[data["id"]] = data
    return mocks


# ---------------------------------------------------------------- scoring model

def latest_score(rec):
    return rec["attempts"][-1]["score"] if rec.get("attempts") else None


def apply_score(rec, score):
    first = not rec.get("attempts")
    box = rec.get("box", 0)
    if score >= 4:
        box = 2 if first else min(len(INTERVALS) - 1, box + 1)
    elif score == 3:
        box = 1 if first else max(1, box)
    else:
        box = 0
    rec["box"] = box
    rec["due"] = (today() + timedelta(days=INTERVALS[box])).isoformat()


def topic_stats(p, bank):
    stats = {}
    for t in TOPICS:
        ids = [qid for qid, q in bank.items() if q["topic"] == t]
        scores = []
        for qid in ids:
            s = latest_score(p["questions"].get(qid, {}))
            if s is not None:
                scores.append(s / 4)
        gen = [g["score"] / 4 for g in p["generated"] if g.get("topic") == t][-15:]
        attempted = len(scores)
        total = len(ids)
        accuracy_pool = scores + gen
        accuracy = sum(accuracy_pool) / len(accuracy_pool) if accuracy_pool else 0.0
        coverage = attempted / total if total else 0.0
        # mastery rewards both breadth (coverage) and correctness (accuracy)
        mastery = accuracy * min(1.0, coverage * 1.5 + (0.15 if gen else 0))
        due = sum(
            1 for qid in ids
            if qid in p["questions"] and p["questions"][qid].get("due", "9999") <= today().isoformat()
        )
        stats[t] = {
            "total": total, "attempted": attempted, "coverage": coverage,
            "accuracy": accuracy, "mastery": mastery, "due": due, "generated": len(gen),
        }
    return stats


def readiness(stats):
    tw = sum(TOPICS[t]["weight"] for t in TOPICS)
    return sum(TOPICS[t]["weight"] * stats[t]["mastery"] for t in TOPICS) / tw


def bar(frac, width=20):
    n = round(max(0.0, min(1.0, frac)) * width)
    return "#" * n + "." * (width - n)


def time_left():
    delta = EXAM_TIME - datetime.now()
    if delta.total_seconds() <= 0:
        return "exam time has passed"
    d = delta.days
    h = delta.seconds // 3600
    return f"{d} day{'s' if d != 1 else ''}, {h} h"


# ---------------------------------------------------------------- clocks (question timer + session clock)

CLOCK_FILE = ROOT / ".focus" / "clock.json"   # machine-local, git-ignored (.focus/)
CLOCK_RECENT_SECONDS = 30 * 60                # a stopped timer is usable by `record` for this long


def fmt_dur(seconds):
    """3m 42s / 1m 05s / 42s."""
    seconds = int(round(seconds))
    m, s = divmod(abs(seconds), 60)
    return f"{m}m {s:02d}s" if m else f"{s}s"


def load_clock():
    try:
        with open(CLOCK_FILE, encoding="utf-8") as f:
            c = json.load(f)
    except (OSError, ValueError):
        c = {}
    if not isinstance(c, dict):
        c = {}
    c.setdefault("running", None)
    c.setdefault("last", None)
    return c


def save_clock(c):
    CLOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = CLOCK_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(c, f, indent=2)
        f.write("\n")
    tmp.replace(CLOCK_FILE)


def recent_clock_seconds(qid):
    """Seconds from the last stopped timer if it was for `qid` and stopped within 30 minutes."""
    last = load_clock().get("last")
    if not last or last.get("label") != qid:
        return None
    try:
        age = (datetime.now() - datetime.fromisoformat(last["stopped"])).total_seconds()
        if age <= CLOCK_RECENT_SECONDS:
            return int(last["seconds"])
    except (KeyError, ValueError, TypeError):
        pass
    return None


def session_clock_line(p):
    """`session: 14 min used, 46 min left (planned 60, ends 14:56)`, or None if no session is open."""
    if not p["sessions"] or p["sessions"][-1].get("end"):
        return None
    cur = p["sessions"][-1]
    try:
        start = datetime.fromisoformat(cur["start"])
    except (KeyError, ValueError, TypeError):
        return None
    used = max(0, int((datetime.now() - start).total_seconds() // 60))
    planned = cur.get("planned_minutes")
    if not planned:
        return f"session: {used} min used"
    left = round(planned - used)
    ends = (start + timedelta(minutes=planned)).strftime("%H:%M")
    left_txt = f"{left} min left" if left >= 0 else f"{-left} min over"
    return f"session: {used} min used, {left_txt} (planned {planned:g}, ends {ends})"


def cmd_clock(args):
    c = load_clock()
    now = datetime.now()
    if args.action == "start":
        if not args.label:
            sys.exit("usage: clock start LABEL [--target MIN]")
        c["running"] = {"label": args.label, "started": now.isoformat(timespec="seconds"),
                        "target_min": args.target}
        save_clock(c)
        print(f"timer started: {args.label}" + (f" (target {args.target:g}m)" if args.target else ""))
    elif args.action == "stop":
        r = c.get("running")
        if not r:
            sys.exit("no timer running")
        secs = max(0, int(round((now - datetime.fromisoformat(r["started"])).total_seconds())))
        c["last"] = {"label": r["label"], "seconds": secs, "target_min": r.get("target_min"),
                     "stopped": now.isoformat(timespec="seconds")}
        c["running"] = None
        save_clock(c)
        msg = f"{r['label']}: {fmt_dur(secs)}"
        tgt = r.get("target_min")
        if tgt:
            diff = secs - round(tgt * 60)
            msg += f" (target {tgt:g}m) - {fmt_dur(diff)} " + ("over target" if diff > 0 else "under target")
        print(msg)
    else:
        r = c.get("running")
        if r:
            secs = (now - datetime.fromisoformat(r["started"])).total_seconds()
            tgt = r.get("target_min")
            print(f"timer: {r['label']} - {fmt_dur(secs)} elapsed" + (f" (target {tgt:g}m)" if tgt else ""))
        else:
            print("timer: none running")
        line = session_clock_line(load_progress())
        if line:
            print(line)


# ---------------------------------------------------------------- commands

def cmd_status(args):
    p, bank = load_progress(), load_bank()
    stats = topic_stats(p, bank)
    who = p["student"].get("name")
    print(f"== {EXAM_NAME} — {EXAM_TIME:%a %b %d, %I:%M %p} — time left: {time_left()} ==")
    if who:
        print(f"Student: {who}" + (f" · ~{p['student']['hours_per_day']:g} h/day" if p["student"].get("hours_per_day") else ""))
    else:
        print("Student: (not set up yet - run /setup)")
    print(f"Overall readiness: [{bar(readiness(stats), 30)}] {readiness(stats) * 100:.0f}%")
    print()
    print(f"{'topic':<12} {'mastery':<24} {'done':>9} {'acc':>5} {'due':>4}  notes")
    order = sorted(TOPICS, key=lambda t: stats[t]["mastery"])
    for t in order:
        s = stats[t]
        notes = p["topics"][t]["notes_studied"] or "-"
        gen = f" +{s['generated']} gen" if s["generated"] else ""
        print(f"{t:<12} [{bar(s['mastery'])}] {s['attempted']:>3}/{s['total']:<4} "
              f"{s['accuracy'] * 100:>4.0f}% {s['due']:>4}  {notes}{gen}")
    total_due = sum(s["due"] for s in stats.values())
    print()
    print(f"Questions due for review: {total_due}")
    open_weak = [w for w in p["weak_spots"] if not w.get("resolved")]
    if open_weak:
        print(f"Open weak spots ({len(open_weak)}):")
        for w in open_weak[-8:]:
            print(f"  #{w['n']} [{w.get('topic') or '-'}] {w['text']}")
    live = [x for x in p["learner"] if not x.get("retired")]
    if live:
        print(f"How this student learns ({len(live)} notes):")
        for x in live:
            print(f"  #{x['n']} [{x['kind']}] {x['text']}")
    if p["mocks"]:
        print("Mock exams:")
        for m in p["mocks"]:
            print(f"  {m['date']}  {m['id']}: {m['score']}/{m['max']} ({m['score'] / m['max'] * 100:.0f}%)")
    else:
        print("Mock exams: none taken yet")
    try:
        import focus
        print(focus.status_text())
    except Exception:  # focus mode is optional
        pass
    clock_line = session_clock_line(p)
    if clock_line:
        print(clock_line)
    if p["sessions"]:
        last = p["sessions"][-1]
        print(f"Last session: {last.get('start', '?')[:16]} — {last.get('summary') or '(no summary)'}")
    print()
    print("Weakest topics (study these next): " + ", ".join(order[:3]))


def pick_questions(p, bank, n, topic=None, qtype=None, mode="mix", rng=None):
    rng = rng or random.Random()
    stats = topic_stats(p, bank)
    pool = [q for q in bank.values()
            if (topic is None or q["topic"] == topic) and (qtype is None or q["type"] == qtype)]
    t_iso = today().isoformat()
    due = [q for q in pool if q["id"] in p["questions"] and p["questions"][q["id"]].get("due", "9999") <= t_iso]
    due.sort(key=lambda q: (p["questions"][q["id"]].get("box", 0), p["questions"][q["id"]]["due"]))
    new = [q for q in pool if q["id"] not in p["questions"]]

    def new_priority(q):
        s = stats[q["topic"]]
        need = TOPICS[q["topic"]]["weight"] * (1.2 - s["mastery"])
        diff_pref = {2: 0, 1: 0.5, 3: 1.0}.get(q.get("difficulty", 2), 0.5)
        # gentle ramp: easy questions first while a topic is fresh
        if s["attempted"] < 3:
            diff_pref = {1: 0, 2: 0.4, 3: 1.2}.get(q.get("difficulty", 2), 0.5)
        return (-need + diff_pref * 4 + rng.random() * 3)

    new.sort(key=new_priority)
    if mode == "due":
        chosen = due[:n]
    elif mode == "new":
        chosen = new[:n]
    else:
        n_due = min(len(due), max(1, n // 2)) if due else 0
        chosen = due[:n_due] + new[: n - n_due]
        if len(chosen) < n:
            chosen += [q for q in due[n_due:] if q not in chosen][: n - len(chosen)]
    # avoid back-to-back same topic when mixing
    return chosen


def cmd_next(args):
    p, bank = load_progress(), load_bank()
    chosen = pick_questions(p, bank, args.n, args.topic, args.type, args.mode)
    if not chosen:
        print("No matching questions (try a different filter, or `heap/hash/sort random` for generated traces).")
        return
    for q in chosen:
        rec = p["questions"].get(q["id"])
        state = "new" if rec is None else f"review (box {rec.get('box', 0)}, last {latest_score(rec)}/4)"
        print(f"{q['id']:<18} {q['topic']:<12} {q['type']:<10} d{q.get('difficulty', '?')} "
              f"{q.get('points', '?'):>3}pt  {state}")


def cmd_show(args):
    bank = load_bank()
    q = bank.get(args.id)
    if q is None:
        mocks = load_mocks()
        for m in mocks.values():
            for mq in m["questions"]:
                if mq["id"] == args.id:
                    q = mq
        if q is None:
            sys.exit(f"unknown question id {args.id!r}")
    print(f"[{q['id']}] {q.get('topic', '')} · {q['type']} · difficulty {q.get('difficulty', '?')} · "
          f"{q.get('points', '?')} pts · source: {q.get('source', '?')}")
    print()
    print(q["prompt"])
    if args.answer:
        print("\n---------------- MODEL ANSWER (grader only) ----------------")
        print(q["answer"])
        print("\n---------------- RUBRIC ----------------")
        for item in q["rubric"]:
            print(f"- {item}")


def cmd_record(args):
    p, bank = load_progress(), load_bank()
    if args.score not in SCORE_MEANING:
        sys.exit("score must be 0-4")
    now = datetime.now().isoformat(timespec="minutes")
    seconds = args.seconds if args.seconds is not None else recent_clock_seconds(args.id)
    took = f" ({fmt_dur(seconds)})" if seconds is not None else ""
    if args.id.startswith("gen:"):
        topic = args.topic or GEN_TOPIC.get(args.id.split(":")[1] if ":" in args.id else "", "analysis")
        entry = {"id": args.id, "topic": topic, "score": args.score,
                 "date": now, "note": args.note or ""}
        if seconds is not None:
            entry["seconds"] = seconds
        p["generated"].append(entry)
        save_progress(p)
        print(f"recorded generated {args.id}: {args.score}/4 ({SCORE_MEANING[args.score]}){took}")
        return
    if args.id not in bank:
        sys.exit(f"unknown question id {args.id!r}")
    rec = p["questions"].setdefault(args.id, {"attempts": []})
    apply_score(rec, args.score)
    attempt = {"date": now, "score": args.score, "note": args.note or ""}
    if seconds is not None:
        attempt["seconds"] = seconds
    rec["attempts"].append(attempt)
    save_progress(p)
    print(f"recorded {args.id}: {args.score}/4 ({SCORE_MEANING[args.score]}) -> box {rec['box']}, "
          f"next review {rec['due']}{took}")


def cmd_weak(args):
    p = load_progress()
    if args.action == "add":
        n = max([w["n"] for w in p["weak_spots"]] or [0]) + 1
        p["weak_spots"].append({"n": n, "topic": args.topic, "text": args.text,
                                "added": today().isoformat(), "resolved": None})
        save_progress(p)
        print(f"added weak spot #{n}")
    elif args.action == "resolve":
        for w in p["weak_spots"]:
            if w["n"] == int(args.text):
                w["resolved"] = today().isoformat()
        save_progress(p)
        print(f"resolved #{args.text}")
    else:
        for w in p["weak_spots"]:
            mark = "x" if w.get("resolved") else " "
            print(f"[{mark}] #{w['n']} [{w.get('topic') or '-'}] {w['text']}  (added {w['added']})")


def cmd_style(args):
    """Learner profile: how this student learns best (read at the start of every session)."""
    p = load_progress()
    if args.action == "add":
        n = max([x["n"] for x in p["learner"]] or [0]) + 1
        p["learner"].append({"n": n, "kind": args.kind, "text": args.text, "added": today().isoformat(),
                             "retired": None})
        save_progress(p)
        print(f"added learner note #{n} [{args.kind}]")
    elif args.action == "retire":
        for x in p["learner"]:
            if x["n"] == int(args.text):
                x["retired"] = today().isoformat()
        save_progress(p)
        print(f"retired learner note #{args.text}")
    else:
        live = [x for x in p["learner"] if not x.get("retired")]
        if not live:
            print("no learner notes yet - observe how the student learns and add some")
        for x in live:
            print(f"#{x['n']} [{x['kind']}] {x['text']}  ({x['added']})")


def cmd_topic(args):
    p = load_progress()
    if args.topic not in TOPICS:
        sys.exit(f"unknown topic; choose from {', '.join(TOPICS)}")
    t = p["topics"][args.topic]
    t["notes_studied"] = today().isoformat()
    t["learn_sessions"] = t.get("learn_sessions", 0) + 1
    save_progress(p)
    print(f"marked {args.topic} notes studied ({t['learn_sessions']} learn session(s))")


def cmd_topics(args):
    for t, info in TOPICS.items():
        print(f"{t:<12} weight {info['weight']:>2}%  {info['title']:<36} {info['notes']}")


def cmd_session(args):
    p = load_progress()
    now = datetime.now().isoformat(timespec="minutes")
    if args.action == "start":
        sess = {"start": now, "end": None, "summary": None}
        if args.minutes:
            sess["planned_minutes"] = args.minutes
        p["sessions"].append(sess)
        print(f"session started {now}" + (f" (planned {args.minutes:g} min)" if args.minutes else ""))
    else:
        if not p["sessions"] or p["sessions"][-1].get("end"):
            p["sessions"].append({"start": now, "end": None, "summary": None})
        p["sessions"][-1]["end"] = now
        p["sessions"][-1]["summary"] = args.summary
        print(f"session ended {now}")
    save_progress(p)


def cmd_mock(args):
    mocks = load_mocks()
    p = load_progress()
    if args.action == "list":
        taken = {}
        for m in p["mocks"]:
            taken.setdefault(m["id"], []).append(f"{m['score']}/{m['max']}")
        for mid, m in mocks.items():
            qs = m["questions"]
            print(f"{mid:<8} {m['title']:<20} {len(qs)} questions, {m['total_points']} pts, "
                  f"{m['minutes']} min   taken: {', '.join(taken.get(mid, [])) or 'never'}")
    elif args.action == "show":
        m = mocks.get(args.id) or sys.exit(f"unknown mock {args.id!r}")
        print(f"# {m['title']}  ({m['minutes']} minutes, {m['total_points']} points)\n")
        print(m["instructions"] + "\n")
        for i, q in enumerate(m["questions"], 1):
            print(f"## Question {i}  [{q['points']} points]   ({q['id']})\n")
            print(q["prompt"] + "\n")
            if args.answers:
                print("**MODEL ANSWER (grader only):**\n" + q["answer"] + "\n")
                print("**RUBRIC:**\n" + "\n".join(f"- {r}" for r in q["rubric"]) + "\n")
    elif args.action == "record":
        m = mocks.get(args.id) or sys.exit(f"unknown mock {args.id!r}")
        scores = {}
        for part in (args.scores or "").split(","):
            if part.strip():
                k, v = part.split("=")
                scores[k.strip()] = float(v)
        valid = {q["id"]: q["points"] for q in m["questions"]}
        bad = [k for k in scores if k not in valid]
        if bad:
            sys.exit(f"unknown question ids: {bad}; expected {list(valid)}")
        missing = [k for k in valid if k not in scores]
        if missing:
            sys.exit(f"missing scores for {missing}")
        total = sum(scores.values())
        p["mocks"].append({"id": args.id, "date": today().isoformat(), "score": total,
                           "max": m["total_points"], "breakdown": scores, "minutes_used": args.minutes})
        save_progress(p)
        print(f"recorded {args.id}: {total}/{m['total_points']} ({total / m['total_points'] * 100:.0f}%)")


ANSWER_DIR = ROOT / "answers"


def _find_question(qid):
    q = load_bank().get(qid)
    if q is not None:
        return q
    for m in load_mocks().values():
        for mq in m["questions"]:
            if mq["id"] == qid:
                return mq
    return None


def _comment_block(text, prefix):
    return "\n".join((prefix + line).rstrip() for line in text.splitlines())


CPP_MARKER = "// ===== YOUR ANSWER ====="
MD_MARKER = "<!-- ===== YOUR ANSWER ===== -->"
EDITOR = Path(__file__).resolve().parent / "editor.py"


def answer_part(path):
    """The text below the answer marker (what the student wrote)."""
    text = path.read_text(encoding="utf-8")
    for marker in (CPP_MARKER, MD_MARKER):
        if marker in text:
            return text.split(marker, 1)[1].strip("\n")
    return text


def run_editor(path, minutes=None, title=None, wait=True):
    """Open the exam editor. With wait=True, blocks until the student submits/closes, then prints
    the result and their answer, so the caller (Claude) gets it directly."""
    import subprocess
    cmd = [sys.executable, str(EDITOR), str(path)]
    if minutes:
        cmd += ["--minutes", f"{minutes:g}"]
    if title:
        cmd += ["--title", title]
    rel = path.relative_to(ROOT).as_posix()
    if not wait:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"editor opened for {rel} (not waiting) - read the file when the student says done")
        return
    print(f"editor open for {rel} - waiting for the student to submit...", flush=True)
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    result = {}
    for line in reversed((proc.stdout or "").strip().splitlines()):
        try:
            result = json.loads(line)
            break
        except ValueError:
            continue
    if result.get("status") == "error" or proc.returncode not in (0,):
        print(f"EDITOR FAILED: {result.get('error') or proc.stderr.strip()[-500:]}")
        print(f"Fallback: the student can edit {rel} in any text editor and say done.")
        return
    m, sec = divmod(int(result.get("seconds", 0)), 60)
    print(f"STUDENT {result.get('status', '?').upper()} after {m} min {sec} s")
    print(f"----- answer from {rel} -----")
    print(answer_part(path) or "(empty)")


def given_stub(q):
    """If the question prints a function for the student to complete (like the exam's
    `void ReversePrintMultiples(...){ // write code here }`), return that stub so the answer
    starts from it, exactly as on the paper exam. Class declarations, buggy code to debug, etc.
    are context, not stubs, and stay in the question pane only."""
    if q.get("type") != "coding":
        return ""
    import re
    for block in re.findall(r"```(?:cpp|c\+\+)?\n(.*?)```", q["prompt"], re.S):
        lines = [ln for ln in block.strip("\n").splitlines()]
        first = next((ln.strip() for ln in lines if ln.strip()), "")
        if re.match(r"(class|struct|template|#include)\b", first):
            continue
        if re.search(r"//\s*(write|your|insert)\b.*code", block, re.I) and "(" in first:
            return block.rstrip() + "\n"
    return ""


def cmd_answer(args):
    """Create answers/<id>.<ext> with the question on top and an answer area, then open the editor."""
    q = _find_question(args.id)
    if q is None:
        sys.exit(f"unknown question id {args.id!r}")
    ANSWER_DIR.mkdir(exist_ok=True)
    ext = args.ext or (".cpp" if q["type"] == "coding" else ".md")
    path = ANSWER_DIR / f"{args.id}{ext}"
    budget = args.minutes if args.minutes is not None else round(max(2, q.get("points", 5) * 0.65))
    if path.exists() and not args.fresh:
        print(f"exists (keeping previous work): {path.relative_to(ROOT).as_posix()}")
    else:
        header = f"{q['id']} · {q['type']} · {q.get('points', '?')} pts · suggested {budget} min\n\n{q['prompt']}"
        if ext == ".cpp":
            body = ("/*\n" + _comment_block(header.replace("*/", "* /"), " * ") + "\n */\n" + CPP_MARKER + "\n"
                    + (given_stub(q) or "\n"))
        else:
            body = _comment_block(header, "> ") + "\n" + MD_MARKER + "\n\n"
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
        print(f"created: {path.relative_to(ROOT).as_posix()}")
    if args.no_open:
        return
    run_editor(path, minutes=budget, title=f"{q['id']} — {q['type']}, {q.get('points', '?')} pts",
               wait=not args.no_wait)


def close_study_browser():
    """Close the study browser window (the mock-exam window takes its place)."""
    import os
    import signal
    pid_file = FOCUS_DIR / "browser.pid"
    if not _browser_running():
        return
    try:
        os.kill(int(pid_file.read_text().strip()), signal.SIGTERM)
        print("closed the study browser")
    except (OSError, ValueError):
        pass


def cmd_sheet(args):
    """Open the mock-exam window (one question at a time, a box per part, arrows), or with --classic the
    single-file editor sheet. Either way the answers end up in answers/<mock>-<time>.md."""
    m = load_mocks().get(args.id) or sys.exit(f"unknown mock {args.id!r}")
    ANSWER_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    if not args.classic:
        import subprocess
        state = Path(args.resume) if args.resume else ANSWER_DIR / f"{args.id}-{stamp}.json"
        if not state.is_absolute():
            state = (ROOT / state).resolve()
        md = state.with_suffix(".md")
        print(f"answers: {md.relative_to(ROOT).as_posix()} (state {state.name})")
        if args.no_open:
            return
        close_study_browser()
        mock_file = ROOT / "mocks" / f"{args.id}.json"
        cmd = [sys.executable, str(Path(__file__).resolve().parent / "mockui.py"), str(mock_file), str(state),
               "--minutes", f"{m['minutes']:g}", "--place", "left60"]
        try:
            import winplace
            print(winplace.arrange_terminal("right40"))
        except Exception:  # noqa: BLE001
            pass
        print(f"exam window open ({m['minutes']} min) - waiting for the student to submit...", flush=True)
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        result = {}
        for line in reversed((proc.stdout or "").strip().splitlines()):
            try:
                result = json.loads(line)
                break
            except ValueError:
                continue
        if result.get("status") == "error" or proc.returncode != 0:
            print(f"EXAM WINDOW FAILED: {result.get('error') or proc.stderr.strip()[-800:]}")
            print(f"Fallback: study sheet {args.id} --classic")
            return
        mins, sec = divmod(int(result.get("seconds", 0)), 60)
        print(f"STUDENT {result.get('status', '?').upper()} after {mins} min {sec} s")
        print(f"----- answers from {md.relative_to(ROOT).as_posix()} -----")
        print(md.read_text(encoding="utf-8") if md.exists() else "(empty)")
        return
    path = ANSWER_DIR / f"{args.id}-{stamp}.md"
    head = [f"# {m['title']} — {m['minutes']} minutes, {m['total_points']} points",
            f"Started: {datetime.now():%Y-%m-%d %H:%M}", "", m["instructions"], ""]
    for i, q in enumerate(m["questions"], 1):
        head += ["=" * 60, f"QUESTION {i}   [{q['points']} points]   ({q['id']})", "", q["prompt"], ""]
    answers = []
    for i, q in enumerate(m["questions"], 1):
        answers += [f"### Question {i} ({q['id']}) [{q['points']} pts]", "", "", ""]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(_comment_block("\n".join(head), "> ") + "\n" + MD_MARKER + "\n\n" + "\n".join(answers) + "\n")
    print(f"created: {path.relative_to(ROOT).as_posix()}")
    if args.no_open:
        return
    run_editor(path, minutes=m["minutes"], title=f"{m['title']} — {m['minutes']} minutes", wait=not args.no_wait)


def cmd_edit(args):
    """Open any file (e.g. a reopened answer) in the exam editor."""
    path = Path(args.path)
    if not path.is_absolute():
        path = (ROOT / path).resolve()
    if not path.exists():
        sys.exit(f"no such file {path}")
    run_editor(path, minutes=args.minutes, wait=not args.no_wait)


def cmd_focus(args):
    import focus
    if args.action == "start":
        print(focus.start(args.minutes))
    elif args.action == "status":
        print(focus.status_text())
    elif args.action == "end":
        print(focus.end())
    elif args.action == "stop":
        print(focus.stop(args.reason))
    elif args.action == "config":
        print(focus.configure(args.reason or "show", args.value))


def browser_python():
    """Python for the study browser: the repo-local .venv if present (has the GUI packages), else this one."""
    import os
    venv = ROOT / ".venv" / ("Scripts/pythonw.exe" if os.name == "nt" else "bin/python")
    if venv.exists():
        return str(venv)
    if os.name == "nt":
        pyw = Path(sys.executable).with_name("pythonw.exe")
        if pyw.exists():
            return str(pyw)
    return sys.executable


def browser_script():
    """Windows: Edge WebView2 engine (pywebview). Linux/macOS: Qt WebEngine."""
    import os
    name = "studybrowser_win.py" if os.name == "nt" else "studybrowser.py"
    return Path(__file__).resolve().parent / name


def browser_ready():
    import os
    import subprocess
    mod = "webview" if os.name == "nt" else "PyQt6.QtWebEngineWidgets"
    py = browser_python().replace("pythonw.exe", "python.exe")
    if subprocess.run([py, "-c", f"import {mod}, markdown"], capture_output=True).returncode == 0:
        return True
    if os.name == "nt":
        print("study browser not installed. Run:  python -m pip install --user uv  then  "
              "uv venv --python 3.12 .venv  and  uv pip install --python .venv/Scripts/python.exe -r requirements-windows.txt")
    else:
        print("study browser not installed. Run:  python3 -m venv .venv && .venv/bin/pip install -r requirements.txt")
    return False


def cmd_browse(args):
    show_in_browser(args.target or "", place=None, terminal=None)


def cmd_validate(args):
    ok = True
    ids = set()
    for path in sorted(BANK_DIR.glob("*.json")):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"{path.name}: INVALID JSON: {e}")
            ok = False
            continue
        if data.get("topic") not in TOPICS:
            print(f"{path.name}: unknown topic {data.get('topic')!r}")
            ok = False
        counts = {}
        for q in data["questions"]:
            for k in ("id", "type", "difficulty", "source", "tags", "points", "prompt", "answer", "rubric"):
                if k not in q:
                    print(f"{path.name}: {q.get('id', '?')} missing {k}")
                    ok = False
            if q.get("type") not in QTYPES:
                print(f"{path.name}: {q.get('id')} bad type {q.get('type')!r}")
                ok = False
            if q.get("id") in ids:
                print(f"{path.name}: duplicate id {q.get('id')}")
                ok = False
            ids.add(q.get("id"))
            counts[q.get("type")] = counts.get(q.get("type"), 0) + 1
        print(f"{path.name:<20} {len(data['questions']):>3} questions  " +
              " ".join(f"{k}:{v}" for k, v in sorted(counts.items())))
    for path in sorted(MOCK_DIR.glob("*.json")):
        try:
            with open(path, encoding="utf-8") as f:
                m = json.load(f)
            pts = sum(q["points"] for q in m["questions"])
            flag = "" if pts == m["total_points"] else f"  POINTS MISMATCH ({pts})"
            ok = ok and not flag
            print(f"{path.name:<20} {len(m['questions']):>3} questions  {pts} pts{flag}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"{path.name}: INVALID: {e}")
            ok = False
    print("all valid" if ok else "PROBLEMS FOUND")
    sys.exit(0 if ok else 1)


# ---------------------------------------------------------------- trace engines: heaps, hashing, sorting

def _vals(s):
    return [int(v) for v in (s or "").replace(" ", "").replace(";", ",").split(",") if v != ""]


def _parse_gen(gen_id):
    parts = gen_id.split(":")
    if len(parts) != 3 or parts[0] != "gen":
        sys.exit(f"bad generated id {gen_id!r} (expected gen:<kind>:<seed>)")
    return parts[1], int(parts[2])


def _show_page(name, title, body, place="left60"):
    path = write_view(name, title, body)
    show_in_browser(str(path), place=place, terminal="right40" if place not in (None, "none") else None)


def _heap_steps_text(steps, start=1):
    out = []
    for label, snap in steps:
        if start == 1:
            out.append(f"  {heap.fmt(snap):<46} # {label}")
        else:
            out.append(f"  {' '.join(map(str, snap)):<40} # {label}")
    return "\n".join(out)


def _compare_arrays(expected, given_text):
    given = _vals(given_text)
    ok = given == expected
    return ok, f"expected {','.join(map(str, expected))}, got {','.join(map(str, given))}"


def cmd_heap(args):
    a = args.action
    kind = "max" if args.max else "min"
    if a == "random":
        k = {"ins": "heap-ins", "del": "heap-del", "build": "heap-build", "max": "heap-max",
             "sort": "heapsort"}[args.kind] if args.kind != "any" else random.choice(
            ["heap-ins", "heap-del", "heap-build", "heap-max", "heapsort"])
        seed = args.seed if args.seed is not None else random.randrange(10**6)
        prob = heap.random_problem(k, seed)
        print(f"Problem id: gen:{k}:{seed}\n")
        print(heap.describe(prob))
        return
    if a in ("solve", "grade"):
        k, seed = _parse_gen(args.arg)
        prob = heap.random_problem(k, seed)
        final, steps, extra = heap.solve(prob)
        if a == "solve":
            print(heap.describe(prob) + "\n")
            print(_heap_steps_text(steps, 0 if k == "heapsort" else 1))
            print(f"\nfinal: {final}" + (f"   {extra}" if extra else ""))
            if args.show:
                _heap_page(k, prob, steps)
            return
        exp = _vals(final)
        ok, detail = _compare_arrays(exp, args.array or "")
        print(("OK    final array" if ok else f"WRONG final array: {detail}"))
        if not ok:
            given = _vals(args.array or "")
            diff = [i for i in range(max(len(exp), len(given)))
                    if i >= len(exp) or i >= len(given) or exp[i] != given[i]]
            base = 0 if k == "heapsort" else 1
            print(f"first difference at index {diff[0] + base}" if diff else "")
        return
    if a == "check":
        arr = heap.from_list(_vals(args.arg))
        bad = heap.is_heap(arr, kind)
        print(f"valid {kind}-heap" if not bad else f"NOT a {kind}-heap:\n  " + "\n  ".join(bad))
        return
    if a == "insert":
        arr = heap.from_list(_vals(args.arg))
        steps = []
        for x in _vals(args.rest[0] if args.rest else ""):
            arr, _ = heap.insert(arr, x, kind, steps)
        title = f"{kind}-heap insert {args.rest[0] if args.rest else ''}"
    elif a == "delete":
        arr = heap.from_list(_vals(args.arg))
        steps, outs = [], []
        for _ in range(args.count):
            arr, top, _ = heap.delete_min(arr, kind, steps)
            outs.append(top)
        title = f"{kind}-heap delete{'Min' if kind == 'min' else 'Max'} x{args.count} (removed {outs})"
    elif a == "build":
        arr, steps = heap.build_heap(_vals(args.arg), kind, detail=args.detail)
        title = f"buildHeap ({kind}-heap)"
    elif a in ("decrease", "increase", "remove"):
        arr = heap.from_list(_vals(args.arg))
        pos = int(args.rest[0])
        if a == "remove":
            arr, gone, steps = heap.remove_at(arr, pos, kind)
            title = f"remove(index {pos}) = {gone}"
        else:
            delta = int(args.rest[1])
            fn = heap.decrease_key if a == "decrease" else heap.increase_key
            arr, steps = fn(arr, pos, delta, kind)
            title = f"{a}Key({pos}, {delta})"
    elif a == "sort":
        res, steps = heap.heapsort(_vals(args.arg))
        print(f"heapsort {args.arg}  (textbook Fig. 7.10: 0-indexed max-heap)\n")
        print(_heap_steps_text(steps, 0))
        print(f"\nsorted: {','.join(map(str, res))}")
        if args.show:
            _show_page("heapsort", "Heapsort", heap.steps_html("Heapsort", steps, start=0, sorted_tail=True), args.place)
        return
    else:
        sys.exit(f"unknown heap action {a}")
    print(f"{title}\n")
    print(_heap_steps_text(steps))
    print(f"\nfinal heap (from index 1): {heap.plain(arr)}")
    if args.show:
        _show_page(f"heap-{a}", title, heap.steps_html(title, steps), args.place)


def _heap_page(k, prob, steps):
    if k == "heapsort":
        _show_page("heapsort", "Heapsort", heap.steps_html("Heapsort", steps, start=0, sorted_tail=True))
    else:
        _show_page(f"{k}", k, heap.steps_html(heap.describe(prob).splitlines()[0], steps))


def cmd_hash(args):
    a = args.action
    if a == "random":
        m = args.method if args.method != "any" else random.choice(["chain", "linear", "quadratic", "double"])
        seed = args.seed if args.seed is not None else random.randrange(10**6)
        prob = hashing.random_problem(m, seed)
        print(f"Problem id: gen:hash-{m}:{seed}\n")
        print(hashing.describe(prob))
        return
    if a in ("solve", "grade"):
        k, seed = _parse_gen(args.arg)
        m = k.split("-", 1)[1]
        prob = hashing.random_problem(m, seed)
        t, frames = hashing.run(prob["keys"], prob["size"], m, prob["R"])
        if a == "solve":
            print(hashing.describe(prob) + "\n")
            print("\n".join(t.log))
            print("\n" + t.text())
            print(f"\nanswer line: {t.answer_line()}")
            if args.show:
                _show_page(f"hash-{m}", f"Hashing - {hashing.METHOD_TEXT[m]}",
                           hashing.frames_html(hashing.describe(prob), frames, m), args.place)
            return
        given = " ".join((args.table or "").split())
        ok = given == t.answer_line()
        print("OK    final table" if ok else f"WRONG final table:\n  expected {t.answer_line()}\n  got      {given}")
        return
    if a == "prime":
        n = int(args.arg)
        print(f"nextPrime({n}) = {hashing.next_prime(n)};  is {n} prime? {hashing.is_prime(n)};  "
              f"nextPrime(2*{n}) = {hashing.next_prime(2 * n)}")
        return
    if a == "run":
        ops = hashing.parse_ops(args.arg)
        t, frames = hashing.run([], args.size, args.method, args.R, args.rehash, ops, args.reuse_deleted, args.mod)
        print(f"{hashing.METHOD_TEXT[args.method]}, TableSize {args.size}, hash(x) = x mod {args.mod or args.size}"
              + (f", hash2(x) = {t.R} - (x mod {t.R})" if args.method == "double" else "")
              + (" (rehash on: textbook thresholds)" if args.rehash else "") + "\n")
        print("\n".join(t.log))
        print("\n" + t.text())
        print(f"\nload factor {len(t.items_in_order())}/{t.size} = {t.load_factor():.2f}")
        print(f"answer line: {t.answer_line()}")
        if args.show:
            _show_page(f"hash-{args.method}", f"Hashing - {hashing.METHOD_TEXT[args.method]}",
                       hashing.frames_html(f"{hashing.METHOD_TEXT[args.method]} (size {args.size})", frames,
                                           args.method), args.place)
        return
    sys.exit(f"unknown hash action {a}")


def _pivot_opts(args):
    pv = args.pivot
    if pv.isdigit():
        return "index", int(pv)
    return pv, None


def cmd_sort(args):
    a = args.action
    if a == "random":
        k = args.kind if args.kind != "any" else random.choice(
            ["partition", "partition", "quicksort", "quickselect", "mergesort", "insertion"])
        seed = args.seed if args.seed is not None else random.randrange(10**6)
        prob = sorting.random_problem(k, seed)
        print(f"Problem id: gen:{k}:{seed}\n")
        print(sorting.describe(prob))
        return
    if a in ("solve", "grade"):
        k, seed = _parse_gen(args.arg)
        prob = sorting.random_problem(k, seed)
        res = sorting.solve(prob)
        if a == "solve":
            print(sorting.describe(prob) + "\n")
            print(sorting.steps_text(res["steps"]))
            print(f"\nfinal: {','.join(map(str, res['final']))}" + (f"   {res['extra']}" if res["extra"] else ""))
            if args.show:
                _show_page(k, k, sorting.steps_html(sorting.describe(prob).splitlines()[0], prob["values"],
                                                    res["steps"]), args.place)
            return
        if args.answer is not None and k == "quickselect":
            ans = int(res["extra"].split(":")[1])
            print("OK    answer" if int(args.answer) == ans else f"WRONG answer: expected {ans}, got {args.answer}")
        if args.array is not None:
            ok, detail = _compare_arrays(res["final"], args.array)
            print("OK    final array" if ok else f"WRONG final array: {detail}")
        if args.steps is not None:
            # each ';'-separated array is checked against the engine's snapshots in order
            want = [s["array"] for s in res["steps"]]
            given = [_vals(x) for x in args.steps.split(";") if x.strip()]
            pos = 0
            for g in given:
                while pos < len(want) and want[pos] != g:
                    pos += 1
                if pos == len(want):
                    print(f"WRONG step {','.join(map(str, g))} - not a state the textbook algorithm reaches "
                          f"(in this order)")
                    break
                pos += 1
            else:
                print(f"OK    all {len(given)} intermediate arrays match textbook states in order")
        return
    vals = _vals(args.arg)
    if a == "inversions":
        inv = sorting.inversions(vals)
        print(f"{len(inv)} inversions: {inv}\naverage for n={len(vals)}: n(n-1)/4 = {len(vals) * (len(vals) - 1) / 4:g}")
        return
    title = ""
    if a == "partition":
        how, given = _pivot_opts(args)
        arr = list(vals)
        steps = []
        i = sorting.partition(arr, 0, len(arr) - 1, args.method, how, given, steps)
        title = f"{args.method} partition, pivot {args.pivot}"
        extra = f"pivot ends at index {i}"
    elif a == "quick":
        how, given = _pivot_opts(args)
        arr, steps = sorting.quicksort(vals, args.method, how, args.cutoff, given)
        title = f"quicksort ({args.method}, pivot {args.pivot}, cutoff {args.cutoff})"
        extra = ""
    elif a == "select":
        how, given = _pivot_opts(args)
        ans, arr, steps = sorting.quickselect(vals, args.k, args.method, how, args.cutoff, given)
        title = f"quickselect k={args.k} ({args.method}, pivot {args.pivot}, cutoff {args.cutoff})"
        extra = f"k={args.k} smallest = {ans}"
    elif a == "merge":
        arr, steps = sorting.mergesort(vals)
        title, extra = "mergesort", ""
    elif a == "insertion":
        arr, steps = sorting.insertion_sort(list(vals))
        title, extra = "insertion sort", f"{len(sorting.inversions(vals))} inversions"
    elif a == "heap":
        args.action = "sort"
        return cmd_heap(args)
    else:
        sys.exit(f"unknown sort action {a}")
    print(f"{title}: {','.join(map(str, vals))}\n")
    print(sorting.steps_text(steps))
    print(f"\nfinal: {','.join(map(str, arr))}" + (f"   {extra}" if extra else ""))
    if args.show:
        _show_page(f"sort-{a}", title, sorting.steps_html(title, vals, steps), args.place)


def cmd_setup(args):
    import studysetup as su
    a = args.action
    if a == "check":
        print(su.check(load_progress()))
    elif a == "name":
        if not args.arg:
            sys.exit('usage: setup name "Your Name" [--hours H]')
        p = load_progress()
        print(su.set_name(p, " ".join(args.arg), args.hours))
        save_progress(p)
    elif a == "textbook":
        if not args.arg:
            sys.exit("usage: setup textbook <path to the Weiss PDF>")
        print(su.textbook(" ".join(args.arg)))
    elif a == "material":
        if not args.arg:
            sys.exit("usage: setup material <zip> [<zip> ...]")
        print(su.material(args.arg))
    elif a == "browser":
        print(su.browser())
    elif a == "allowlist":
        print(su.allowlist())
    elif a == "repo-info":
        print(su.repo_info())


# ---------------------------------------------------------------- showing things on screen

FOCUS_DIR = ROOT / ".focus"
VIEWS = FOCUS_DIR / "browser" / "views"


def _browser_running():
    import focus
    pid_file = FOCUS_DIR / "browser.pid"
    try:
        pid = int(pid_file.read_text().strip())
    except (OSError, ValueError):
        return False
    return focus.pid_alive(pid)


def show_in_browser(target, find=None, place="left60", terminal="right40"):
    """Open/steer the study browser to `target` (URL, repo file, or generated page) and lay out windows."""
    import os
    import subprocess
    import winplace
    place = None if place in (None, "none") else place
    if _browser_running():
        FOCUS_DIR.mkdir(exist_ok=True)
        cmd = {"open": target, "find": find, "place": place}
        tmp = FOCUS_DIR / "browser_cmd.tmp"
        tmp.write_text(json.dumps(cmd), encoding="utf-8")
        tmp.replace(FOCUS_DIR / "browser_cmd.json")
        how = "steered the open study browser"
    else:
        if not browser_ready():
            return
        args = [browser_python(), str(browser_script()), target]
        if place:
            args += ["--place", place]
        if find:
            args += ["--find", find]
        kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        if os.name == "nt":
            kwargs["creationflags"] = 0x00000008 | 0x00000200
        else:
            kwargs["start_new_session"] = True
        subprocess.Popen(args, **kwargs)
        how = "opened the study browser"
    msg = f"{how}: {target or 'idle page'}" + (f" (highlighting '{find}')" if find else "")
    if terminal and terminal != "none" and place:
        msg += "; " + winplace.arrange_terminal(terminal)
    print(msg)


def write_view(name, title, body):
    from pagestyle import page
    VIEWS.mkdir(parents=True, exist_ok=True)
    path = VIEWS / f"{name}.html"
    extra = "<style>.pic{overflow-x:auto;padding:6px 0 14px}.pic svg{color:var(--fg)}</style>"
    path.write_text(page(title, extra + body), encoding="utf-8")
    return path


def cmd_viz(args):
    import viz
    k, a = args.kind, args.arg
    try:
        if k == "memory":
            name, title, body = viz.memory(viz.parse_values(a or "7,2,5,9,4"))
        elif k == "erase":
            name, title, body = viz.erase(viz.parse_values(a or "7,2,5,9,4"), args.at)
        elif k == "eraseloop":
            name, title, body = viz.erase_loop(viz.parse_values(a or "1,3,4"), args.remove, args.container, args.fixed)
        elif k == "overwriter":
            name, title, body = viz.overwriter(viz.parse_values(a or "7,-2,5,-1,4"), args.remove)
        elif k == "move":
            name, title, body = viz.move(args.op, args.members, args.cls)
        elif k == "loops":
            kinds = args.kinds.split(",") if args.kinds else None
            name, title, body = viz.loops(kinds, args.n)
        elif k == "iterators":
            name, title, body = viz.iterators()
        elif k == "costs":
            name, title, body = viz.costs()
        elif k == "bst":
            name, title, body = viz.bst(a, args.rest[0], int(args.rest[1]))
        else:  # page
            name, title, body = viz.page(a, args.title)
    except (ValueError, IndexError, KeyError, OSError) as e:
        sys.exit(f"viz {k}: {e}")
    path = write_view(name, args.title or title, body)
    if args.no_open:
        print(f"wrote {path}")
    else:
        show_in_browser(str(path), place=args.place, terminal="right40" if args.place != "none" else None)


def cmd_view(args):
    target = args.target or ""
    if args.section and target.endswith(".md"):
        args.find = args.find or args.section
    show_in_browser(target, find=args.find, place=args.place, terminal=args.terminal)


def cmd_layout(args):
    import winplace
    if args.preset == "study":      # browser left, terminal right
        show_in_browser("", place="left60", terminal="right40")
    elif args.preset == "terminal":  # terminal back to full screen
        print(winplace.arrange_terminal("full"))
    elif args.preset == "editor":    # terminal right, editor gets the left (editor places itself)
        print(winplace.arrange_terminal("right40"))


# ---------------------------------------------------------------- text to speech

def _settings():
    p = load_progress()
    return p, p.setdefault("settings", {})


def speak(text):
    """Speak text with the OS voice, without blocking. Returns False if no voice is available."""
    import os
    import shutil
    import subprocess
    if not text.strip():
        return True
    if os.name == "nt":
        safe = text.replace("'", "''")
        ps = ("Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
              f"$s.Rate = 1; $s.Speak('{safe}')")
        subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=0x08000000)
        return True
    for exe, args in (("spd-say", ["-r", "10"]), ("espeak-ng", []), ("espeak", [])):
        if shutil.which(exe):
            subprocess.Popen([exe, *args, text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
    return False


def cmd_tts(args):
    p, st = _settings()
    if args.action in ("on", "off"):
        st["tts"] = args.action == "on"
        save_progress(p)
        print(f"text-to-speech {args.action}")
        if args.action == "on" and not speak("Voice on. I'll read out the key takeaways."):
            print("no voice found - Linux: sudo apt install speech-dispatcher (spd-say) or espeak-ng")
    else:
        print(f"text-to-speech is {'on' if st.get('tts') else 'off'}")


def cmd_say(args):
    _, st = _settings()
    if not st.get("tts") and not args.force:
        print("(tts is off - not spoken)")
        return
    print("spoken" if speak(args.text) else "no voice available")


# ---------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser(description="CSCI 335 Exam 2 study tracker")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("clock", help="question timer + session clock: clock start LABEL [--target MIN] | stop | (none)")
    s.add_argument("action", nargs="?", choices=("start", "stop"))
    s.add_argument("label", nargs="?")
    s.add_argument("--target", type=float, help="target minutes for this question")
    s.set_defaults(func=cmd_clock)

    sub.add_parser("status", help="progress dashboard").set_defaults(func=cmd_status)
    sub.add_parser("topics", help="list topics").set_defaults(func=cmd_topics)
    sub.add_parser("validate", help="check bank/ and mocks/ files").set_defaults(func=cmd_validate)

    s = sub.add_parser("next", help="pick the next questions to practice")
    s.add_argument("--n", type=int, default=5)
    s.add_argument("--topic", choices=list(TOPICS))
    s.add_argument("--type", choices=QTYPES)
    s.add_argument("--mode", choices=("mix", "due", "new"), default="mix")
    s.set_defaults(func=cmd_next)

    s = sub.add_parser("show", help="print a question (add --answer for the grader view)")
    s.add_argument("id")
    s.add_argument("--answer", action="store_true")
    s.set_defaults(func=cmd_show)

    s = sub.add_parser("answer", help="create answers/<id>.cpp|.md and open the exam editor (waits for submit)")
    s.add_argument("id")
    s.add_argument("--ext", choices=(".cpp", ".md", ".txt"))
    s.add_argument("--minutes", type=float, help="countdown (default: points x 0.65)")
    s.add_argument("--fresh", action="store_true", help="overwrite an existing answer file")
    s.add_argument("--no-open", action="store_true")
    s.add_argument("--no-wait", action="store_true")
    s.set_defaults(func=cmd_answer)

    s = sub.add_parser("sheet", help="open the mock-exam window (arrows, a box per part, tree check) with a countdown")
    s.add_argument("id")
    s.add_argument("--classic", action="store_true", help="the old single-file editor sheet instead")
    s.add_argument("--resume", help="answers/<mock>-<time>.json of a paused exam to continue")
    s.add_argument("--no-open", action="store_true")
    s.add_argument("--no-wait", action="store_true")
    s.set_defaults(func=cmd_sheet)

    s = sub.add_parser("edit", help="open any file in the exam editor")
    s.add_argument("path")
    s.add_argument("--minutes", type=float)
    s.add_argument("--no-wait", action="store_true")
    s.set_defaults(func=cmd_edit)

    s = sub.add_parser("focus", help="focus mode: focus start --minutes N | status | stop 'reason' | end | "
                                     "config [show|categories a,b|add APP|remove APP|allow APP|unallow APP|on|off]")
    s.add_argument("action", choices=("start", "status", "stop", "end", "config"))
    s.add_argument("reason", nargs="?", default="")
    s.add_argument("value", nargs="?")
    s.add_argument("--minutes", type=int, default=75)
    s.set_defaults(func=cmd_focus)

    s = sub.add_parser("browse", help="open the locked-down study browser (optionally a URL or repo file)")
    s.add_argument("target", nargs="?")
    s.set_defaults(func=cmd_browse)

    s = sub.add_parser("view", help="show something in the study browser beside the terminal")
    s.add_argument("target", nargs="?", help="URL from the allowlist, repo file (notes/03-heaps.md, material/slides/Heaps.pdf#page=3)")
    s.add_argument("--find", help="highlight this text on the page")
    s.add_argument("--section", help="for notes: jump to/highlight this heading text")
    s.add_argument("--place", default="left60", help="browser region: left60, left, full, center, ... or none")
    s.add_argument("--terminal", default="right40", help="terminal region (Windows only), or none")
    s.set_defaults(func=cmd_view)

    s = sub.add_parser("viz", help="diagram pages in the study browser: memory | erase | eraseloop | overwriter | "
                                   "move | loops | iterators | costs | bst | page  (see tools/viz.py)")
    s.add_argument("kind", choices=("memory", "erase", "eraseloop", "overwriter", "move", "loops", "iterators",
                                    "costs", "bst", "page"))
    s.add_argument("arg", nargs="?", help="values (7,2,5,9,4), a tree in notation (bst), or a file (page)")
    s.add_argument("rest", nargs="*", help="bst: insert|remove X")
    s.add_argument("--at", type=int, default=1, help="erase: index to erase")
    s.add_argument("--remove", default="odd", help="eraseloop/overwriter: odd|even|neg|pos|<N|>N|=N")
    s.add_argument("--container", choices=("vector", "list"), default="vector", help="eraseloop container")
    s.add_argument("--fixed", action="store_true", help="eraseloop: show the correct loop instead of the bug")
    s.add_argument("--op", default="ctor", choices=("ctor", "ctor-copy", "ctor-no-null", "assign",
                                                    "assign-no-delete", "self"), help="move: which scenario")
    s.add_argument("--members", help="move: 'name_:type,...'; type int|double|... (copy), std::string / "
                                     "std::vector<T> (std::move), T* (one object), T*[] (array)")
    s.add_argument("--cls", default="AlgorithmsCourse", help="move: class name for the code")
    s.add_argument("--kinds", help="loops: comma list of linear,log,nlogn,triangle,square,cubic")
    s.add_argument("--n", type=int, default=8, help="loops: n to draw")
    s.add_argument("--title")
    s.add_argument("--place", default="left60", help="browser region (or none)")
    s.add_argument("--no-open", action="store_true", help="only write the page, print its path")
    s.set_defaults(func=cmd_viz)

    s = sub.add_parser("layout", help="arrange windows: layout study | editor | terminal")
    s.add_argument("preset", choices=("study", "editor", "terminal"))
    s.set_defaults(func=cmd_layout)

    s = sub.add_parser("tts", help="text-to-speech for key takeaways: tts on | off | status")
    s.add_argument("action", choices=("on", "off", "status"))
    s.set_defaults(func=cmd_tts)

    s = sub.add_parser("say", help="speak a short takeaway aloud (only if tts is on)")
    s.add_argument("text")
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=cmd_say)

    s = sub.add_parser("record", help="record a graded attempt: score 0-4")
    s.add_argument("id")
    s.add_argument("score", type=int)
    s.add_argument("--note", help="what went wrong / right")
    s.add_argument("--topic", help="topic for generated (gen:...) questions")
    s.add_argument("--seconds", type=int, help="time taken (default: the last `clock stop` for this id, if recent)")
    s.set_defaults(func=cmd_record)

    s = sub.add_parser("weak", help="track misconceptions: weak add 'text' --topic t | weak resolve N | weak list")
    s.add_argument("action", choices=("add", "resolve", "list"))
    s.add_argument("text", nargs="?", default="")
    s.add_argument("--topic")
    s.set_defaults(func=cmd_weak)

    s = sub.add_parser("style", help="learner profile: style add 'text' --kind works|avoid|pace|pref | style retire N | style list")
    s.add_argument("action", choices=("add", "retire", "list"))
    s.add_argument("text", nargs="?", default="")
    s.add_argument("--kind", choices=("works", "avoid", "pace", "pref", "other"), default="other")
    s.set_defaults(func=cmd_style)

    s = sub.add_parser("studied", help="mark a topic's notes as studied")
    s.add_argument("topic")
    s.set_defaults(func=cmd_topic)

    s = sub.add_parser("session", help="session start | session end --summary '...'")
    s.add_argument("action", choices=("start", "end"))
    s.add_argument("--summary")
    s.add_argument("--minutes", type=float, help="planned session length (with start)")
    s.set_defaults(func=cmd_session)

    s = sub.add_parser("mock", help="mock list | mock show ID [--answers] | mock record ID --scores q1=8,...")
    s.add_argument("action", choices=("list", "show", "record"))
    s.add_argument("id", nargs="?")
    s.add_argument("--answers", action="store_true")
    s.add_argument("--scores")
    s.add_argument("--minutes", type=int)
    s.set_defaults(func=cmd_mock)

    s = sub.add_parser("heap", help="binary heap practice (textbook Ch.6 + heapsort): random | solve ID | grade ID | "
                                    "insert HEAP X,Y | delete HEAP | build VALUES | decrease|increase HEAP P D | "
                                    "remove HEAP P | check HEAP | sort VALUES")
    s.add_argument("action", choices=("random", "solve", "grade", "insert", "delete", "build", "decrease",
                                      "increase", "remove", "check", "sort"))
    s.add_argument("arg", nargs="?", help="gen id, or the heap/values as 1,3,2,... (heap = array from index 1)")
    s.add_argument("rest", nargs="*")
    s.add_argument("--kind", choices=("any", "ins", "del", "build", "max", "sort"), default="any")
    s.add_argument("--seed", type=int)
    s.add_argument("--max", action="store_true", help="max-heap instead of min-heap")
    s.add_argument("--count", type=int, default=1, help="delete: how many deleteMin/deleteMax")
    s.add_argument("--detail", action="store_true", help="build: every slide inside each percolateDown")
    s.add_argument("--array", help="grade: the student's final array")
    s.add_argument("--show", action="store_true", help="also open a step-by-step picture page")
    s.add_argument("--place", default="left60")
    s.set_defaults(func=cmd_heap)

    s = sub.add_parser("hash", help="hash table practice (textbook 5.3-5.5): random | solve ID | grade ID | "
                                    "run KEYS --size M --method ... | prime N")
    s.add_argument("action", choices=("random", "solve", "grade", "run", "prime"))
    s.add_argument("arg", nargs="?", help="gen id, or keys: 4371,1323,-6173 (remove),?99 (find)")
    s.add_argument("--method", choices=("any", "chain", "linear", "quadratic", "double"), default="linear")
    s.add_argument("--size", type=int, default=10)
    s.add_argument("--R", type=int, help="double hashing: hash2(x) = R - (x mod R) (default 7)")
    s.add_argument("--mod", type=int, help="hash(x) = x mod MOD (default: the table size)")
    s.add_argument("--rehash", action="store_true", help="rehash at the textbook load-factor thresholds")
    s.add_argument("--reuse-deleted", action="store_true", help="insert into DELETED cells (Exercise 5.7)")
    s.add_argument("--seed", type=int)
    s.add_argument("--table", help="grade: the student's final table, e.g. '0:9679 1:4371' or '1:[4371] 3:[1323,6173]'")
    s.add_argument("--show", action="store_true")
    s.add_argument("--place", default="left60")
    s.set_defaults(func=cmd_hash)

    s = sub.add_parser("sort", help="sorting practice (textbook Ch.7): random | solve ID | grade ID | partition V | "
                                    "quick V | select V --k K | merge V | insertion V | heap V | inversions V")
    s.add_argument("action", choices=("random", "solve", "grade", "partition", "quick", "select", "merge",
                                      "insertion", "heap", "inversions"))
    s.add_argument("arg", nargs="?", help="gen id or values 8,1,4,9,...")
    s.add_argument("rest", nargs="*")
    s.add_argument("--kind", choices=("any", "partition", "quicksort", "quickselect", "mergesort", "insertion"),
                   default="any")
    s.add_argument("--method", choices=("hoare", "code", "lomuto"), default="hoare",
                   help="hoare = textbook 7.7.2 (default); code = Fig. 7.17 median3 + right-1; lomuto")
    s.add_argument("--pivot", default="median3", help="median3 | first | last | middle | an index (0-based)")
    s.add_argument("--cutoff", type=int, default=3, help="insertion-sort subarrays of size <= cutoff (HW7: 3)")
    s.add_argument("--k", type=int, default=1, help="select: k-th smallest (1-based)")
    s.add_argument("--seed", type=int)
    s.add_argument("--array", help="grade: the student's final array")
    s.add_argument("--steps", help="grade: the student's intermediate arrays, ';'-separated")
    s.add_argument("--answer", help="grade (quickselect): the student's answer")
    s.add_argument("--max", action="store_true", help=argparse.SUPPRESS)
    s.add_argument("--show", action="store_true")
    s.add_argument("--place", default="left60")
    s.set_defaults(func=cmd_sort)

    s = sub.add_parser("setup", help="first-time setup: check | name 'NAME' [--hours H] | textbook PDF | "
                                     "material ZIP... | browser | allowlist | repo-info")
    s.add_argument("action", choices=("check", "name", "textbook", "material", "browser", "allowlist", "repo-info"))
    s.add_argument("arg", nargs="*")
    s.add_argument("--hours", type=float, help="hours per day available to study")
    s.set_defaults(func=cmd_setup)


    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
