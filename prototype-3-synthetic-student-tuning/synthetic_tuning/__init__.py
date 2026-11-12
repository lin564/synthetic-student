"""Prototype 3 - Synthetic Student Tuning.

A simulation harness that develops and calibrates QuestSim's adaptive engine
(ACE) on simulated middle schoolers, so real student data is needed only for
low-volume aggregate validation and never for model development.

From "Wicked Problem Prototypes: Personalization Without the Data Districts
Can't Defend" (Linda Bernard, Nov 2026).
"""
from .skills import SKILLS, SKILL_NAMES, FT_TARGET, SCAF_TARGET, FT_GRID, SCAF_GRID
from .learners import sample_population, PARAMS
from .ace import run_student
from .harness import run_cohort, calibrate, pick_threshold
from . import validation

__all__ = [
    "SKILLS", "SKILL_NAMES", "FT_TARGET", "SCAF_TARGET", "FT_GRID", "SCAF_GRID",
    "sample_population", "PARAMS", "run_student",
    "run_cohort", "calibrate", "pick_threshold", "validation",
]
