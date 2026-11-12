# Synthetic Student Tuning — findings at a glance

_2026-11-12 · no real student data used_

---
## 1. The claim
Build and tune ACE on simulated students; real students only ever
confirm, in aggregate, that it works.

---
## 2. It holds
- Synthetic-tuned ACE is **within range** of real-tuned ACE on every
  aggregate outcome (PASS).
- The aggregate-only feedback loop recovers true cohort difficulty
  to **MAE 0.017** from one number per cohort.
- A fix found on synthetic data transfers to the real cohort
  (+0.019 bottom-quartile mastery, no record leaves).

---
## 3. It generalises
- Within-range holds for **5/5** cohort shapes tried
  (uniform, forgetting tail, bimodal, gaming, slow).

---
## 4. The honest limit
- Matching the aggregate ≠ being right about individuals.
- The **retention** blind spot is invisible to the aggregate; across
  cohort shapes it ranges 0.014–0.108, largest for the
  mis-specified **high_gaming** cohort.
- So the two streams **validate each other** — neither replaces the other.

---
## 5. Ready for real data
- Drop in a district's one aggregate number (CSV/JSON); the loop
  re-grounds. Minimum cohort enforced; per-student fields refused.
