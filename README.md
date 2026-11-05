# CSCI 335 Exam 2 — Claude Code study coach

A [Claude Code](https://claude.com/claude-code)–powered exam coach for **CSCI 33500 Software Analysis & Design 3
(Hunter College, Prof. Tojeira)**, **Exam 2: Thursday Nov 19, 2026** (seated by 2:30 PM, 70 minutes, closed book).

Claude reads `CLAUDE.md` and becomes your tutor. It teaches from the study guides, quizzes you, grades you the way the
professor does, generates unlimited auto-graded traces, and tracks your progress in `progress/progress.json`.

Covers **hashing (Ch 5.1–5.6), binary heaps (Ch 6.1–6.4) and sorting (Ch 7)**: quicksort/quickselect with the
textbook's Hoare partition, heapsort, introsort, mergesort, insertion sort and the lower bounds. It also covers the
**cumulative complexity-analysis, design and STL coding questions** that make up about half of the exam.

> The professor warned that algorithm variants from AI tools are graded wrong. Every trace here comes from engines that
> implement the **textbook** algorithms exactly. They were checked against the HW5 official answers, the textbook
> figures/exercises (6.2, Fig 7.6–7.10, 7.7.2) and the Hoare Partitioning Example handout.

## Get started (5 minutes)

```bash
git clone https://github.com/ricky074game/csci335-exam2.git
cd csci335-exam2
claude
/setup
```

`/setup` asks your name, how much time you have, what you find hard and how you learn best, then:
- imports **your** Brightspace downloads (point it at the zips; it keeps only the Exam 2 files and converts them to text),
- optionally extracts the in-scope chapters from your copy of the textbook PDF (stays on your machine),
- installs the locked-down **study browser** (pictures of every trace, the notes, the course docs),
- sets up **focus mode** if you want it (closes browsers, chat, social, games and streaming apps during a session; you
  pick the categories and which apps to keep),
- optionally creates **your own private GitHub repo** for your progress, so it syncs between computers. This
  template becomes `upstream`, so you can still pull new questions later.

Requirements: Python 3.8+ (no packages needed for the core), Claude Code. Optional: `gh` (GitHub CLI), a C++ compiler
(lets Claude compile-check your code answers), Tk on Linux (`sudo apt install python3-tk`) for the exam editor.

## Daily use

```
/start 60        sync, dashboard, plan a 60-minute session
...
/save            log the session and push your progress
```

| Command | What it does |
|---|---|
| `/setup [name]` | First-time setup (above) |
| `/start [min]` | Sync, dashboard, plan for the session |
| `/learn <topic>` | Interactive lesson with check questions |
| `/quiz [topic] [type] [n]` | Spaced-repetition practice (default 5 mixed) |
| `/trace [hash\|heap\|sort\|mix] [n]` | Unlimited auto-graded traces (hash tables, heaps, partitions, quickselect, heapsort, mergesort) |
| `/design [n]` | "Design a solution and analyze it" drill, the biggest part of Exam 2 |
| `/drill` | Your weak spots + questions you got wrong |
| `/mock [mock-1]` | Full timed 70-minute, 100-point mock exam, graded |
| `/cram` | Night-before / exam-morning rapid review |
| `/status` | Dashboard + what to do next |
| `/save` | End session, commit + push progress |

Topics: `analysis` `hashing` `quicksort` `heaps` `coding` `heapsort` `sortbasics`.

You can also just talk to it: "explain quadratic probing again", "give me a harder buildHeap", "I have 20 minutes".

**Writing code / long answers:** for coding and design questions Claude opens the built-in **exam editor**. The
question is on top, your answer goes below, and there's a countdown. It has no autocomplete, and Exam mode turns off
even the helpers. **Submit** (Ctrl+Enter) sends it to Claude for grading. Mocks open in a window with one question
per page. You can also write on paper and drop a photo into `answers/`.

## The trace engines (usable without Claude)

```bash
python tools/study.py hash run 4371,1323,6173,4199,4344,9679,1989 --size 10 --method double     # HW5 5.1d
python tools/study.py heap delete "3,6,5,7,12,9,13,11,8"            # HW6 Q2, with index 0 shown
python tools/study.py heap build 10,12,1,14,6,5,8,15,3,9,7,4,11,13,2 # Exercise 6.2b
python tools/study.py sort partition 11,2,3,9,10,8,4,12,1,13,5,14 --pivot 3   # the Hoare handout
python tools/study.py sort quick 3,1,4,1,5,9,2,6,5,3,5 --cutoff 3   # HW7 7.19
python tools/study.py sort select 8,1,4,9,6,3,5,2,7,0 --k 7
python tools/study.py heap sort 31,41,59,26,53,58,97                # Fig 7.6-7.9
python tools/study.py sort random        # then: sort solve <id>   /  hash random, heap random
```
Add `--show` to any of them for a step-by-step picture page.

## Layout

```
CLAUDE.md                tutor instructions (the "brain")
.claude/commands/        slash commands (/setup, /start, /learn, /quiz, /trace, /design, /drill, /mock, /cram, /status, /save)
tools/study.py           tracker + CLI;  hashing.py, heap.py, sorting.py = textbook-exact trace engines
tools/studysetup.py      what /setup runs (material import, textbook split, browser install, allowlist)
tools/editor.py, mockui.py   exam editor + mock window      tools/focus.py   focus mode
notes/                   study guides (00-cheatsheet.md = exam-morning sheet)
bank/                    question bank: prompts, model answers, rubrics
mocks/                   full mock exams
progress/progress.json   your progress (created on first use; synced through YOUR repo)
material/                the professor's files, imported by /setup (not in this repo)
```

The course files and the textbook are not included in this repo for copyright reasons. Everyone imports their own.
This is an unofficial study aid and is not affiliated with Hunter College or the professor.
