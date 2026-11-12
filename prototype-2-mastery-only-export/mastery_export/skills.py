"""Pythagoras Quest skill sequence and constants for the divergence harness.

Mirrors the sequence used in Prototype 3 (Synthetic Student Tuning), which in
the integrated story supplies the logged sessions this prototype replays.
Each skill carries Bayesian Knowledge Tracing difficulty parameters
(Corbett & Anderson, 1995): guess P(G), slip P(S), learn P(T).
"""

SKILLS = [
    ("square_numbers", dict(guess=0.20, slip=0.08, learn=0.22)),
    ("square_roots",   dict(guess=0.18, slip=0.10, learn=0.19)),
    ("identify_hyp",   dict(guess=0.25, slip=0.10, learn=0.20)),
    ("theorem_setup",  dict(guess=0.15, slip=0.12, learn=0.16)),
    ("solve_hyp",      dict(guess=0.12, slip=0.13, learn=0.14)),
    ("solve_leg",      dict(guess=0.10, slip=0.15, learn=0.12)),
    ("word_problems",  dict(guess=0.10, slip=0.17, learn=0.10)),
]
SKILL_NAMES = [n for n, _ in SKILLS]

MAX_OPP = 12       # most practice items per skill
FT_CHECK = 3       # the fast-track decision point
EWMA_ALPHA = 0.4   # smoothing of the rolling struggle signal

# ACE trigger thresholds (shared by both models; only the fine signals differ).
FT_THRESHOLD = 0.90    # mastery needed to fast-track at FT_CHECK
SCAF_THRESHOLD = 0.60  # struggle (EWMA of errors) needed to scaffold
HINT_BAND = 0.15       # server lets an early hint pull a borderline struggler in

# Pre-registered decision rule for the test (set BEFORE running):
# the on-device model must diverge from the server model on fewer than this
# share of scaffold and fast-track triggers.
DIVERGENCE_THRESHOLD = 0.05
