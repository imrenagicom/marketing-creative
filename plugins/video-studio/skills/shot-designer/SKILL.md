---
name: shot-designer
description: Turn a Video Studio script and narration into a shot list — what the viewer sees on every line, why it appears, how it transitions — then lint it and time every shot to the narration's word timestamps. Use whenever a project has a script (and ideally a narration take) and needs a storyboard, shot list or visual breakdown, when shots feel static or vague, or after a new narration take makes timing stale. Explainer shots are motion-graphics layouts; cinematic shots are camera shots with continuity references and take grouping.
---

# Shot Designer

Decide what the viewer sees on every spoken line, make every picture earn its moment, and time the cuts to the words. Vague shots ("dynamic visuals") cannot be built or generated well; the linter exists to catch them before anyone spends time or credits.

## Inputs

An approved direction lock (visual plan, contrast rule), the script with keywords, and — for timing — `voice/words.json`. Read [shot-craft.md](references/shot-craft.md) for the visual vocabulary and rhythm rules and [visual-modes.md](references/visual-modes.md) for each graphic mode's fields.

## Write `shots/shots.json`

One entry per shot, in screen order: `{id, kind, beat, lines[], motivation, transition, visual}` (contract in the producer's [project contract](../studio-producer/references/project-contract.md)).

- **Every line has a picture.** Each script line belongs to exactly one shot; a shot may cover several lines when its visual builds across them (a checklist revealing one item per step).
- **Motivation is required.** Say what the narration needs shown at that moment ("make the pain visible as it is named"). If you cannot, the shot is decoration — merge or cut it.
- **Change something every 2–5 seconds.** A new keyword, list item, card or layout counts. Vary modes; four of the same layout in a row reads as a slideshow.
- **Transitions have jobs.** `cut` by default; `wipe` marks a new section (between steps or beats); `fade` for the ending; `push` for a sequence moving forward.
- **Explainer shots are `graphic`.** `camera` shots belong to footage recipes (see below).
- The final shot may be a silent `hold` (seconds) for the end card.

## Footage shots (cinematic recipe)

Camera shots carry `framing`, `movement` (a direction and a reason), `action` (what hands, eyes and body do), `light_source` (a visible source from the bible's environment), `sound`, `refs` (bible ids it shows), `screen_direction`, and a `duration` when there is no narration. Group consecutive shots that must match across the cut into one `take` (2–4 shots, within `max_take_seconds` for the chosen model); give a shot its own take when it is likely to need retakes. The linter warns on missing references or environments and on screen-direction flips within a beat, and refuses takes longer than the model limit.

## Lint, time, re-lint

```sh
python3 <this-skill>/scripts/shots.py lint <project-dir>
python3 <this-skill>/scripts/shots.py time <project-dir>
python3 <this-skill>/scripts/shots.py lint <project-dir>
```

`lint` catches lines without a picture, out-of-order lines, missing motivation or mode fields, vague wording, camera moves without direction, missing image assets, repeated layouts and — once timed — shots too short to read or static too long. Fix errors; fix warnings or say why they are fine.

`time` cuts each shot slightly before the first word of its first line, holds the last shot past the final word (default 0.8 s, or the shot's `hold`), and records which take it was timed against. Re-run it whenever a new take is selected. Without narration (cinematic), it lays shots end to end from their durations.

Show the user the shot list as a table (time, line, what's on screen, why) before composition. Then hand off to `motion-designer`.
