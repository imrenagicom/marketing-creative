# Gemini API CLI (`gemini-api`) for images and video

An alternative to Higgsfield for bible reference images, keyframes and video takes. Unlike the Higgsfield MCP, the helpers run the CLI themselves, so the command sent is derived from the stored request and its fingerprint.

Read on 2026-10-29 from [google-gemini/gemini-api-cli](https://github.com/google-gemini/gemini-api-cli) (`main` at `68ce6f1`, 2026-10-28: README, `image`/`video` command sources and the bundled `CreateInteraction` schema), the [pricing page](https://ai.google.dev/gemini-api/docs/pricing) and the [Omni guide](https://ai.google.dev/gemini-api/docs/omni). The CLI is beta and may change between releases: pin a release, and re-check this page when you upgrade.

## Setup

Install a release binary (or `go install github.com/google-gemini/gemini-api-cli/cmd/gemini-api@latest`) and put `gemini-api` on `PATH`. Authenticate with an exported `GEMINI_API_KEY` (kept in `~/.config/marketing-creative/.env` or a secret manager and exported by the user) or `gemini-api configure`; check with `gemini-api whoami`. The helpers never read or print the key. Set `VIDEO_STUDIO_GEMINI_BIN` to use a binary outside `PATH`.

## What the helpers run

| Use | Command derived from the request | Notes |
| --- | --- | --- |
| Reference image, keyframe, board ([boards.md](boards.md)) | `gemini-api image "<prompt>" --body '{model, response_format{type:image, aspect_ratio, image_size}}' -i <ref>… --out <dir> --output-format json` | Synchronous; returns `{path, response_id}` |
| Video take | `gemini-api video "<prompt>" --body '{model, response_format{type:video, aspect_ratio, resolution, duration}, generation_config.video_config.task}' -i <frame>… --async --output-format json` | Returns the interaction id at once; recorded before anything else |
| Download a take | `gemini-api video --resume <id> --out <dir> --output-format json` | Polls the existing interaction; never generates again |
| Preview | the same command plus `--dry-run` | Offline: validates and prints the redacted request; no key, no network |

Exit codes: `0` success, `2` invalid usage, `3` authentication — both mean nothing was generated, so the ledger entry is `failed`. `1` (runtime/API failure), a timeout or unreadable output may mean the request was accepted, so the entry stays `unknown`, counted, and is never resubmitted automatically. For a video, inspect the recorded id with `gemini-api agent status <id> --stream=false --output-format json` first.

## Models and limits

| Kind | Models | Limits used by the helpers |
| --- | --- | --- |
| Image | `gemini-nano-banana-2.1` (CLI default), `gemini-3-pro-image`, `gemini-3.1-flash-image`, `gemini-3.1-flash-lite-image` | Aspect 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9; size 512, 1K, 2K, 4K (not every model prices every size) |
| Video | `gemini-omni-1.1-flash` (CLI default), `gemini-omni-flash-preview` | **16:9 and 9:16 only**; 360p, 720p (default), 1080p and 4k (the last two upscaled); 3–10 s per generation |

There are no Higgsfield-style elements. Identity comes from reference images passed with `-i` and named in the prompt. For video, the input order is the binding: with a start frame the task is `image_to_video` (first image = first frame, optional second = last frame) and bible references are not attached, so they cannot be mistaken for an end frame; without a start frame, reference images go in as `reference_to_video`; with neither, `text_to_video`.

**Veo is not available here.** Google shut down Veo 3.1 Preview in the Gemini API on 2026-10-22 and names `gemini-omni-1.1-flash` as the replacement ([deprecations](https://ai.google.dev/gemini-api/docs/deprecations), checked 2026-10-29). The GA Veo models run only on Google Cloud's Gemini Enterprise Agent Platform, which Video Studio does not integrate. Use Omni here or a Higgsfield model.

4:5 and 1:1 takes cannot be generated natively. Use Higgsfield for those canvases, or a labelled, separately approved reframe. A take longer than 10 s must be regrouped into shorter takes. Prompt timecodes are directions, not guaranteed cut points: the split check still applies.

## Prices (USD, Standard paid tier, 2026-10-29)

No free tier is listed for these models.

| Model | Per image |
| --- | --- |
| `gemini-nano-banana-2.1` | 1K $0.0336 · 2K $0.0504 · 4K $0.113 |
| `gemini-3-pro-image` | 1K/2K $0.134 · 4K $0.24 |
| `gemini-3.1-flash-image` | 512 $0.045 · 1K $0.067 · 2K $0.101 · 4K $0.151 |
| `gemini-3.1-flash-lite-image` | 1K $0.0336 |

Image estimates cover output only; input tokens for the prompt and references are billed on top at the model's input rate.

`gemini-omni-1.1-flash` video is about **$0.10 per second at 720p** (5,792 output tokens per second at $17.50 per million). No 360p, 1080p or 4k rate is published, so the helpers give no estimate there. Look up the current rate, show it to the user, and pass it as `--estimate`. An estimate is not a billing ceiling.

## Budgets

- `gemini-image` is a per-project cap **in USD**, approved once, like `higgsfield-image`.
- `gemini-video` needs approval of each exact request, like `higgsfield-video`. The fingerprint covers model, prompt, duration, aspect ratio, resolution, task and the project paths of the input images.

A provider response is evidence that a file was returned, not that it looks right. Every take still goes through dailies.
