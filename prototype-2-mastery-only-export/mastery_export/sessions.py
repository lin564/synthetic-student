"""Logged sessions: fixed raw event trails for the replay harness.

In the current product, this raw trail (every click, latency, hint) is what
leaves the student's device and goes to a server-side learner model. This
prototype asks whether that is necessary. The sessions here are synthetic —
in the integrated story they come from Prototype 3's synthetic learners, so
no real clickstream is needed to run the comparison.

Each logged event records what a real event trail would:
    correct    : was the answer right
    latency    : seconds to answer (fast correct on an unknown skill = a guess)
    hint_used  : was a hint opened
    hint_time  : when in the attempt it was opened (0 = immediately, 1 = at the end)

`latency` and `hint_time` are the fine-grained behavioral signals districts
object to. The point of the harness is to measure how much ACE's decisions
actually depend on them.
"""
from __future__ import annotations
import json
import numpy as np

from .skills import SKILLS, MAX_OPP, FT_CHECK


def sample_population(n: int, seed: int) -> dict:
    r = np.random.default_rng(seed)
    return {
        "prior": np.clip(r.normal(0.20, 0.10, n), 0.02, 0.70),
        "learn_mult": np.clip(r.normal(1.0, 0.30, n), 0.25, 2.20),
        "slip_mult": np.clip(r.normal(1.0, 0.30, n), 0.40, 2.50),
        "hint": np.clip(r.normal(0.30, 0.16, n), 0.0, 0.90),
    }


def log_sessions(pop: dict, seed: int) -> list:
    """Generate one fixed logged session per (student, skill)."""
    r = np.random.default_rng(seed)
    n = len(pop["prior"])
    logs = []
    for i in range(n):
        for s, (_name, p) in enumerate(SKILLS):
            guess = min(0.45, p["guess"])
            slip = min(0.45, p["slip"] * pop["slip_mult"][i])
            learn = min(0.60, p["learn"] * pop["learn_mult"][i])
            known = r.random() < pop["prior"][i]
            events = []
            for opp in range(1, MAX_OPP + 1):
                correct = (r.random() > slip) if known else (r.random() < guess)
                # latency, in seconds, from the true state
                if known and correct:
                    lat = r.normal(2.6, 0.7)
                elif known and not correct:
                    lat = r.normal(3.0, 0.9)
                elif (not known) and correct:
                    lat = r.normal(1.3, 0.4)   # a fast, lucky guess
                else:
                    lat = r.normal(4.6, 1.4)   # struggling, slow
                lat = round(float(max(0.4, lat)), 2)
                # hint-seeking, earlier when struggling
                p_hint = min(0.90, pop["hint"][i] * (1.6 if not known else 0.6))
                hint_used = bool(r.random() < p_hint)
                if hint_used:
                    ht = r.normal(0.22, 0.10) if not known else r.normal(0.60, 0.15)
                    ht = round(float(min(0.98, max(0.02, ht))), 2)
                else:
                    ht = None
                events.append({"correct": bool(correct), "latency": lat,
                               "hint_used": hint_used, "hint_time": ht})
                if not known and r.random() < learn:
                    known = True
                if correct and known and opp >= FT_CHECK and r.random() < 0.5:
                    break
            logs.append({"student": i, "skill": s, "events": events})
    return logs


def session_footprint(session: dict) -> dict:
    """Bytes that would leave the device under each design, for one session.

    current  : the whole raw event trail is sent to the server.
    proposed : only the per-skill mastery vector leaves (a single float here).
    """
    raw = json.dumps(session["events"], separators=(",", ":")).encode()
    mastery_value = json.dumps({"skill": session["skill"], "mastery": 0.0},
                               separators=(",", ":")).encode()
    return {"raw_bytes": len(raw), "mastery_bytes": len(mastery_value),
            "events": len(session["events"])}
