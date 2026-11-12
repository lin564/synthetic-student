"""Prototype 2 - Mastery-Only Export.

A technical proof that ACE can adapt on the device and export only a per-skill
mastery vector to the district's Drive folder, so the raw clickstream never
leaves the browser. A side-by-side harness replays the same logged sessions
through a full server-side model and a mastery-only on-device model and
measures how often their adaptation decisions diverge.

From "Wicked Problem Prototypes: Personalization Without the Data Districts
Can't Defend" (Linda Bernard, Nov 2026).
"""
from .skills import SKILLS, SKILL_NAMES, DIVERGENCE_THRESHOLD
from .sessions import sample_population, log_sessions, session_footprint
from .models import mastery_trail, replay
from .harness import run_harness, run_multi

__all__ = [
    "SKILLS", "SKILL_NAMES", "DIVERGENCE_THRESHOLD",
    "sample_population", "log_sessions", "session_footprint",
    "mastery_trail", "replay", "run_harness", "run_multi",
]
