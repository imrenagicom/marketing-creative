---
name: reference-analyst
description: Break down a reference video — hook, structure, shot list with timings, camera setups and moves, pacing, graphics, audio and transferable directing techniques — into an analysis and report that separates techniques to adopt from the reference's style, which must not be copied. Use whenever the user shares a video they like, a competitor ad, a "make it like this" example, or a folder of reference clips or prompts before directing a Video Studio project. Not for transcribing meetings or editing the reference itself.
---

# Reference Analyst

Learn from references without cloning them. Measure what can be measured (cuts, shot lengths, loudness), look at what must be seen (framing, moves, graphics), and write down *techniques* the project can reuse — hook mechanisms, camera grammar, pacing, continuity habits — separately from the reference's look, palette, typography and persona.

## Measure

```sh
python3 <this-skill>/scripts/analyze.py <video> --out <project-dir>/references/<name>
```

It writes `analysis.json` (metadata, shot list from scene cuts, pacing, loudness and silences), one frame per shot under `frames/` and a `contact-sheet.png`. Cut detection misses dissolves and whip-pans and can split on flashes; adjust `--threshold` (0.2 more sensitive, 0.4 stricter) and correct the shot list by eye.

Transcription is optional and paid: add `--transcribe-estimate <credits> --project <project-dir> [--language en|id]` to run ElevenLabs Scribe v2 under the project's approved ElevenLabs cap. Supplied transcripts or prompts are free; use them first.

## Look and write

View the contact sheet and frames (and the video itself when you can). Then write `report.md` next to the analysis using [report-template.md](references/report-template.md):

- **Hook**: what happens in the first 2 seconds, which pattern (see the director's hook library), how it is paid off.
- **Structure and pacing**: beats with timestamps, shot count, average shot length, where the cut rhythm changes.
- **Camera**: setups (framing, angle), moves and their motivation, screen direction, how continuity is kept across angles.
- **Graphics and text**: what appears with which words, depth layering, callouts, UI treatment.
- **Audio**: voice style, music or none, sound effects, loudness.
- **Techniques to adopt** and **style not to copy**, as two explicit lists.

If the reference comes with prompts or written tips, extract their structure (reference roles, locks, timed beats, negatives) as techniques too.

## Handoff

Give the director the techniques list, not the look. Never put the reference's video, frames or creator identity into the plugin or a commit; analyses stay in the project directory.
