# Higgsfield MCP for video takes

Read on 2026-10-27 from the Higgsfield MCP tool descriptions available in that session (`generate_video`, `manage_reference_elements`, `reframe`, `upscale_video`). The `models_explore` catalog tool was not exposed there, so durations, aspect ratios and media roles were **not** verified; check them in the catalog before relying on them and record the date.

## Models named by the tools

| Model | Described use |
| --- | --- |
| `seedance_2_5` | default for general video |
| `kling3_0` | multi-shot, audio, motion transfer; honours elements only when a `start_image` is supplied |
| `minimax_h3` | 2K keyframes or mixed references |
| `cinematic_studio_3_0`, `cinematic_studio_video_v2`, `seedance_2_0` | honour `<<<element_id>>>` placeholders |
| `hf_mult_motion_control` | transfer motion from a driving video (performance transfer) |
| `hf_mult_replace_object` | replace an object or character in a source video |

Element placeholders work only on the element-aware models listed in `studio-producer/scripts/prompting.py`; for others, the compiler attaches reference images as media.

## Calls

| Step | Tool | Notes |
| --- | --- | --- |
| Price | `generate_video` with `get_cost: true` | submits nothing |
| Upload inputs | `media_upload` → PUT bytes → `media_confirm` | `medias[].value` must be a media id or job id, never a URL |
| Generate | `generate_video` | `count: 1`; `use_unlim` only when the user asks |
| Wait / display | the job tools the server offers (for example `job_display`, `show_generation_by_ids`) | poll politely; never resubmit to "check" |
| Reframe (fallback) | `reframe` | per-request approval; `get_cost` supported |
| Upscale | `upscale_video` | per-request approval; no cost preflight, so state that to the user |

The server's own rule matches ours: on a transport timeout the outcome may be unknown — do not resubmit; reuse the job id and retry only after the original outcome is known.

## The fingerprint and media ids

The approval fingerprint covers the request content: model, prompt, duration, aspect ratio, and which project assets go in which roles. Uploading those assets and replacing their paths with media ids is transport, not a change. Swapping an asset, editing the prompt, or changing model, duration or ratio is a change and needs a new approval.
