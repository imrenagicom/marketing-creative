# Marketing Campaign Suite

Three independently installable plugins cover campaign planning, copywriting, analytics and creative production. Marketing Performance owns `marketing-brief`, `marketing-copywriter`, `campaign-manager` and `google-analytics-analyst`; Marketing Images owns `marketing-image-board` and `marketing-image-producer` for campaign images; Video Studio makes the campaign's explainers and cinematic short films with thirteen stage skills ([design](docs/video-studio-design.md)). Codex, Claude Code and Google Antigravity use the same source. Production supports **16:9, 9:16, 4:5 and 1:1** as independently composed and reviewed variants.

## One campaign, every plugin

The plugins serve one purpose: producing a marketing campaign. `campaign-manager` (marketing-performance) creates the campaign workspace, `marketing/campaigns/<YYYY-MM-DD>-<campaign-name>/`, with its brief, Meta Ads and social trees, tracking and reports. The creative plugins work inside it:

- Marketing Images plans boards and finals in an ad's or post's `assets/development/images/` and files approved images into `assets/approved/vNNN/images/`.
- Video Studio creates its project in `assets/development/video/<YYYY-MM-DD>-<slug>/`, records the link with `campaign.py link`, and after QC and the user's approval runs `campaign.py handoff` to file the deliveries into `assets/approved/vNNN/video/` with `assets.json`.
- `marketing-copywriter` writes the copy and alt text. `campaign-manager` updates revision pointers and UTMs and writes performance reports.

Every creative skill reads the campaign brief, approved claims, CTA and required ratios instead of repeating intake. None of them publishes or edits the campaign's `campaign.json`, `ad.json` or `post.json`.

## Marketing Creative was removed

The earlier Marketing Creative plugin was deprecated and then removed. Its image skills now live in Marketing Images, and Video Studio replaces its video workflow. Projects made with it stay readable in Git history up to v0.13.0. New work uses:

| Marketing Creative | Use instead |
| --- | --- |
| `marketing-video`, `motion-video-producer` | `studio-producer` (+ `editor`) |
| `creative-ideation`, `ad-video-director`, `motion-art-director` | `director`, `scriptwriter`; `marketing-image-board` for image concepts |
| `motion-storyboard` | `shot-designer` |
| `motion-voice` | `voice-director` |
| `motion-composer` | `motion-designer` |
| `motion-video-qa` | `qc-reviewer` |
| `marketing-omni-video` | `ai-video-generator --provider gemini` |
| `marketing-veo-video` | `ai-video-generator` with Gemini Omni or a Higgsfield model. Google shut down Veo 3.1 Preview in the Gemini API on 2026-10-22 ([deprecations](https://ai.google.dev/gemini-api/docs/deprecations)) |

## Skills and handoffs

| Skill | Input → output |
| --- | --- |
| `campaign-manager` (marketing-performance) | Product campaign → `<YYYY-MM-DD>-<campaign-name>` workspace, paid ad hierarchy (`meta-ads/campaigns/.../adsets/.../ads/...`), social media trees (`instagram/`, `linkedin/`, `twitter/`), timestamped performance reports (`reports/<datetime>.md`), storyboard/media development & approved copy/asset revisions, and UTM links |
| `google-analytics-analyst` (marketing-performance) | GA4 / Firebase project & campaign UTMs → GA4 Data API funnel reports, ad-click-to-session reconciliation, drop-off diagnosis and recommendations |
| `marketing-brief` (marketing-performance) | Product facts, research and goal → strategic brief, evidence, placement requirements |
| `marketing-copywriter` (marketing-performance) | Brief or draft → exact ad, landing-page, email or social copy, voice/style variants and localization |
| `marketing-image-board` (marketing-images) | Brief, concepts and optional references → one board with a chosen tile count/ratio and locally cropped previews |
| `marketing-image-producer` (marketing-images) | Brief or selected concepts/tiles, with optional references → standalone image assets or discounted asynchronous Gemini batches |

Use only the stages needed. Supplied briefs, selected ideas and recordings enter downstream; small revisions do not restart intake. Planning alone does not launch campaigns or render a video. A general explainer can bypass advertising strategy.

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

Plugins live in `plugins/marketing-images/`, `plugins/marketing-performance/` and `plugins/video-studio/`. Install any of the complete trees; each plugin contains its own required resources and host manifests for Codex (`.codex-plugin/plugin.json`), Claude Code (`.claude-plugin/plugin.json`) and Google Antigravity (`plugin.json`). Creative production accepts supplied briefs without the Performance plugin.

### Codex

```sh
codex plugin marketplace add /absolute/path/to/marketing-creative
codex plugin add marketing-images@marketing-creative
codex plugin add marketing-performance@marketing-creative
codex plugin add video-studio@marketing-creative
codex plugin list --marketplace marketing-creative --json
```

Or register `imrenagicom/marketing-creative` after the relevant release is published (`codex plugin marketplace add imrenagicom/marketing-creative`). Reload the client if needed. Invoke `$marketing-brief`, `$studio-producer`, or any skill in the tables.

### Claude Code

```sh
claude plugin marketplace add /absolute/path/to/marketing-creative
claude plugin install marketing-images@marketing-creative
claude plugin install marketing-performance@marketing-creative
claude plugin install video-studio@marketing-creative
claude plugin details marketing-performance
```

After publication, use `claude plugin marketplace add imrenagicom/marketing-creative` instead of the local path. Inside Claude Code, the equivalent commands begin with `/plugin marketplace add` and `/plugin install`. For temporary development without installation, use `claude --plugin-dir ./plugins/video-studio --plugin-dir ./plugins/marketing-performance`. Invoke `/marketing-performance:marketing-brief` or `/video-studio:studio-producer`, for example. `marketing-brief` has moved: its Claude namespace is now `marketing-performance`; its Codex and Antigravity invocation remains `marketing-brief` / `$marketing-brief`.

### Google Antigravity

From a checkout or an extracted plugin archive (`marketing-images-plugin.zip`, `marketing-performance-plugin.zip` or `video-studio-plugin.zip`):

```sh
agy plugin install /absolute/path/to/marketing-creative/plugins/marketing-images
agy plugin install /absolute/path/to/marketing-creative/plugins/marketing-performance
agy plugin install /absolute/path/to/marketing-creative/plugins/video-studio
agy plugin list --json
```

Inside an interactive Antigravity CLI session, run `/plugin install /absolute/path/to/marketing-creative/plugins/<plugin>` for each plugin (or select *Install from local directory* in the `/plugin` manager). Installed plugins are staged under `~/.gemini/config/plugins/<plugin>/` and synchronized across the Antigravity App, IDE, and CLI; restart if newly installed skills do not appear immediately. When opening the `marketing-creative` repository itself as a workspace in Antigravity, `.agents/plugins.json` automatically registers all three plugins and their 19 skills without requiring global installation.

For clients without plugin support, reference the complete skill tree from the client's instruction file, retaining all sibling skills. No global installation or client configuration is changed by this repository.

## Example requests

> Use $studio-producer to make a 30-second Indonesian explainer Reel for the ad in our launch campaign. Take the brief and required ratios from the campaign, and file the approved video back into that ad.

> Use $studio-producer to resume this video project and revise its CTA. Keep the rest of the narration and rebuild the affected canvases.

> Use $marketing-brief for our task app. Goal: users completing their first assignment. Audience: small design teams. We have real captures but no verified trial offer. Plan Meta feed, Reels, landscape and square deliverables.

> Use $marketing-copywriter with this brief to draft ad copy and a matching landing-page hero in English and Indonesian. Give me two variants that test different benefit emphases, keep the supplied offer and destination, and flag unsupported claims.

> Use $marketing-image-board with this product image and marketing brief. Show nine distinct Instagram/ad concepts in one square 3×3 board, then split the previews locally.

> Use $marketing-image-board with this brief and any attached references. Choose a useful number of concepts and a portrait or landscape sheet layout. Ensure each concept can be cropped separately.

> Use $marketing-image-producer to regenerate my three selected tiles as separate 4K assets through Gemini's discounted Batch API. Keep the original source image as the product reference.

## Marketing copy

Use `$marketing-copywriter` (Claude: `/marketing-performance:marketing-copywriter`) for exact wording or revisions from an existing brief or draft. It can prepare multiple complete versions with different voices, tones, styles and selling intensity: personal experience sharing, a friendly useful-find recommendation, a warm explanation or a direct sales pitch. Firsthand stories use the actual speaker's supplied experiences; warm copy can also work from product facts alone. It preserves supported claims and offer terms, and provides meaningful test variants or localization when requested. Copy is returned in chat unless saving is part of the task. Full timed video scripts and shot direction belong to Video Studio's `scriptwriter` and `shot-designer`; drafting copy does not publish a campaign or send email.

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

Use the next unused revision (`v001`, `v002`, ...) for changes to tracking exports, approved copy or approved assets. Existing exports and published link identities are preserved; conflicts with destination UTMs need explicit resolution. The helper preserves other query parameters/fragments, encodes values once, emits `url_tags` for Meta URL parameters, and validates `meta-ads/campaigns/` and `{instagram,linkedin,twitter}/posts/` specs against `campaign.json` when present, resolving ad set `audience_slug` references against the shared `audiences/meta-ads/` registry. Local validation does not prove redirect preservation or analytics collection; record those checks separately. The [workspace record contract](plugins/marketing-performance/skills/campaign-manager/references/workspace-records.md), [performance reporting structure](plugins/marketing-performance/skills/campaign-manager/references/reporting.md), [Meta Ads hierarchy contract](plugins/marketing-performance/skills/campaign-manager/references/meta-ads.md), [social media structure](plugins/marketing-performance/skills/campaign-manager/references/social-media.md), [account-level Meta audiences](plugins/marketing-performance/skills/campaign-manager/references/meta-audiences.md), [link schema](plugins/marketing-performance/skills/campaign-manager/references/link-plan.md) and [naming/source register](plugins/marketing-performance/skills/campaign-manager/references/utm-conventions.md) describe the handoff and limits.

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

Planning needs no renderer, account, API key or paid service. Marketing Images needs Python 3.10+ and Pillow. Video Studio's requirements are listed in its section above.

### API keys and local configuration

Keep optional credentials outside this repository, in **`~/.config/marketing-creative/.env`** or your preferred secret manager. The bundled tools read environment variables; they **do not automatically load `.env` files**.

| Credential | Used by | Required when |
| --- | --- | --- |
| `ELEVENLABS_API_KEY` | the `elevenlabs` CLI used by Video Studio | Generating narration, sound effects or music. The CLI can instead use the key stored by `elevenlabs auth login` in the OS keychain |
| `GEMINI_API_KEY` | Marketing Images' Gemini helper; the `gemini-api` CLI used by Video Studio | Image generation and batches, or explicitly approved video generation and job retrieval |
| `GOOGLE_APPLICATION_CREDENTIALS` | `google-analytics-analyst/scripts/ga4_report.py` | Live GA4 Data API queries using a GCP Service Account JSON key |

No API key is required for briefs, scripts, local board splitting, supplied audio alignment, composition or local QC. Gemini image generation requires its key and API project access. Other external image/media connectors and HyperFrames manage their own authentication; this package does not currently read `FAL_KEY`, OpenAI keys, or HyperFrames credentials directly.

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
"$PYTHON" "$IMG_TOOL" board image-plan.json --out /path/to/work/board-v1 --dry-run
```

Set `PYTHON` and `IMG_TOOL` as shown below. The dry-run makes no API call. Omit `--dry-run` only when ready to generate. For agent-run commands, have the agent load the local file in the helper's shell; a desktop app launched separately may not inherit your terminal's environment.

Plans and configs contain only nonsecret settings, never the API key. Never place credentials in skill files, project JSON, prompts, commits, or release archives. Repository `.env` files are also ignored as a precaution.

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

## Validate and package

```sh
# Activate the image-tools environment above to run all image tests.
. /path/to/image-tools-env/bin/activate
python3 -m pip install -r plugins/marketing-images/skills/marketing-image-producer/scripts/requirements.txt
python3 -m unittest discover -s tests -v
python3 scripts/validate_package.py
claude plugin validate ./plugins/marketing-images
claude plugin validate ./plugins/marketing-performance
claude plugin validate ./plugins/video-studio
claude plugin validate ./.claude-plugin/marketplace.json
agy plugin validate ./plugins/marketing-images
agy plugin validate ./plugins/marketing-performance
agy plugin validate ./plugins/video-studio
python3 scripts/build_plugin.py --plugin marketing-images --output /tmp/marketing-images-plugin.zip
python3 scripts/build_plugin.py --plugin marketing-performance --output /tmp/marketing-performance-plugin.zip
python3 scripts/build_plugin.py --plugin video-studio --output /tmp/video-studio-plugin.zip
```

The deterministic ZIP includes only manifests, skill instructions/references, approved scripts and example resources. It excludes samples, local documents, generated video/audio, dependencies and credentials. samples/ and local-docs/ stay local and ignored. Tests do not call paid APIs.

[Behavioral evaluation scenarios](docs/skill-evaluation.md) complement executable tests. Package checks do not establish installation, model behavior, rendered quality or advertising performance. Machine QC explicitly distinguishes automated checks from watching, listening and visual review.

## Repository workflow

See [AGENTS.md](AGENTS.md) for contributor guidance, validation, credential handling and incremental commits using the commit skill.

### Automated releases

The public release line starts at `v0.1.0`. Every push to `main` with new commits runs offline Python and Node tests and package validation before semantic-release publishes a GitHub release. Pull requests run validation only. Both jobs use the standard GitHub-hosted `ubuntu-latest` runner, which is [free for public repositories](https://docs.github.com/en/actions/reference/runners/github-hosted-runners). Python and Node are configured by setup actions. FFmpeg enables the optional local media-conversion regression.

Commit messages determine the highest version bump since the last tag: `feat: ...` produces a minor release, `feat!: ...` or a `BREAKING CHANGE:` footer produces a major release, and all other changes produce a patch release, including skill documentation and ordinary commit messages. A rerun without new commits creates no release. Keep using conventional commits so the generated release notes identify changes clearly, including skill documentation.

Releases synchronize all three client manifests (`.codex-plugin/plugin.json`, `.claude-plugin/plugin.json` and `plugin.json`) for each plugin and the private release-tooling package/lockfile, update `CHANGELOG.md`, and commit those files with `[skip ci]` before tagging. This keeps marketplace/Git installations for Codex, Claude Code and Google Antigravity and the attached `marketing-images-plugin.zip`, `marketing-performance-plugin.zip` and `video-studio-plugin.zip` at the same version. Each ZIP contains one plugin's complete allowlisted skill tree, built outside the repository. Nothing is published to npm.

The workflow uses GitHub's automatic `GITHUB_TOKEN` with `contents: write`; no npm token or manually configured release secret is required. If branch rules later prevent release commits or tags, allow an appropriate GitHub App to perform those actions before expecting releases to succeed. Release runs are serialized and in-progress runs are not cancelled. The workflow also supports manual dispatch to retry a failed run; inspect any existing tag/release first if publication was interrupted.

For local release-tooling checks, use Node 24.15+ and run `npm ci` then `npm test`. An authenticated `npm run release -- --dry-run --no-ci` previews the next version and notes, but skips version updates, ZIP preparation, commits, tags and publication. Do not run the real release command locally; push to `main` to use the validated workflow.

Configuration follows the official [semantic-release GitHub Actions recipe](https://semantic-release.org/recipes/ci-configurations/github-actions/), [commit analyzer rules](https://github.com/semantic-release/commit-analyzer#release-rules) and [Git release-asset plugin](https://github.com/semantic-release/git), reviewed on 2026-10-15. Node requirements were also checked against the pinned npm packages' engine metadata.
