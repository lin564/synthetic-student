# Wicked Problem Prototypes — Personalization Without the Data Districts Can't Defend

Three prototypes for a single wicked problem, from the write-up of the same name
(Linda Bernard, Nov 2026).

## The problem

QuestSim's adaptive engine (**ACE**) gets better at personalizing instruction the
more fine-grained the data it sees — response latency, error patterns, hint use,
session behavior over time. COPPA and FERPA, and the districts that enforce them,
push the other way: collect and retain less. Solving for personalization makes
the privacy problem harder; solving for privacy degrades personalization.

> **How might we personalize learning without collecting the data districts
> can't defend?**

## The reframe: two streams, never crossed

"Personalization versus privacy" assumed one dataset serving two masters. Once
the two purposes are separated, most of the tension goes away:

- a **classroom stream** — what *this child* did today — written into the
  district's own Google Workspace, owned by the district, that QuestSim never
  stores;
- an **engineering stream** — how children *in general* behave — synthetic or
  de-identified aggregates only, never individual records.

The three prototypes probe the three places a district's objection can land.

## The three prototypes

| | Prototype | Reframes | What it is | Status |
|---|---|---|---|---|
| 1 | **[Data Diet Toggle](prototype-1-data-diet-toggle/)** | the policy surface | A clickable admin-console mock: a district picks how much the classroom stream collects (Full / Standard / Minimal), tradeoffs in plain language, QuestSim's share fixed at nothing. | Clickable HTML mock |
| 2 | **[Mastery-Only Export](prototype-2-mastery-only-export/)** | the architecture | A replay harness proving ACE can adapt on-device and export only a mastery vector; measures how much adaptation depends on the raw trail that would otherwise leave the device. | Runnable Python harness |
| 3 | **[Synthetic Student Tuning](prototype-3-synthetic-student-tuning/)** | where the data comes from | A simulation harness that develops and calibrates ACE on ~200 synthetic middle schoolers, so real student data is needed only for low-volume aggregate validation. | Runnable Python harness |

## How they relate

- **Prototype 1** makes the narrowing a first-class product feature a privacy
  officer can sign against without calling counsel.
- **Prototype 2** shows that ~99% of ACE's adaptation decisions survive moving
  on-device with only a mastery vector leaving — and names the two signals
  (response latency, hint timing) that carry the residual.
- **Prototype 3** answers *if QuestSim never gets student data, how does the
  product get better?* — the brain is built in simulation; real students only
  ever confirm, in aggregate, that it works.

They interlock: **Prototype 2's divergence** falls on exactly the two signals
**Prototype 1's** Standard and Minimal levels drop, and **Prototype 3** can
supply the synthetic logged sessions **Prototype 2** replays.

## Running the code

Prototypes 2 and 3 are self-contained Python (numpy + matplotlib); each has its
own `requirements.txt` and a `python run.py` that regenerates its figures and
report. Prototype 1 is a single `index.html` — just open it.

```bash
# Prototype 3
cd prototype-3-synthetic-student-tuning && pip install -r requirements.txt && python run.py

# Prototype 2
cd prototype-2-mastery-only-export && pip install -r requirements.txt && python run.py

# Prototype 1 — open prototype-1-data-diet-toggle/index.html in a browser
```

## Honest caveats (carried from the write-up)

- The data fields, tradeoff language, and decision rules are **illustrative**.
  Grounding them needs ACE's actual signal dependencies from the engineering
  team.
- The "real" cohorts and logged sessions are **synthetic stand-ins**; a real
  pilot would replace them.
- A synthetic population tuned to match real aggregates can still be wrong about
  individuals in ways that only show up in real classrooms — which is why the
  two streams validate each other rather than one replacing the other.

## Provenance

Parameters are grounded in Bayesian Knowledge Tracing (Corbett & Anderson, 1995),
the power law of practice (Newell & Rosenbloom, 1981), help-seeking research
(Aleven et al., 2006), and memory-decay work (Ebbinghaus; Pavlik & Anderson,
2005). No real student data is used anywhere in this repository.
