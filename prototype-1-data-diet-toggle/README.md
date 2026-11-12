# Prototype 1 — the Data Diet Toggle

> From **"Wicked Problem Prototypes: Personalization Without the Data Districts
> Can't Defend"** (Linda Bernard, Nov 2026).

A settings screen in the QuestSim admin console that lets a district choose how
much the **classroom stream** collects, with the tradeoff stated in plain
language and the QuestSim side fixed at **nothing** regardless of the choice.

## What it is

A clickable, self-contained HTML mock of one screen —
[`index.html`](index.html) — with three collection levels:

- **Full Adaptation** — every signal ACE can use.
- **Standard** — mastery and hint counts, no fine-grained timing.
- **Minimal** — right/wrong only, the smallest defensible footprint.

The screen has two columns:

- The **left column changes** with the toggle: what each teacher sees about a
  student at that level, what ACE can do, and how long the district keeps it.
- The **right column never changes**. At every level it reads: *stored in your
  Google Workspace, readable by your teachers, QuestSim retains nothing.*

Each step down **names what the student loses** in plain language — e.g.
*"Minimal: hint timing is not tracked, so ACE cannot detect guessing; scaffolds
trigger on wrong answers only."* A one-page **data inventory** updates live
alongside the toggle, field by field, showing what is collected, that it lives
in the district's own tenant, and that QuestSim's access is always *Never*.

## Run it

Open `index.html` in any browser — no build, no dependencies. Click the three
levels and watch the left column, the "what the student loses" callout, and the
data inventory update while the right-hand guarantee stays fixed.

## Which insight it comes from

District counsel approves pilots with narrowed settings that blunt adaptation;
the privacy-officer persona is moved by district control and a lower-data mode
with its tradeoffs stated plainly. This makes the narrowing a **first-class
product feature** instead of something negotiated per pilot.

## The test

Put the screen in front of two or three district technology directors or
privacy officers and ask one question: *could you sign a data processing
agreement against this without a call to counsel?* If they still want the call,
the language isn't plain enough. Secondary measure: which level they pick, and
whether the right-hand column changes their reaction to the left.

## Honest caveats

The data fields and the tradeoff language here are **illustrative**. Writing
them so they are *true* is the hard part, and it needs ACE's actual signal
dependencies from the engineering team — which of latency, hint timing and
session behavior each trigger really relies on. The levels and the "what you
lose" lines should be re-grounded against that list before this goes in front
of a district.
