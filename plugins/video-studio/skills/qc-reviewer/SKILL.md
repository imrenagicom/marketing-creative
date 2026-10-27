---
name: qc-reviewer
description: Run quality control for Video Studio — dailies review of each generated take against the continuity bible (face, outfit, location, movement) before clips are selected, and final checks on render versions (dimensions, frame rate, duration, audio, loudness, black frames, silence, captions) with the human watch-and-listen checks still required. Use whenever a take comes back from generation, a shot looks off, a video has been rendered or finished, or the user asks whether it is ready to publish. Not for creative critique of direction or script (director, scriptwriter).
---

# QC Reviewer

Catch technical problems before the user publishes, and be explicit about what automated checks cannot see. A passing report means the files match the plan technically; it does not mean the video is good.

## Run

```sh
python3 <this-skill>/scripts/qc.py final <project-dir> [--version N]
```

It checks the delivery copy of each canvas (or the raw render if not finished yet, with a warning) and writes `qc/report.json`:

| Check | Fails when |
| --- | --- |
| dimensions, frame rate | they differ from `project.json` |
| duration | more than 0.15 s (+1 frame) from the shot plan |
| audio stream | missing |
| loudness, true peak | delivery is more than 1 LU off its target or peaks above it |
| black frames | any black span over 0.5 s |
| mid-video silence | silence over 1.5 s away from the start and end (warning) |
| captions | cues do not cover the narration or overlap |

It also writes one frame per shot midpoint to `qc/frames/v<N>/<canvas>/` for visual review.

## Review

1. Fix failures at the stage that owns them (rendering → editor, timing → shot-designer, audio level → editor finish, missing narration → voice-director), then re-render a new version and run QC again.
2. Look at the review frames for every canvas: text overflow, safe areas, contrast, keyword timing at boundaries.
3. Present the report's `manual_checks_remaining` to the user. Watching every canvas with sound, checking names and pronunciation, and approving claims are human checks; never mark them done unless a person actually did them.

## Report

Summarise per canvas: passed, failed, warnings, and what still needs a human. Name the files checked (delivery vs raw render). Do not describe the video as "ready" or "high quality" on the strength of automated checks.

## Dailies (generated takes)

Every generated take is reviewed before its clips can be selected. Read [dailies.md](references/dailies.md).

```sh
python3 <this-skill>/scripts/qc.py dailies <project-dir> --take T1-16x9
python3 <this-skill>/scripts/qc.py verdict <project-dir> --take T1-16x9 --shot S02 --pillar outfit --fail --note "bag on the wrong shoulder"
python3 <this-skill>/scripts/qc.py verdict <project-dir> --take T1-16x9 --shot S01 --pillar all --pass
python3 <this-skill>/scripts/qc.py retakes <project-dir>
```

`dailies` extracts three frames per shot (10%, 50%, 90%), a contact sheet, and checks each clip's aspect ratio and length against the plan; pillar verdicts start as `unreviewed`. Look at the sheet next to the bible's reference images and record a verdict for each pillar — face, outfit, location (including light direction), movement (including screen direction across the cut). A failure needs a note saying what drifted. `retakes` lists every shot with a failed pillar or check for `ai-video-generator retake`.

Record verdicts only for what was actually looked at; if the user reviewed, say so in the note.
