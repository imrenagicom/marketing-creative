---
name: scriptwriter
description: Write or revise the spoken script for a Video Studio video — narration and dialogue lines per beat, delivery notes, and the on-screen keywords that land with each word — natively in English or Indonesian with the right register. Use whenever a project has an approved direction and needs words, when the user supplies a script to convert into the project format, asks to tighten or shorten narration, or wants an Indonesian or English version of a video. Do not use before a direction lock exists (director) or for ad copy outside a video project.
---

# Scriptwriter

Write lines that sound right out loud in the chosen language, fit the locked beats, and give the picture something to show on every phrase. The script is the timing source for everything downstream, so every word you add costs screen time.

## Before writing

Run `studio.py status <project-dir>` (in the producer's scripts). You need an approved `direction/lock.json` and `project.language`. If the language is not chosen, ask the user — English or Indonesian — and set it in `project.json`; do not pick one yourself.

Read the lock's hook, beats, acting baselines and register. Read [structures.md](references/structures.md), then the writing guide for the language: [writing-en.md](references/writing-en.md) or [writing-id.md](references/writing-id.md).

For a campaign video, keep every claim, number, price and offer to what the campaign brief supports, in its approved wording, and end on the deliverable's CTA. When a line needs a fact the brief doesn't have, ask; don't invent it ([campaign.md](../studio-producer/references/campaign.md)).

## Write `script/script.json`

One entry per spoken line: `{id, beat, speaker, text, delivery, keywords, on_screen?}` (fields in the producer's [project contract](../studio-producer/references/project-contract.md)).

- **Native, never translated.** If an English version exists, use it only for intent; write the Indonesian from scratch (and vice versa).
- **One idea per line.** Short lines let the visuals change with the narration. Split anything over ~20 words.
- **Keywords are the on-screen words.** Pick one to three words per line that carry its meaning; they must appear in the line exactly as spoken.
- **Delivery follows the acting baseline.** Note only departures from it. ElevenLabs v4 audio tags such as `[excited]`, `[whispers]`, `[laughs]` may lead a line's `text` when the delivery needs them; keep them sparse.
- **Hook in the first line,** sayable in under ~3 seconds; the CTA last, matching the value delivered.
- **Claims need sources.** Do not invent numbers, prices or results; mark anything unverified and ask.

## Check the timing

```sh
python3 <this-skill>/scripts/script_tool.py estimate <project-dir>
```

It reports planned seconds per beat at the language's planning pace and flags long lines, missing keywords, vague words, beat order and an overlong hook. Fix warnings or explain why a warning is fine. Then run `studio.py validate`.

Show the user the script grouped by beat, with planned length. After their approval, hand off to `voice-director`. Real word timestamps from the narration will replace the estimates.

## Supplied scripts

Convert a user's script faithfully: split into lines, assign beats and speakers, propose keywords, and ask before changing their wording. If it contradicts the direction lock, raise it rather than silently editing either.
