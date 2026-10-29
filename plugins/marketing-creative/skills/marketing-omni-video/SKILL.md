---
name: marketing-omni-video
description: Deprecated Marketing Creative skill for explicitly approved Omni Flash marketing clips, edits and extensions. For new work use ai-video-generator with --provider gemini (video-studio plugin). Use this only to resume or revise an existing Marketing Creative project.
---

# Marketing Omni Video

> **Deprecated.** Marketing Creative is being retired in favour of Video Studio and Marketing Images. For new work, use `$ai-video-generator` with `--provider gemini` (video-studio plugin). Use this skill only to resume or revise an existing Marketing Creative project, and keep that project's files intact.

Generate a standalone marketing video or a clip for [motion-video-producer](../motion-video-producer/SKILL.md), which owns final assembly with images, footage, animation, typography and audio. This skill is opt-in because generation costs more than ordinary local composition. General production permission or a request to plan does not authorize paid Omni use.

## Prepare and obtain approval

Read [capabilities.md](references/capabilities.md) for supported modes and limits; read [workflow.md](references/workflow.md) for configuration, media roles and recovery. View source media, preserve approved claims and selection, and choose text, image, interpolation, loop, reference, edit, extension or upscale mode. Explicit source/reference bindings prevent a character reference from accidentally becoming the first frame or edit target.

Run [omni_video.py](scripts/omni_video.py) submit --dry-run. Present the actual prompt/media, model, mode, duration, ratio, resolution, storage choices and a current cost estimate. Ask for explicit approval of that request before submitting with its requestSha256 as --approve-request and a factual --approval-note. Every additional edit, extension, upscale or regeneration is a new paid call requiring approval covering that request. A preview-model fallback is not automatic.

## Run and recover

The script reads exported GEMINI_API_KEY via the README's external credential setup; it never loads .env. Preserve unique run directories, interaction IDs, original creation URIs and returned MP4 bytes. Background requests use stored state; streaming checkpoints identity and complete media steps. status queries once; download checks file readiness and measures actual media. An uncertain submission is investigated, never automatically repeated. Cancellation is best effort for running background interactions and is used only when the user asks.

For a follow-up change, resume the selected video's saved run through the Python helper's history RUN and continue RUN REVISION_CONFIG commands. Continue from the latest intended version rather than restarting generation or re-uploading the clip. Omitted model, ratio, resolution and edit duration inherit from that run; new media paths resolve relative to the revision config. Record each returned run directory in project/session notes so later requests can resume after a Python or chat restart. Read the workflow's conversation example for approval, branching and recovery.

Stored previousRun or previousInteractionId also enables conversational revisions. store=false disables future retrieval/editing of that turn; retain the creation output locally. Uploaded sources have stricter duration/region limits than model-generated multi-turn footage. Reference-video sound is ignored; standalone audio references and voice editing are unsupported. Put desired dialogue, music, sound and ordinary negative constraints in the prompt. Use motion-voice for narration revisions instead of asserting Omni voice-edit support.

## Review and handoff

Inspect actual frames, motion, text, claims, product/character identity and transitions; listen to sound. A higher output resolution can be upscaled, so inspect detail rather than claiming new native detail. Verify whether an extension returned the combined scene or a continuation, then use its measured runtime. Never certify timing from prompt timestamps alone.

Show standalone assets with review notes, or pass local files, hashes, provenance, measured dimensions/duration/audio and sound policy to motion-video-producer. Native 16:9/9:16 footage is recomposed for final 4:5/1:1 canvases there. Generated depictions are illustrative assets, not verified product proof or customer testimony.
