"""The Pythagoras Quest skill sequence and the global simulation constants.

Prototype 3 (Synthetic Student Tuning) from "Wicked Problem Prototypes:
Personalization Without the Data Districts Can't Defend" (Linda Bernard,
Nov 2026). A synthetic middle-school cohort is run through this skill
sequence so ACE's scaffold and fast-track triggers can be calibrated
without any real student data.

Each skill carries Bayesian Knowledge Tracing (BKT) difficulty parameters
(Corbett & Anderson, 1995):

    guess (P(G)) : probability of a correct answer while the skill is NOT known
    slip  (P(S)) : probability of a wrong answer while the skill IS known
    learn (P(T)) : probability of acquiring the skill on each opportunity

The sequence is ordered easy -> hard: later skills have a lower learn rate
and a higher slip, so a realistic fraction of the cohort stalls on the
back half of the unit (word problems) the way real classes do.
"""

# --- Pythagoras Quest: a Pythagorean-theorem unit for middle schoolers ---
SKILLS = [
    ("square_numbers", dict(guess=0.20, slip=0.08, learn=0.22)),  # 7^2 = 49
    ("square_roots",   dict(guess=0.18, slip=0.10, learn=0.19)),  # sqrt(49) = 7
    ("identify_hyp",   dict(guess=0.25, slip=0.10, learn=0.20)),  # which side is c?
    ("theorem_setup",  dict(guess=0.15, slip=0.12, learn=0.16)),  # a^2 + b^2 = c^2
    ("solve_hyp",      dict(guess=0.12, slip=0.13, learn=0.14)),  # solve for c
    ("solve_leg",      dict(guess=0.10, slip=0.15, learn=0.12)),  # solve for a leg
    ("word_problems",  dict(guess=0.10, slip=0.17, learn=0.10)),  # distance / ladders
]

SKILL_NAMES = [name for name, _ in SKILLS]

# --- Simulation constants (shared by the engine and the harness) ---
MAX_OPP = 14      # most practice items ACE will serve for one skill
MASTERY = 0.95    # BKT mastery threshold; the Cognitive Tutor convention
FT_CHECK = 3      # ACE makes the fast-track decision after this many items
SCAF_WARMUP = 4   # earliest item at which scaffold may fire
EWMA_ALPHA = 0.4  # smoothing for the rolling "struggle" signal

# --- ACE trigger design intent (the rates calibration aims to hit) ---
# These are pedagogical targets, chosen before any tuning: fast-track should
# fire on ~15% of skill encounters, scaffold on ~35%. Calibration finds the
# thresholds that land closest to them.
FT_TARGET = 0.15
SCAF_TARGET = 0.35

# Threshold grids the calibration sweeps.
FT_GRID = [round(0.70 + 0.02 * i, 3) for i in range(15)]    # 0.70 .. 0.98
SCAF_GRID = [round(0.30 + 0.05 * i, 3) for i in range(11)]  # 0.30 .. 0.80
