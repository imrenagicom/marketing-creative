---
name: marketing-image-producer
description: Generate marketing images from a brief, optional reference images or selected concept-board tiles using Nano Banana, individually or through Gemini's discounted asynchronous Batch API. Use for final Instagram posts, carousel assets and image ads.
---

# Marketing Image Producer

Produce the authorized image deliverable from the marketing/creative brief and any supplied reference images. References are optional, including for direct generation without a board. For exploratory alternatives, use [marketing-image-board](../marketing-image-board/SKILL.md) first; a supplied selected concept can enter here directly.

Read supplied references and selected tiles using available viewing tools. Identify each reference's role, such as product, style, logo or character. Preserve product identity, evidence, approved copy and the chosen direction. A tile is a layout reference, not a source of new facts.

## Choose delivery mode

Read [image-workflow.md](references/image-workflow.md) for Python setup, plan shape, commands and artifacts. Use [gemini_images.py](scripts/gemini_images.py):

- image: one selected standalone asset from the brief, optionally with references and its preview tile.
- batch-submit: one asynchronous Gemini Batch API job with separate requests for selected final assets. This is the discount mechanism; concurrent synchronous calls are not discounted batch inference.
- batch-status / batch-download: resume a saved job without submitting again.
- batch-cancel: request cancellation when the user asks; cancellation is best effort.

Default model is gemini-nano-banana-2.1, latest verified on 2026-10-15. It supports 1K/2K/4K and the documented image ratios, including all four video-suite ratios. See [gemini-api.md](references/gemini-api.md) for official sources and refresh guidance. Use --model explicitly for a deliberate alternate model; never silently substitute or assert a pinned model remains latest forever.

## From previews to finals

Select the actual approved item IDs. Supply --tiles to include each selected crop along with any original references. References can be set in the plan or with repeated --reference paths. Request a standalone reconstruction of the chosen design, not a grid or mere upscale. Default finals use 4K; select 2K or 1K when appropriate. Higher resolution alone does not guarantee better composition, identity or spelling.

Recompose at the requested supported image ratio. Distinguish canvas ratio from current platform placement specifications. Keep captions/CTAs/brand marks within verified placement-safe areas. For multiple ratio versions of one idea, create separate stable item IDs in the plan. Grid cropping never certifies current Meta upload requirements.

## Spend, persistence and failures

Run --dry-run first for request count, model, reference hashes and payload size; it reads no key and makes no calls/writes. The helper reads GEMINI_API_KEY only from the environment; it does not load .env automatically. Use the README's external key setup.

Actual paid runs create a unique run directory with submission state before making requests. Do not overwrite it or automatically resubmit on timeout; use the saved jobName or inspect AI Studio using displayName if the outcome is unknown. File-backed jobs retain inputFile for manual cleanup/recovery. Status/download commands make one bounded query and return; do not block the chat with a 24-hour polling loop.

A succeeded batch can contain failed items. Download preserves successful images and writes per-item errors; interrupted collection resumes by verifying existing files. Unexpected ratios are saved and flagged for review. Retry only chosen failed IDs in a new explicit job when authorized. No automatic paid fallback or retry.

## Review and handoff

Inspect every generated image at delivery size. Check exact copy, logos/product fidelity, claims, composition, placement crop and generated-art labeling where relevant. A model can render incorrect text; ask for textless imagery plus deterministic typography when exact typesetting is needed. Do not declare an image reviewed from an HTTP success.

Show native/local images to the user. Keep assets.json, original reference/plan, selected IDs, actual dimensions, generation model and review notes with the campaign. For a video, register the reviewed image and hash in its asset manifest; this skill does not render video or publish ads.
