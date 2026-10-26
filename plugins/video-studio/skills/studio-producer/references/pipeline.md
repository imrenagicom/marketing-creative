# Pipeline and handoffs

## Stage order

Audio comes before pictures: the narration's word timestamps decide how long every shot lasts and when each on-screen keyword appears. Building visuals first and stretching audio to fit produces rushed or padded delivery.

| # | Stage | Owner | Gate before the next stage |
| --- | --- | --- | --- |
| 1 | Direction | `director` | `direction/lock.json` exists with `approved.by = "user"` |
| 2 | Script | `scriptwriter` | `script/script.json` validates; language matches the project |
| 3 | Voice | `voice-director` | `voice/words.json` validates against the script |
| 4 | Shots | `shot-designer` | lint has no errors; every shot is timed |
| 5 | Compose | `motion-designer` | each canvas builds; HyperFrames lint passes when installed |
| 6 | Edit | `editor` | renders, captions and deliveries written per canvas |
| 7 | QC | `qc-reviewer` | `qc/report.json` with no failing checks, or failures reported to the user |

`studio.py status` reports the first missing stage as `next`.

## Entry points

Respect what the user already has; do not restart intake.

- **Only an idea** → start at direction.
- **A brief** → direction, using the brief instead of an interview.
- **A chosen direction in prose** → record it as the lock (with the user's approval), then script.
- **A finished script** → convert it to `script/script.json` faithfully, confirm beats and speakers with the user, then voice. Ask before rewriting their words.
- **Recorded narration plus its transcript** → voice-director aligns it (forced alignment) instead of generating speech.
- **An existing project** → `status`, then continue.

## Changes after a stage is locked

Changes travel downstream, never sideways:

- A direction change bumps `lock.version`; script, voice, shots and compositions are stale until re-checked.
- A script change invalidates the narration take and word timings for the changed lines.
- A new narration take invalidates shot timing; re-run `shots.py time`.
- Shot changes only affect compositions and renders.

Tell the user which downstream files a change makes stale before regenerating paid material.
