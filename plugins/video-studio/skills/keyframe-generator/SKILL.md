---
name: keyframe-generator
description: Generate start (and optional end) keyframes for each camera shot of a Video Studio film from the continuity bible, under the project's Higgsfield image cap, and register them as anchors for AI video takes. Use whenever a cinematic project has an approved bible and shot list and needs first frames, start/end frames, style frames or a visual preview of shots before paid video generation, or when a shot's keyframe drifted and needs a new version.
---

# Keyframe Generator

A good first frame is the cheapest place to fix composition, identity and light before paying for video. Keyframes become `start_image` (and sometimes end) anchors for takes, and the user's approval of them is approval of the film's look.

Read [keyframe-craft.md](references/keyframe-craft.md).

## Plan

```sh
python3 <this-skill>/scripts/keyframes.py plan <project-dir> --canvas 16x9 [--ends] [--shot S03]
```

Writes `keyframes/requests-<canvas>.json`: one request per camera shot (and end frames with `--ends`), compiled from the shot's framing, action, refs, light source, the characters' acting baselines, the bible's look and negatives. Element-aware models (default `nano_banana_pro`) get `<<<element>>>` placeholders; others get reference images as media whose role names you must map to the model's declared roles. Read and fix the prompts before spending — they are drafts, not sacred text.

Plan each canvas separately; a 9:16 keyframe is composed for vertical, not cropped from 16:9.

## Generate under the image cap

For each request:

1. `generate_image` with `get_cost: true` for the estimate.
2. `keyframes.py reserve <project> --canvas 16x9 --shot S01 --frame start --estimate <credits>` — refuses when the image cap is missing or would be exceeded (stop and ask the producer to propose or raise it).
3. Call `generate_image` with the exact request, download the result.
4. `keyframes.py record <project> --canvas 16x9 --shot S01 --frame start --entry <ledger id> --file <path> --job-id <id>` — stores `keyframes/<canvas>/S01-start-v<N>.png` with provenance and links it from the shot.
5. Refused: `keyframes.py fail --entry <id>`. Timeout or lost response: `--uncertain`, check the job by id, never resubmit automatically.

Prefer a couple of variants (`count`) for the opening and hero shots only; one per ordinary shot keeps the cap healthy.

## Review

Show the keyframes as a storyboard in shot order with each shot's motivation. Check the four pillars against the bible (face, outfit, location and light direction, implied movement). Regenerate only the shots that fail — new versions never overwrite old ones. Approved keyframes hand off to `ai-video-generator`.
