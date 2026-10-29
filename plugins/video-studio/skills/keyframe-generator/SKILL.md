---
name: keyframe-generator
description: Generate start (and optional end) keyframes for each camera shot of a Video Studio film from the continuity bible, through Higgsfield or the Gemini API CLI under the project's image cap, and register them as anchors for AI video takes; preview many shots first on one low-cost Gemini contact-sheet board. Use whenever a cinematic project has an approved bible and shot list and needs first frames, start/end frames, style frames or a visual preview of shots before paid video generation, or a storyboard-style board of a whole sequence, or when a shot's keyframe drifted and needs a new version.
---

# Keyframe Generator

A good first frame is the cheapest place to fix composition, identity and light before paying for video. Keyframes become `start_image` (and sometimes end) anchors for takes, and the user's approval of them is approval of the film's look.

Read [keyframe-craft.md](references/keyframe-craft.md). For the Gemini provider, also read [gemini-api.md](../studio-producer/references/gemini-api.md).

## Preview a sequence on one board (optional)

Before paying for one keyframe per shot, `keyframes.py board <project> --canvas 16x9` puts up to 12 camera shots on one Gemini contact sheet. `board-preview` shows the command and estimate, `board-generate` runs one capped call and crops the sheet into `tiles-v1/<shot>-start.png`, and `board-split --inset` re-crops it. Read [boards.md](../studio-producer/references/boards.md). Review the whole sheet with the user in shot order. Tiles are previews only: never register them as keyframes, then plan finals with `--tiles <tiles folder>` so each chosen tile is attached as a composition reference.

## Plan

```sh
python3 <this-skill>/scripts/keyframes.py plan <project-dir> --canvas 16x9 [--ends] [--shot S03]
```

Writes `keyframes/requests-<canvas>.json`: one request per camera shot (and end frames with `--ends`), compiled from the shot's framing, action, refs, light source, the characters' acting baselines, the bible's look and negatives. Element-aware models (default `nano_banana_pro`) get `<<<element>>>` placeholders; others get reference images as media whose role names you must map to the model's declared roles. Read and fix the prompts before spending — they are drafts, not sacred text.

Plan each canvas separately; a 9:16 keyframe is composed for vertical, not cropped from 16:9.

Choose the provider per project, or per canvas, with the user. `--provider gemini` (default model `gemini-nano-banana-2.1`, `--image-size 2K`) plans `gemini-api image` requests. Gemini has no elements, so bible images are attached as inputs and the prompt names each subject with its preserve list.

## Generate under the image cap (Higgsfield)

For each request:

1. `generate_image` with `get_cost: true` for the estimate.
2. `keyframes.py reserve <project> --canvas 16x9 --shot S01 --frame start --estimate <credits>` — refuses when the image cap is missing or would be exceeded (stop and ask the producer to propose or raise it).
3. Call `generate_image` with the exact request, download the result.
4. `keyframes.py record <project> --canvas 16x9 --shot S01 --frame start --entry <ledger id> --file <path> --job-id <id>` — stores `keyframes/<canvas>/S01-start-v<N>.png` with provenance and links it from the shot.
5. Refused: `keyframes.py fail --entry <id>`. Timeout or lost response: `--uncertain`, check the job by id, never resubmit automatically.

## Generate under the image cap (Gemini)

1. `keyframes.py preview <project> --canvas 16x9 --shot S01` prints the exact command, the USD estimate and the CLI's offline `--dry-run`. Fix any reported problems or missing inputs first.
2. `keyframes.py generate <project> --canvas 16x9 --shot S01 [--frame start]` checks the `gemini-image` cap (USD), records the entry, runs the CLI once and stores the keyframe as above. When no published price covers the model and size, it refuses until you pass `--estimate` with the figure you showed the user.
3. A validation or authentication refusal is recorded as `failed`. A timeout or unclear failure stays `unknown` and counted. Tell the user, and do not run `generate` for that frame again until they decide.

Prefer a couple of variants (`count`) for the opening and hero shots only; one per ordinary shot keeps the cap healthy.

## Review

Show the keyframes as a storyboard in shot order with each shot's motivation. Check the four pillars against the bible (face, outfit, location and light direction, implied movement). Regenerate only the shots that fail — new versions never overwrite old ones. Approved keyframes hand off to `ai-video-generator`.
