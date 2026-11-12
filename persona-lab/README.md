# Synthetic Persona Lab

A self-contained, in-browser site for **testing educational apps and games against
a population of synthetic student personas**. It's a browser port of the
Synthetic Student Tuning model (Prototype 3), turned into a usable tool.

**Live (private) page:** https://claude.ai/artifact/VAogVdZo3JPmsTgTFgjBvv

Everything runs client-side — no server, no build, no data leaves the browser.
Open `index.html` directly, or use the live link above.

## What's in it

- **Population** — generate a cohort of synthetic learners, each with six
  grounded parameters (prior knowledge, learning rate, slip, guessing,
  hint-seeking, forgetting). Shape it with sliders and presets, see live
  parameter distributions, save named populations (e.g. "ELL 6th grade") to
  reuse, and copy the cohort out as JSON or CSV. Deterministic from the seed.
- **Activity runner** — describe your app or game as a sequence of skills with
  difficulty (no code) and run the whole population through it. See mean
  mastery, retention, bottom-quartile, where students stall, and how often the
  adaptive fast-track / scaffold triggers fire.
- **API sandbox** — the population is live on the page as
  `window.SyntheticPersonas`. Paste your app's real scoring/difficulty logic
  into the editor and run the whole cohort against it.
- **Embed a game** — load a web game and drive it with persona *players* over a
  tiny `postMessage` protocol. A working demo game ("Number Climb") is included;
  a real game drops in a ~15-line adapter.

## The JavaScript API

```js
const { personas } = SyntheticPersonas.generate({ n: 200, seed: 1 });
const st = SyntheticPersonas.newLearnerState(personas[0], 123);
const ev = SyntheticPersonas.respond(personas[0], { guess: 0.15, slip: 0.1, learn: 0.18 }, st);
// ev -> { correct, latencyMs, usedHint, mastery, struggle }
const agg = SyntheticPersonas.runActivity(personas, { skills, maxOpp: 14, ftThr: 0.9, scafThr: 0.6 });
```

## Embed protocol

The lab is the authority on how a persona responds; the game asks it per item.

| direction | message | payload |
|---|---|---|
| game → lab | `persona-test:ready` | — |
| lab → game | `persona-test:init` | `{ players: [{id}], config }` |
| game → lab | `persona-test:item` | `{ playerId, item: {guess, slip, learn} }` |
| lab → game | `persona-test:response` | `{ playerId, correct, latencyMs, usedHint, mastery }` |
| game → lab | `persona-test:result` | `{ playerId, mastery, level }` |
| game → lab | `persona-test:done` | `{ count }` |

## Notes

- The model is illustrative learning-science (BKT + power law of practice +
  help-seeking + memory decay), not any specific product's engine.
- Per-viewer conveniences (theme, saved populations) use `localStorage`; they
  live only in that browser.
- No real student data is used anywhere.
