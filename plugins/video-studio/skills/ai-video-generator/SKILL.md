---
name: ai-video-generator
description: Compile, get approval for, submit and ingest AI video takes (Higgsfield MCP or the Gemini API CLI) for a Video Studio film — one take covering one or several consecutive shots, built from the shot list and continuity bible, approved per exact request, then split into shot clips and selected; also plans single-shot retakes anchored on neighbouring clips. Use whenever a cinematic project has timed camera shots (and ideally approved keyframes) and needs generated footage, a retake of one shot, or a different video model. Paid and opt-in; nothing is sent without the user's approval of that exact request.
---

# AI Video Generator

Turn approved shots into footage without surprises: every request is compiled from the project files, shown to the user with its price, approved as-is, and only then sent. The helper keeps the request, its fingerprint, the job id and the resulting clips together so an interrupted job can be recovered instead of paid for twice.

Read [prompt-anatomy.md](references/prompt-anatomy.md) for what the compiled prompt contains, [higgsfield.md](references/higgsfield.md) for the MCP flow, models and verification notes, and [gemini-api.md](../studio-producer/references/gemini-api.md) for the Gemini CLI provider.

## Plan

```sh
python3 <this-skill>/scripts/takes.py plan <project-dir> --canvas 16x9 [--model seedance_2_5] [--take T1]
python3 <this-skill>/scripts/takes.py show <project-dir> --take T1-16x9
```

Shots sharing a `take` id become one request (each other camera shot its own). The prompt is compiled from the logline, reference roles and preserve lists, locks, environment and light, a timed beat per shot (action, camera, light, sound, dialogue), camera language, acting baselines, audio policy, negatives and a final priority. The approved keyframe becomes `start_image`. Edit the shot list or bible — not the compiled prompt — and re-plan, so the files stay the source of truth.

`--provider gemini` (default model `gemini-omni-1.1-flash`, `--resolution 720p`) plans `gemini-api video` requests instead. The plan refuses canvases other than 16:9 and 9:16, and takes outside 3–10 s. A keyframe becomes the first input frame (`image_to_video`); without one, bible images become references. The take records `estimate_usd` when a published rate covers the resolution.

Check the chosen model's limits and media roles first (`models_explore` when available): maximum duration (also set as `max_take_seconds` in the shot list), supported aspect ratios, whether it honours `<<<element>>>` placeholders, and the role names it expects for start images and references.

## Approve, submit, record

1. Get the price: call `generate_video` with the request's parameters and `get_cost: true`.
2. Show the user the take: shots and timing, model, duration, aspect ratio, references and roles, the full prompt, and the price. Ask for approval of this request.
3. After a clear yes: `takes.py approve <project> --take T1-16x9 --estimate <credits>`.
4. Right before the call: `takes.py submit <project> --take T1-16x9` — refuses if anything changed since approval.
5. Upload referenced assets (`media_upload` → PUT → `media_confirm`), map them into `medias` with the model's roles, call `generate_video` once, and immediately run `takes.py job <project> --take T1-16x9 --job-id <id>`.
6. On a refusal: `takes.py fail --take …`. On a timeout or lost response: `takes.py fail --take … --uncertain`, check the job by id, and never resubmit automatically.

General production permission, an earlier approval, or an approval of a different request never authorizes a submission.

**Gemini takes** use the same approval, with these differences:

1. `takes.py preview <project> --take T1-16x9` shows the exact `gemini-api` command, the USD estimate, missing inputs and the CLI's offline `--dry-run`. Show the user the shots, model, duration, ratio, resolution, input images, full prompt and estimate.
2. After a clear yes: `takes.py approve … --estimate <USD>`.
3. `takes.py submit <project> --take T1-16x9` consumes the approval, runs `gemini-api video --async` once and records the interaction id. A refusal (exit 2 or 3) marks the take `failed`. A timeout or other failure marks it `unknown`: inspect the id or the provider console, and never submit it again automatically.
4. `takes.py fetch <project> --take T1-16x9` waits on that interaction (`--resume`; polling never regenerates), downloads the video and runs the ingest below. If it times out, run it again; the take keeps its status.

## Ingest and split

For Higgsfield, download the finished video, then:

```sh
python3 <this-skill>/scripts/takes.py ingest <project-dir> --take T1-16x9 --file <downloaded.mp4>
```

It stores `takes/<take>/raw.mp4`, marks the paid job succeeded, and splits the take into `takes/<take>/clips/<shot>.mp4` at detected cuts. If the detected cuts do not match the planned ones, the take becomes `needs-split` with both lists; look at it, then split at the times you confirm with the user (`takes.py split --take … --at 3.1`). Never accept a silent remap.

## Dailies, select, retake

Run `qc-reviewer dailies` on every new take before selecting it. Select clips per shot:

```sh
python3 <this-skill>/scripts/takes.py select <project-dir> --take T1-16x9 [--shot S02]
python3 <this-skill>/scripts/takes.py retake <project-dir> --canvas 16x9 --shot S02 [--with-end] [--provider gemini]
```

A retake is a single-shot take anchored on the last frame of the previous selected clip (and the first frame of the next with `--with-end`, if the model supports end frames). It goes through the same approve → submit → ingest flow. Retake only shots that failed dailies.

Compose each canvas from its own takes. Reframing a finished take to another aspect ratio is a labelled fallback that needs its own per-request approval.
