---
name: qc-reviewer
description: Run final quality control on a Video Studio render version — dimensions, frame rate, duration against the shot plan, audio presence, loudness and true peak, black frames, mid-video silence, caption coverage — extract a review frame per shot, and list the human watch-and-listen checks still required. Use whenever a video has been rendered or finished and the user asks whether it is ready, wants a QA pass before publishing, or a delivery may have technical problems. Not for creative critique of direction or script (director, scriptwriter).
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

Dailies review of generated footage (continuity of face, outfit, location, movement across takes) belongs to the footage recipes and is not part of this v1 explainer check.
