# Marketing Creative and Performance

Four independently installable plugins cover campaign planning, copywriting, analytics and creative production. Marketing Performance owns `marketing-brief`, `marketing-copywriter`, `campaign-manager` and `google-analytics-analyst`; Marketing Images owns `marketing-image-board` and `marketing-image-producer` for campaign images; Marketing Creative owns eleven skills for ideas, scripts and videos; Video Studio is a from-scratch video studio for explainers and cinematic short films with thirteen stage skills ([design](docs/video-studio-design.md)). Codex, Claude Code and Google Antigravity use the same source. Production supports **16:9, 9:16, 4:5 and 1:1** as independently composed and reviewed variants.

## One campaign, every plugin

The plugins serve one purpose: producing a marketing campaign. `campaign-manager` (marketing-performance) creates the campaign workspace, `marketing/campaigns/<YYYY-MM-DD>-<campaign-name>/`, with its brief, Meta Ads and social trees, tracking and reports. The creative plugins work inside it:

- Marketing Images plans boards and finals in an ad's or post's `assets/development/images/` and files approved images into `assets/approved/vNNN/images/`.
- Video Studio creates its project in `assets/development/video/<YYYY-MM-DD>-<slug>/`, records the link with `campaign.py link`, and after QC and the user's approval runs `campaign.py handoff` to file the deliveries into `assets/approved/vNNN/video/` with `assets.json`.
- `marketing-copywriter` writes the copy and alt text. `campaign-manager` updates revision pointers and UTMs and writes performance reports.

Every creative skill reads the campaign brief, approved claims, CTA and required ratios instead of repeating intake. None of them publishes or edits the campaign's `campaign.json`, `ad.json` or `post.json`.

## Skills and handoffs

| Skill | Input → output |
| --- | --- |
| `marketing-video` | Topic, brief, script or existing video → appropriate workflow stages and requested video deliverables |
| `campaign-manager` (marketing-performance) | Product campaign → `<YYYY-MM-DD>-<campaign-name>` workspace, paid ad hierarchy (`meta-ads/campaigns/.../adsets/.../ads/...`), social media trees (`instagram/`, `linkedin/`, `twitter/`), timestamped performance reports (`reports/<datetime>.md`), storyboard/media development & approved copy/asset revisions, and UTM links |
| `google-analytics-analyst` (marketing-performance) | GA4 / Firebase project & campaign UTMs → GA4 Data API funnel reports, ad-click-to-session reconciliation, drop-off diagnosis and recommendations |
| `marketing-brief` (marketing-performance) | Product facts, research and goal → strategic brief, evidence, placement requirements |
| `marketing-copywriter` (marketing-performance) | Brief or draft → exact ad, landing-page, email or social copy, voice/style variants and localization |
| `creative-ideation` | Marketing brief → distinct concepts and selected creative brief |
| `marketing-image-board` (marketing-images) | Brief, concepts and optional references → one board with a chosen tile count/ratio and locally cropped previews |
| `marketing-image-producer` (marketing-images) | Brief or selected concepts/tiles, with optional references → standalone image assets or discounted asynchronous Gemini batches |
| `marketing-veo-video` | Explicitly approved Veo request → generated marketing video or clip with measured metadata and provenance |
| `marketing-omni-video` | Explicitly approved Omni Flash request → reference-driven video, conversational edit, extension or upscaled clip |
| `ad-video-director` | Selected idea and brief → exact script, copy, shot direction and production handoff |
| `motion-video-producer` | Authorized production request → assembled images, clips, Three.js/HTML scenes and audio in one reviewed project |
| `motion-art-director` | Selected concept and brand → visual system, camera and motion language |
| `motion-storyboard` | Script and style → visual beats, semantic cues and per-ratio framing |
| `motion-voice` | Narration/script → aligned audio, measured loudness, cue-based pause classes and backed-up phrase replacement |
| `motion-composer` | Resolved storyboard → seekable HyperFrames compositions in requested ratios |
| `motion-video-qa` | Source/build/export → integrity checks, frame review and encoded-file verification |

Use only the stages needed. Supplied briefs, selected ideas and recordings enter downstream; small revisions do not restart intake. Planning alone does not launch campaigns or render a video. A general explainer can bypass advertising strategy. Existing ad-video-director invocations continue to work, with strategy and ideation routed to their new owners when needed.

Start video work with [`marketing-video`](plugins/marketing-creative/skills/marketing-video/SKILL.md) (Claude: `/marketing-creative:marketing-video`). It explains the topic/brief → concept → script/style → voice → beat plan → composition → QA → exports workflow, selects the missing stages and routes revisions from the changed dependency. `motion-video-producer` remains responsible for the production project and final exports; every focused skill remains directly usable. Existing scripts, recordings and projects skip completed stages.

`motion-storyboard` develops each beat from its job to its hero visual, visible action, framing/zones and cue-driven handoff before composition. Its [beat-planning reference](plugins/marketing-creative/skills/motion-storyboard/references/beat-planning.md) includes concrete visual choices and editorial review gates. Those gates complement executable timing/visibility checks; they do not claim to predict retention.

`motion-voice` normalizes newly generated narration to configurable working targets (default −16 LUFS / −1.5 dBTP / LRA 9), with --no-normalize available. Imports preserve source level unless --normalize is requested. Existing takes use the local normalize command. Cue-based pause classes let ordinary/step pauses use different caps and null preserve dramatic gaps. See [loudness and pause controls](plugins/marketing-creative/skills/motion-voice/references/loudness-and-pauses.md); these mono-source targets do not certify the finished mix.

## Video Studio

`plugins/video-studio/` produces explainer videos and cinematic short films in English or Indonesian. Each stage skill reads and writes one JSON project contract, so work resumes from any stage:

| Skill | Input → output |
| --- | --- |
| `studio-producer` | Idea, campaign brief or existing project → project files linked to the campaign, next stage, language choice, approved budgets and the approved-asset handoff |
| `director` | Idea or brief → 2–3 direction options (hook, beats, acting baselines, visual plan) → the user-approved direction lock |
| `scriptwriter` | Direction lock → native English or Indonesian script with register, delivery and on-screen keywords |
| `voice-director` | Script → ElevenLabs narration take (via the `elevenlabs` CLI) and word timestamps, or alignment of a supplied recording |
| `shot-designer` | Script and timings → linted shot list timed to the words |
| `motion-designer` | Timed shots → HyperFrames compositions per canvas with keywords landing on the spoken word |
| `editor` | Compositions or selected footage clips → versioned renders with a ducked sound mix, SRT/VTT captions and loudness-finished deliveries |
| `qc-reviewer` | Generated take → dailies against the continuity pillars; render version → technical checks, a frame per shot and the human checks still required |
| `reference-analyst` | Reference video → cuts, pacing, frames, audio stats and a techniques-vs-style report |
| `continuity-bible` | Direction lock → characters, locations with motivated light, props, locks, reference images (Higgsfield or Gemini API), look-option contact-sheet boards and Higgsfield elements |
| `keyframe-generator` | Camera shots and bible → optional one-call contact-sheet board of a sequence, then start/end frames under a per-project Higgsfield or Gemini image cap |
| `ai-video-generator` | Timed shots, bible and keyframes → Higgsfield or Gemini API takes approved per exact request, split into shot clips; single-shot retakes (opt-in) |
| `sound-designer` | Shot sounds and audio policy → ElevenLabs sound effects, ambience beds and optional music placed on the timeline |

Explainers are narration-first: word timestamps time every shot. Films are continuity-first: the bible and shot plan come before any generation. ElevenLabs calls and Higgsfield or Gemini images run under per-project caps you approve once (`ledger.py`); every Higgsfield video, reframe or upscale request and every Gemini video request needs your approval of that exact request. Requirements: Python 3.10+, FFmpeg/FFprobe, Node.js 22+ for HyperFrames rendering, the `elevenlabs` CLI signed in with `elevenlabs auth login` (keychain) or `ELEVENLABS_API_KEY`, and for films either a connected Higgsfield MCP server or the [`gemini-api` CLI](https://github.com/google-gemini/gemini-api-cli) on `PATH` with an exported `GEMINI_API_KEY` (or `gemini-api configure`). Gemini video is generated natively only in 16:9 and 9:16, 3–10 s per take; see the [Gemini reference](plugins/video-studio/skills/studio-producer/references/gemini-api.md). Start with `$studio-producer` (Claude: `/video-studio:studio-producer`).

## Install

Plugins live in `plugins/marketing-creative/`, `plugins/marketing-images/`, `plugins/marketing-performance/` and `plugins/video-studio/`. Install either or both complete trees; each plugin contains its own required resources and host manifests for Codex (`.codex-plugin/plugin.json`), Claude Code (`.claude-plugin/plugin.json`) and Google Antigravity (`plugin.json`). Creative production accepts supplied briefs without the Performance plugin.

### Codex

```sh
codex plugin marketplace add /absolute/path/to/marketing-creative
codex plugin add marketing-creative@marketing-creative
codex plugin add marketing-images@marketing-creative
codex plugin add marketing-performance@marketing-creative
codex plugin add video-studio@marketing-creative
codex plugin list --marketplace marketing-creative --json
```

Or register `imrenagicom/marketing-creative` after the relevant release is published (`codex plugin marketplace add imrenagicom/marketing-creative`). Reload the client if needed. Invoke `$marketing-brief`, `$creative-ideation`, or any skill in the table.

### Claude Code

```sh
claude plugin marketplace add /absolute/path/to/marketing-creative
claude plugin install marketing-creative@marketing-creative
claude plugin install marketing-images@marketing-creative
claude plugin install marketing-performance@marketing-creative
claude plugin install video-studio@marketing-creative
claude plugin details marketing-creative
claude plugin details marketing-performance
```

After publication, use `claude plugin marketplace add imrenagicom/marketing-creative` instead of the local path. Inside Claude Code, the equivalent commands begin with `/plugin marketplace add` and `/plugin install`. For temporary development without installation, use `claude --plugin-dir ./plugins/marketing-creative --plugin-dir ./plugins/marketing-performance`. Invoke `/marketing-performance:marketing-brief` or `/marketing-creative:creative-ideation`, for example. `marketing-brief` has moved: its Claude namespace is now `marketing-performance`; its Codex and Antigravity invocation remains `marketing-brief` / `$marketing-brief`.

### Google Antigravity

From a checkout or an extracted plugin archive (`marketing-creative-plugin.zip`, `marketing-images-plugin.zip`, `marketing-performance-plugin.zip` or `video-studio-plugin.zip`):

```sh
agy plugin install /absolute/path/to/marketing-creative/plugins/marketing-creative
agy plugin install /absolute/path/to/marketing-creative/plugins/marketing-images
agy plugin install /absolute/path/to/marketing-creative/plugins/marketing-performance
agy plugin install /absolute/path/to/marketing-creative/plugins/video-studio
agy plugin list --json
```

Inside an interactive Antigravity CLI session, run `/plugin install /absolute/path/to/marketing-creative/plugins/marketing-creative` and `/plugin install /absolute/path/to/marketing-creative/plugins/marketing-performance` (or select *Install from local directory* in the `/plugin` manager). Installed plugins are staged under `~/.gemini/config/plugins/marketing-creative/` and `~/.gemini/config/plugins/marketing-performance/` and synchronized across the Antigravity App, IDE, and CLI; restart if newly installed skills do not appear immediately. When opening the `marketing-creative` repository itself as a workspace in Antigravity, `.agents/plugins.json` automatically registers all four plugins and their 30 skills without requiring global installation.

For clients without plugin support, reference the complete skill tree from the client's instruction file, retaining all sibling skills and third-party/ notices. No global installation or client configuration is changed by this repository.

## Example requests

> Use $marketing-video to turn this topic into a 30-second Indonesian explainer for Reels. Develop the script, narration, beat plan and finished vertical video using our supplied brand assets.

> Use $marketing-video with this approved script and recording. Produce 16:9, 9:16, 4:5 and 1:1 versions; preserve the wording and voice, plan each ratio's visual zones, and deliver verified exports.

> Use $marketing-video to revise this project's CTA and fix the crowded result beat. Preserve the rest of the take and rebuild the affected variants.

> Use $marketing-brief for our task app. Goal: users completing their first assignment. Audience: small design teams. We have real captures but no verified trial offer. Plan Meta feed, Reels, landscape and square deliverables.

> Use $marketing-copywriter with this brief to draft ad copy and a matching landing-page hero in English and Indonesian. Give me two variants that test different benefit emphases, keep the supplied offer and destination, and flag unsupported claims.

> Use $creative-ideation with this marketing brief. Give me three distinct directions, explain the evidence each needs, and recommend one.

> Use $ad-video-director to turn the selected demonstration concept into a 20-second Indonesian script. Preserve the brief's objective, offer and destination.

> Use $motion-video-producer to produce the selected concept in 16:9, 9:16, 4:5 and 1:1. Recompose for each placement and review every output.

> Use $motion-voice to replace this CTA in the existing recording. Preview the matched phrase first, preserve the original take and retime downstream cues.

> Use $marketing-image-board with this product image and marketing brief. Show nine distinct Instagram/ad concepts in one square 3×3 board, then split the previews locally.

> Use $marketing-image-board with this brief and any attached references. Choose a useful number of concepts and a portrait or landscape sheet layout. Ensure each concept can be cropped separately.

> Use $marketing-image-producer to regenerate my three selected tiles as separate 4K assets through Gemini's discounted Batch API. Keep the original source image as the product reference.

## Marketing copy

Use `$marketing-copywriter` (Claude: `/marketing-performance:marketing-copywriter`) for exact wording or revisions from an existing brief or draft. It can prepare multiple complete versions with different voices, tones, styles and selling intensity: personal experience sharing, a friendly useful-find recommendation, a warm explanation or a direct sales pitch. Firsthand stories use the actual speaker's supplied experiences; warm copy can also work from product facts alone. It preserves supported claims and offer terms, and provides meaningful test variants or localization when requested. Copy is returned in chat unless saving is part of the task. Full timed video scripts and shot direction remain with `ad-video-director`; drafting copy does not publish a campaign or send email.

> Use $marketing-copywriter to turn these product facts and my experience notes into four complete Instagram captions: candid personal story, friend-to-friend recommendation, playful explanation and direct selling. Keep the same facts and destination, make the voices distinct, and avoid adding experiences I did not provide.

## Campaign records, UTMs and performance reports

Use `$campaign-manager` (Claude: `/marketing-performance:campaign-manager`) to combine marketing operations naming rules with paid ad hierarchies (`meta-ads/`), social media campaign structures (`instagram/`, `linkedin/`, `twitter/`), chronological campaign performance reports (`reports/<datetime>.md`), creative/copy revision tracking and tagged links. It reuses the current workspace's campaign directory, or defaults to `marketing/campaigns/`, with a shared index/convention and a `<YYYY-MM-DD>-<campaign-name>` directory per new campaign. Under `meta-ads/campaigns/<meta-campaign-slug>/adsets/<adset-slug>/ads/<ad-slug>/`, each Meta campaign records its goal and budget limits (`campaign.json`), each ad set records its user targeting and placements (`adset.json`), and each ad self-contains its destination link/UTM spec (`ad.json`), working copy (`copy/drafts/`) vs. versioned approved copy (`copy/approved/v001/`, `v002/`, ...), and storyboard/media development (`assets/development/` with `storyboard/`, `images/`, `video/`, `audio/`) vs. versioned approved deliverables (`assets/approved/v001/`, `v002/`, ...). At the same top level under `<YYYY-MM-DD>-<campaign-name>/`, social media directories (`instagram/posts/<post-slug>/`, `linkedin/posts/<post-slug>/`, `twitter/posts/<post-slug>/`) organize each social post's `post.json`, working and approved copy/captions (`copy/drafts/`, `copy/approved/vNNN/`), and storyboard/media development vs. approved assets (`assets/development/`, `assets/approved/vNNN/`), while `reports/<datetime>.md` stores unified Meta Ads + Google Analytics + backend funnel reviews, actions taken, lessons learned and next checkpoints. When a social post reuses an approved image/video from `meta-ads/` (or vice versa), it copies the approved file into its own `assets/approved/v001/` directory to keep a self-contained record without regenerating media, and omits `assets/development/`. Plans, measurement notes, change history and versioned CSV/Markdown tracking exports (`tracking/v001/`) stay in the product workspace for review and Git commits. The skill does not automatically commit or publish campaigns.

> Use $campaign-manager for our product activation campaign across Meta Ads (`meta-ads`) and social media (`instagram`, `linkedin`, `twitter`). Reuse the existing brief and tagging conventions. Create the `<date>-campaign-name` workspace with `meta-ads/campaigns/.../adsets/.../ads/...` and `{instagram,linkedin,twitter}/posts/...` specs, copy/asset directories and destination URLs, and save the campaign plan, measurement checks and UTM registry in this workspace.

The bundled static URL helper needs Python 3.10+ and no API keys or external packages:

```sh
UTM_TOOL="$PWD/plugins/marketing-performance/skills/campaign-manager/scripts/build_utm.py"
# Replace with your saved plan; the bundled example is fictional.
python3 "$UTM_TOOL" /path/to/product/marketing/campaigns/2026-10-18-campaign-name/campaign.json --dry-run
python3 "$UTM_TOOL" /path/to/product/marketing/campaigns/2026-10-18-campaign-name/campaign.json --out /path/to/product/marketing/campaigns/2026-10-18-campaign-name/tracking/v001
```

Use the next unused revision (`v001`, `v002`, ...) for changes to tracking exports, approved copy or approved assets. Existing exports and published link identities are preserved; conflicts with destination UTMs need explicit resolution. The helper preserves other query parameters/fragments, encodes values once, emits `url_tags` for Meta URL parameters, and validates `meta-ads/campaigns/` and `{instagram,linkedin,twitter}/posts/` specs against `campaign.json` when present. Local validation does not prove redirect preservation or analytics collection; record those checks separately. The [workspace record contract](plugins/marketing-performance/skills/campaign-manager/references/workspace-records.md), [performance reporting structure](plugins/marketing-performance/skills/campaign-manager/references/reporting.md), [Meta Ads hierarchy contract](plugins/marketing-performance/skills/campaign-manager/references/meta-ads.md), [social media structure](plugins/marketing-performance/skills/campaign-manager/references/social-media.md), [link schema](plugins/marketing-performance/skills/campaign-manager/references/link-plan.md) and [naming/source register](plugins/marketing-performance/skills/campaign-manager/references/utm-conventions.md) describe the handoff and limits.

## Google Analytics 4 (GA4) & Firebase funnel analysis

Use `$google-analytics-analyst` (Claude: `/marketing-performance:google-analytics-analyst`) to connect to a Google Analytics 4 / Firebase Analytics property via a read-only GCP Service Account, discover the linked GA4 Property ID and measurement streams, query the GA4 Data API (`v1beta`), reconcile ad-platform outbound clicks against GA4 sessions/new users, and diagnose post-click product activation and checkout drop-offs.

```sh
GA4_TOOL="$PWD/plugins/marketing-performance/skills/google-analytics-analyst/scripts/ga4_report.py"
python3 "$GA4_TOOL" discover --project my-gcp-project --dry-run
python3 "$GA4_TOOL" preset --property 521389584 --preset campaigns --start-date 7daysAgo --end-date today --dry-run
python3 "$GA4_TOOL" preset --property 521389584 --preset funnel --campaign my_utm_campaign --start-date 2026-10-16 --end-date today --dry-run
```

See the [GA4 setup and service-account guide](plugins/marketing-performance/skills/google-analytics-analyst/references/setup-and-auth.md), [metrics and funnel formulas](plugins/marketing-performance/skills/google-analytics-analyst/references/metrics-and-dimensions.md) and [diagnostic playbook](plugins/marketing-performance/skills/google-analytics-analyst/references/diagnostic-playbook.md).

## Production tools

Planning needs no renderer, account, API key or paid service. Project validation uses Python 3.9+; the bundled composer uses Node 20+. The external HyperFrames CLI has separate version requirements (Node 22+ in the reference snapshot reviewed on 2026-10-15). HyperFrames is the external default preview/render runtime. FFmpeg/FFprobe are needed for audio conversion and encoded-file checks. Playwright plus a Chromium browser is optional for the visual probe. ElevenLabs is one optional TTS adapter; supplied audio/alignment works without it.

### Use HyperFrames skills where they help

The [HyperFrames capability map](plugins/marketing-creative/skills/motion-video-producer/references/hyperframes-routing.md) reviews all **21 published upstream skills** and routes them into our workflow. Art direction can use creative composition guidance and registry discovery; composition can use animation/Three.js/Lottie adapters and keyframe diagnostics; finishing can use source-aware media treatments, placed-track audio tools and visual regression checks. Product captures, talking-head overlays, captions, music-led promos and Figma imports are conditional workflows.

`motion-video-producer` remains the orchestrator. Use the relevant installed skills or an available reference checkout, then check actual runtime/dependency availability. This plugin does not bundle or automatically install the upstream tools. Existing briefs, selected concepts, four-ratio requirements and paid-generation approval boundaries remain authoritative; only load capabilities the current stage needs. The map includes inspected source links, useful first reads and handoff limitations.

### API keys and local configuration

Keep optional credentials outside this repository, in **`~/.config/marketing-creative/.env`** or your preferred secret manager. The bundled tools read environment variables; they **do not automatically load `.env` files**.

| Credential | Used by | Required when |
| --- | --- | --- |
| `ELEVENLABS_API_KEY` | `motion-voice/scripts/voice.py`; the `elevenlabs` CLI used by Video Studio | Generating narration or a replacement phrase. Video Studio's CLI can instead use the key stored by `elevenlabs auth login` in the OS keychain |
| `GEMINI_API_KEY` | Gemini image, Veo and Omni helpers | Image generation/batches or explicitly approved video generation and job retrieval |
| `GOOGLE_APPLICATION_CREDENTIALS` | `google-analytics-analyst/scripts/ga4_report.py` | Live GA4 Data API queries using a GCP Service Account JSON key |

No API key is required for text-only briefs/ideation, scripts, local board splitting, supplied audio/alignment, pause trimming, supplied replacement audio, composition, or local QA. Gemini image generation requires its key and API project access. Other external image/media connectors and HyperFrames manage their own authentication; this package does not currently read `FAL_KEY`, OpenAI keys, or HyperFrames credentials directly.

Create the local file, then edit it with your editor:

```sh
mkdir -p "$HOME/.config/marketing-creative"
chmod 700 "$HOME/.config/marketing-creative"
touch "$HOME/.config/marketing-creative/.env"
chmod 600 "$HOME/.config/marketing-creative/.env"
```

Its contents use shell assignment syntax (replace the example value locally):

```sh
ELEVENLABS_API_KEY='your-elevenlabs-api-key'
GEMINI_API_KEY='your-gemini-api-key'
```

Export it in the **same shell that invokes the helper**, without printing its contents:

```sh
set -a
. "$HOME/.config/marketing-creative/.env"
set +a
python3 "$SUITE/motion-voice/scripts/voice.py" generate /path/to/video-project --config /path/to/voice-config.json --dry-run
```

Set `SUITE` to the installed skills directory (or the checkout path shown below). The dry-run makes no API call. Omit `--dry-run` only when ready to generate. For agent-run commands, have the agent load the local file in the helper's shell; a desktop app launched separately may not inherit your terminal's environment.

`voice-config.json` contains nonsecret voice/model IDs, language, voice settings and an optional seed; it does not contain the API key. Never place credentials in skill files, project JSON, prompts, commits, or release archives. Repository `.env` files are also ignored as a precaution.

Get the Gemini key from [Google AI Studio](https://aistudio.google.com/apikey), using the intended API project and billing/model access. A Gemini consumer subscription is separate from API credentials and quota. Store the key only in the external `.env` or a secret manager, then use the explicit shell export above before calling the image helper. It accepts `GEMINI_API_KEY`; `GOOGLE_API_KEY` is not an implicit fallback.

### Marketing images: board first, selected finals second

The default is **Nano Banana 2.1 (`gemini-nano-banana-2.1`)**, verified against Google's [model documentation](https://ai.google.dev/gemini-api/docs/models/gemini-nano-banana-2.1) on 2026-10-15. Use `--model` for a deliberate alternate; the helper never silently switches models.

Image helpers need Python 3.10+ and Pillow (no Google SDK). Install in a separate environment:

```sh
SUITE="$PWD/plugins/marketing-images/skills"
python3 -m venv /path/to/image-tools-env
/path/to/image-tools-env/bin/python -m pip install -r "$SUITE/marketing-image-producer/scripts/requirements.txt"
PYTHON=/path/to/image-tools-env/bin/python
IMG_TOOL="$SUITE/marketing-image-producer/scripts/gemini_images.py"
SPLIT_TOOL="$SUITE/marketing-image-board/scripts/split_board.py"
```

Copy the [image plan example](plugins/marketing-images/skills/marketing-image-board/assets/image-plan.example.json) into your work directory. Its nine-cell square layout is only an example: choose the concept count for the brief and set any supported sheet ratio/rows/columns, or omit `grid` for automatic packing. A partially occupied last row is allowed; unused cells stay blank and are not cropped. Each concept has a stable ID and a distinct prompt. Use the same saved plan for generation and splitting.

References are optional. Use `references: []` or omit reference fields for brief-only generation. For one or more inputs, use `"references": [{"path": "product.png", "role": "product"}, {"path": "look.png", "role": "style"}]`, with paths relative to the plan. The example's older single `reference` string remains supported; use either field. Repeated `--reference /path/to/image.png` flags override the plan's references. Up to fourteen reference images are supported per request, including a selected tile. Image plans contain no credentials.

Image generation supports **1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9, 1:4, 4:1, 1:8 and 8:1** with the default model, as listed in Google's [image-generation guide](https://ai.google.dev/gemini-api/docs/image-generation). The sheet ratio and each final asset's ratio are separate settings. The splitter reads the same resolved grid as generation; each equal-grid crop inherits the cell shape, and selected finals are recomposed at their intended ratios.

```sh
# One billable generation request for the whole board, whatever its tile count.
"$PYTHON" "$IMG_TOOL" board image-plan.json --out /path/to/work/board-v1 --dry-run
"$PYTHON" "$IMG_TOOL" board image-plan.json --out /path/to/work/board-v1

# Use the actual returned image filename from assets.json.
"$PYTHON" "$SPLIT_TOOL" /path/to/work/board-v1/board.png --plan image-plan.json --out /path/to/work/tiles-v1

# Regenerate only selected designs as separate higher-resolution assets.
"$PYTHON" "$IMG_TOOL" batch-submit image-plan.json --select demo objection action --tiles /path/to/work/tiles-v1 --size 4K --out /path/to/work/finals-v1 --dry-run
"$PYTHON" "$IMG_TOOL" batch-submit image-plan.json --select demo objection action --tiles /path/to/work/tiles-v1 --size 4K --out /path/to/work/finals-v1
"$PYTHON" "$IMG_TOOL" batch-status /path/to/work/finals-v1
"$PYTHON" "$IMG_TOOL" batch-download /path/to/work/finals-v1
```

Run actual generation only within your intended spend. The example assumes the environment was exported in this shell. Use a fresh run directory for every submission; state is saved before the API call. Status/download resume the existing job without resubmitting, including interrupted downloads with matching existing image hashes. Unexpected ratios are preserved and flagged for review. For an immediate single final, use `image ... --select demo`; cancellation uses `batch-cancel JOB_DIR`.

The board command makes one `generateContent` call for all concepts. More tiles leave fewer pixels per concept; for example, a 2K square 3×3 board gives approximately 682-pixel tiles. Splitting is local and does not create full-resolution assets. Inspect cell boundaries and spelling; use measured crop boxes if the model did not follow the grid. Selected finals use any supplied original references plus their tile and are regenerated individually, not merely upscaled. Direct standalone and batch generation also work from a brief without reference images.

Batch uses the actual asynchronous Gemini Batch API, with automatic inline/JSONL transport. Google currently documents [50% of equivalent standard inference cost and a target turnaround up to 24 hours](https://ai.google.dev/gemini-api/docs/batch-api). Concurrent standard calls do not receive that discount. Board savings depend on resolution and input/output tokens; they are not a guaranteed ninefold reduction. Batch changes cost/latency, while full-resolution regeneration is the quality step.

See the [image workflow](plugins/marketing-images/skills/marketing-image-producer/references/image-workflow.md), [board guidance](plugins/marketing-images/skills/marketing-image-board/references/board-workflow.md) and [API source register](plugins/marketing-images/skills/marketing-image-producer/references/gemini-api.md) for plan fields, errors, output manifests and model/API verification.

### Optional Veo video generation

`marketing-veo-video` is opt-in and requires explicit approval for the exact paid request. General production authorization does not enable it. Prepare a config from the [Veo example](plugins/marketing-creative/skills/marketing-veo-video/assets/veo.example.json), verify current pricing, update its `costEstimate`, and present the prompt/media, model, mode, duration, resolution and estimate before submission.

```sh
VEO_TOOL="$SUITE/marketing-veo-video/scripts/veo_video.py"
"$PYTHON" "$VEO_TOOL" submit veo.json --out /path/to/work/veo-v1 --dry-run
# Only after explicit approval of the current request:
"$PYTHON" "$VEO_TOOL" submit veo.json --out /path/to/work/veo-v1 --approve-request SHA_FROM_DRY_RUN --approval-note 'User approved this request in chat'
"$PYTHON" "$VEO_TOOL" status /path/to/work/veo-v1
"$PYTHON" "$VEO_TOOL" download /path/to/work/veo-v1
```

Use the same exported `GEMINI_API_KEY` and Python environment described above; FFprobe verifies downloaded media. The helper supports text, image animation, first/last frames, asset references and extension of previous Veo footage, with model-specific constraints. Read the [capability register](plugins/marketing-creative/skills/marketing-veo-video/references/capabilities.md) and [workflow](plugins/marketing-creative/skills/marketing-veo-video/references/workflow.md). A quote is an estimate rather than a billing cap. Changed requests need matching approval; timeouts never trigger automatic paid retries. Status/download reuse saved jobs, and local files retain actual dimensions, duration, FPS, audio and hashes for review.

Provider footage can be a standalone asset or an input to the existing motion-video-producer. Veo natively generates 16:9 or 9:16; final square/portrait-feed delivery is composed and reviewed separately. No live video generation is required for tests or package validation.

### Optional Omni Flash video generation and editing

`marketing-omni-video` has the same opt-in approval gate and exported `GEMINI_API_KEY`. The default model is `gemini-omni-1.1-flash`. Start with the [Omni example](plugins/marketing-creative/skills/marketing-omni-video/assets/omni.example.json), replace its fictional content and illustrative quote, then prepare the exact request for approval:

```sh
OMNI_TOOL="$SUITE/marketing-omni-video/scripts/omni_video.py"
"$PYTHON" "$OMNI_TOOL" submit omni.json --out /path/to/work/omni-v1 --dry-run
# Only after explicit approval of this request and current estimate:
"$PYTHON" "$OMNI_TOOL" submit omni.json --out /path/to/work/omni-v1 --approve-request SHA_FROM_DRY_RUN --approval-note 'User approved this request in chat'
"$PYTHON" "$OMNI_TOOL" status /path/to/work/omni-v1
"$PYTHON" "$OMNI_TOOL" download /path/to/work/omni-v1
```

The [Omni capabilities](plugins/marketing-creative/skills/marketing-omni-video/references/capabilities.md) and [workflow](plugins/marketing-creative/skills/marketing-omni-video/references/workflow.md) cover text/image generation, first/last frames, loops, image/video references, uploaded-video edits, previous-interaction edits, tail extensions, upscaled 1080p/4k, inline/URI delivery, background jobs and SSE. Supply local `media` entries or use `file-upload` and `file-status` for larger sources. Explicit media-role bindings distinguish literal first/last frames, appearance references and a source video.

Uploaded edit/extension sources are limited to ten seconds; likeness reference videos to three seconds each. Generated multi-turn extensions can target a combined forty seconds. Standalone audio references and voice editing are unsupported; describe generated sound in the prompt, or use the suite's voice/audio workflow. Stored interactions support later edits; `store=false` disables later retrieval/chaining. Each edit, extension or upscale is a new paid request. The helper preserves received bytes/creation URIs and never automatically regenerates on interruption. Cancellation is available for running background Omni requests when asked, without a refund guarantee.

For later conversational changes, the Python helper resumes the chosen run's stored video context. Prepare a revision config with a new `id`, follow-up `prompt` and current `costEstimate`; omitted model, ratio, resolution and edit duration inherit from that run:

```sh
"$PYTHON" "$OMNI_TOOL" history /path/to/work/omni-v1
"$PYTHON" "$OMNI_TOOL" continue /path/to/work/omni-v1 revision.json --out /path/to/work/omni-v2 --dry-run
# After explicit approval of this revision:
"$PYTHON" "$OMNI_TOOL" continue /path/to/work/omni-v1 revision.json --out /path/to/work/omni-v2 --approve-request SHA_FROM_DRY_RUN --approval-note 'User approved this revision in chat'
"$PYTHON" "$OMNI_TOOL" download /path/to/work/omni-v2
"$PYTHON" "$OMNI_TOOL" history /path/to/work/omni-v2
```

Record the selected run path in project/session notes and continue from v2 for the next edit. Parent runs and output files remain intact; an earlier run can start a deliberate branch. History is local and works after a Python/chat restart. Provider context must still be stored and available; expired/deleted context or `store=false` cannot be resumed conversationally. Pending/unknown calls use existing status/download recovery first. See the [conversation workflow](plugins/marketing-creative/skills/marketing-omni-video/references/workflow.md) for the minimal revision config and limits.

### Assemble images, clips and authored scenes

`motion-video-producer` remains the orchestrator for the finished video. It chooses/reuses sources, coordinates optional approved generation, registers assets, owns sequencing and timing, then delegates composition and QA. General production authorization keeps Veo/Omni off until their particular paid request is approved.

The [local importer](plugins/marketing-creative/skills/motion-video-producer/scripts/assets.py) copies selected media/resources into a project, verifies generated hashes and metadata, preserves provider/request provenance and backs up the manifest:

```sh
ASSET_TOOL="$SUITE/motion-video-producer/scripts/assets.py"
"$PYTHON" "$ASSET_TOOL" /path/to/project --file /path/to/omni-v1/desk-detail-1.mp4 --id opening --provider-manifest /path/to/omni-v1/assets.json --generated-id desk-detail --audio-policy mute --dry-run
"$PYTHON" "$ASSET_TOOL" /path/to/project --file /path/to/omni-v1/desk-detail-1.mp4 --id opening --provider-manifest /path/to/omni-v1/assets.json --generated-id desk-detail --audio-policy mute
```

Use actual returned filenames and new asset IDs for revisions. The importer also accepts supplied images, video/audio, and local GLB/HTML/JS/CSS/font resources. Images/footage use their storyboard modes; Three.js scenes, HTML components, layered overlays and audio mixes use a project-owned custom generator in the same timeline. The bundled generator is a construction example and does not render arbitrary Three.js scenes. Read [asset assembly](plugins/marketing-creative/skills/motion-video-producer/references/asset-assembly.md) for source windows, sound policy, custom runtime adapters, four-ratio framing and final verification. Imports remain unreviewed until actual inspection; changing the manifest invalidates older timing/build/export fingerprints.

The following runs an **original fictional construction example**, not a ready-made ad. Outputs stay outside the repository:

```sh
SUITE="$PWD/plugins/marketing-creative/skills"
python3 "$SUITE/motion-video-producer/scripts/project.py" init /tmp/video-example --id demo --ratios 16:9 9:16 4:5 1:1 --duration 8
node "$SUITE/motion-composer/scripts/compose.mjs" /tmp/video-example --gsap /path/to/local/gsap.min.js
python3 "$SUITE/motion-video-qa/scripts/check.py" /tmp/video-example
```

The generator includes type, illustrative UI, counter, collage and character-stage examples, plus supplied image and footage modes. Custom generators can register custom visual modes. Narration anchors preserve Unicode and reject missing/ambiguous matches. Project/input fingerprints detect stale timing, assets and builds; manually edited output is preserved until reconciled.

Read the [project contract](plugins/marketing-creative/skills/motion-video-producer/references/project-contract.md), [placement profiles](plugins/marketing-creative/skills/motion-video-producer/references/placements.md), [audio workflow](plugins/marketing-creative/skills/motion-voice/references/audio-workflow.md) and [QA procedure](plugins/marketing-creative/skills/motion-video-qa/references/checks.md) for commands and limitations.

Canvas presets are 1920×1080, 1080×1920, 1080×1350 and 1080×1080. They are not universal ad-upload specifications. Select actual placements, verify current limits/safe areas, and adapt layouts; do not simply crop a landscape master. No platform-wide 179-second rule is imposed.

## Validate and package

```sh
# Activate the image-tools environment above to run all image tests.
. /path/to/image-tools-env/bin/activate
python3 -m pip install -r plugins/marketing-images/skills/marketing-image-producer/scripts/requirements.txt
python3 -m unittest discover -s tests -v
python3 scripts/validate_package.py
claude plugin validate ./plugins/marketing-creative
claude plugin validate ./plugins/marketing-images
claude plugin validate ./plugins/marketing-performance
claude plugin validate ./plugins/video-studio
claude plugin validate ./.claude-plugin/marketplace.json
agy plugin validate ./plugins/marketing-creative
agy plugin validate ./plugins/marketing-images
agy plugin validate ./plugins/marketing-performance
agy plugin validate ./plugins/video-studio
python3 scripts/build_plugin.py --output /tmp/marketing-creative-plugin.zip
python3 scripts/build_plugin.py --plugin marketing-images --output /tmp/marketing-images-plugin.zip
python3 scripts/build_plugin.py --plugin marketing-performance --output /tmp/marketing-performance-plugin.zip
python3 scripts/build_plugin.py --plugin video-studio --output /tmp/video-studio-plugin.zip
```

The deterministic ZIP includes only manifests, skill instructions/references, approved scripts/example resources and upstream notices. It excludes samples, local documents, generated video/audio, dependencies and credentials. samples/ and local-docs/ stay local and ignored. Tests do not call paid APIs.

[Behavioral evaluation scenarios](docs/skill-evaluation.md) complement executable tests. Package checks do not establish installation, model behavior, rendered quality or advertising performance. Machine QA explicitly distinguishes source checks from browser inspection, framework checks, listening and actual exports.

## Repository workflow

See [AGENTS.md](AGENTS.md) for contributor guidance, validation, credential handling and incremental commits using the commit skill.

### Automated releases

The public release line starts at `v0.1.0`. Every push to `main` with new commits runs offline Python and Node tests and package validation before semantic-release publishes a GitHub release. Pull requests run validation only. Both jobs use the standard GitHub-hosted `ubuntu-latest` runner, which is [free for public repositories](https://docs.github.com/en/actions/reference/runners/github-hosted-runners). Python and Node are configured by setup actions. FFmpeg enables the optional local media-conversion regression.

Commit messages determine the highest version bump since the last tag: `feat: ...` produces a minor release, `feat!: ...` or a `BREAKING CHANGE:` footer produces a major release, and all other changes produce a patch release, including skill documentation and ordinary commit messages. A rerun without new commits creates no release. Keep using conventional commits so the generated release notes identify changes clearly, including skill documentation.

Releases synchronize all three client manifests (`.codex-plugin/plugin.json`, `.claude-plugin/plugin.json` and `plugin.json`) for each plugin and the private release-tooling package/lockfile, update `CHANGELOG.md`, and commit those files with `[skip ci]` before tagging. This keeps marketplace/Git installations for Codex, Claude Code and Google Antigravity and the attached `marketing-creative-plugin.zip` and `marketing-performance-plugin.zip` at the same version. The ZIP contains the complete allowlisted skill tree and notices, built outside the repository. Nothing is published to npm.

The workflow uses GitHub's automatic `GITHUB_TOKEN` with `contents: write`; no npm token or manually configured release secret is required. If branch rules later prevent release commits or tags, allow an appropriate GitHub App to perform those actions before expecting releases to succeed. Release runs are serialized and in-progress runs are not cancelled. The workflow also supports manual dispatch to retry a failed run; inspect any existing tag/release first if publication was interrupted.

For local release-tooling checks, use Node 24.15+ and run `npm ci` then `npm test`. An authenticated `npm run release -- --dry-run --no-ci` previews the next version and notes, but skips version updates, ZIP preparation, commits, tags and publication. Do not run the real release command locally; push to `main` to use the validated workflow.

Configuration follows the official [semantic-release GitHub Actions recipe](https://semantic-release.org/recipes/ci-configurations/github-actions/), [commit analyzer rules](https://github.com/semantic-release/commit-analyzer#release-rules) and [Git release-asset plugin](https://github.com/semantic-release/git), reviewed on 2026-10-15. Node requirements were also checked against the pinned npm packages' engine metadata.

## Attribution

Visual direction is adapted from [Bang Motion](https://github.com/bangtutorial/bang-motion); timing/revision/verification ideas from [Hyperframe Pro](https://github.com/buildwithhanif/hyperframe-pro). Their MIT notices are retained in third-party/. See the [adaptation register](plugins/marketing-creative/skills/motion-video-producer/references/sources.md). Upstream gallery media and private sample assets are not bundled.
