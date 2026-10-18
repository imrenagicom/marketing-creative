# Suite validation

Implementation validation for the 0.2.0 skill suite:

- Nine skill entry points passed the skill-creator structural validator.
- Dual manifests, marketplace and explicit package allowlist passed repository validation; both Claude plugin validations passed.
- Two independently built ZIPs were byte-identical and included 49 approved files, including both upstream MIT notices. Samples, local documents, generated media and dependencies were excluded.
- Twenty-four executable regressions passed: four canvas builds, variant-specific layouts, Unicode/ambiguous cues, stale inputs/assets, backed-up trim/replacement including boundary edits and accented-language spacing, custom/image/footage contracts, encoded metadata/audio requirements, and symlink refusal for output/package paths.
- Four actual eight-second H.264 MP4s were rendered at 30 FPS through HyperFrames and passed export fingerprint, dimensions, duration and codec verification.
- Browser inspection sampled 17 frames per canvas (68 total) and checked important boxes, overflow and repeat-seek pixels. Actual midpoint contact-sheet frames were reviewed for all five construction primitives in all four ratios.
- HyperFrames 0.8.158 passed runtime, layout and contrast checks in all four canvases. Its static lint reported six nonblocking timeline-organization warnings per compact five-beat construction example. These examples are architectural specimens; larger productions should use coherent sub-compositions.

Tests use disposable projects and synthetic/fictional content. They do not establish advertising performance, actual platform placement acceptance, model compliance on every brief, or inaudible joins in real narration. Paid TTS/provider calls were not exercised. Current placement limits and safe-area previews remain explicit production-time checks.

Run the reproducible local regressions and packaging commands in README.md. Browser/framework/export smoke tests additionally need a local GSAP file, Playwright/Chromium, HyperFrames and FFmpeg. Generated smoke artifacts are intentionally outside the repository.

## Image suite 0.3.0

Validated on 2026-10-15:

- The two new image skills passed skill-creator structural validation; all eleven skills passed the repository package checks. Both Claude manifest validations passed.
- Fifty-three offline regressions passed: twenty-four existing production tests and twenty-nine image tests. Image coverage includes arbitrary concept counts, automatic/explicit rectangular packing, partial rows, optional/multiple/CLI references, selected-tile indexing, extended image ratios, inline/JSONL batch contracts, upload headers, keyed/ordered results, partial failures, interrupted collection, ratio warnings, alpha preservation, exact crop geometry, payload bounds and unknown submission state.
- Independent forward-testing reproduced three recovery/fidelity issues; narrow fixes and regression tests now preserve unexpected-ratio output, recover interrupted downloads and retain transparent crop pixels.
- Two independently built ZIPs were byte-identical and included sixty approved files. Generated images, Python environments and credentials remain excluded.

No live Gemini generation, upload or batch submission was performed. Mocked responses establish local handling and documented request contracts; real API access, model grid adherence, product fidelity, copy accuracy and final visual quality still require a configured project and an authorized live run. This update did not rerun the historical video rendering smoke tests above.

## Opt-in Veo increment 0.4.0

Validated on 2026-10-15: 66 offline tests passed, including thirteen new generated-video regressions. Coverage includes the request-bound approval gate, changed reference fingerprints, Veo generation modes and local constraints, extension provenance/runtime, one-shot status, unknown submissions, secret-safe download redirects, filtered outputs and recovery after FFprobe failure. A synthetic local H.264 fixture was decoded and measured; no provider generation was performed.

Skill structural validation, both Claude manifest validations, the repository allowlist and a 67-file ZIP build passed. Provider access, real REST responses, model quality and regional availability remain unverified by the offline checks.

## Opt-in Omni increment 0.5.0

Validated on 2026-10-15: 79 offline regressions passed. New coverage exercises Omni source/reference bindings, first/last frames and loops, prior stored turns, uploaded edit/extension limits, upscale duration, unsupported controls, background cancellation, step-based SSE, interrupted stream identity, creation-URI preservation, unknown upload state and local recovery after provider file expiry. Package validation enforces explicit-only invocation for both paid-video skills; a 73-file archive and both Claude manifest checks passed.

Independent offline forward-testing covered both skills and reproduced the temporary-URI recovery issue, which now has a regression test. No live generation, uploads, cancellation or remote status/download calls were performed. Real provider compatibility and visual/audio output quality remain production-time checks.

## Mixed-media orchestration increment 0.6.0

Validated on 2026-10-15: 90 offline tests passed. Eleven new assembly tests cover import dry-runs, immutable source copying, provider hash/dimension/provenance checks, manifest backups, symlink refusal, measured audio, sound-policy wiring, custom-generator resource fingerprints and ordinary image/footage/overlay compositions in all four ratios. The importer preserves generated output findings and pending review, and new imports invalidate earlier timing/build fingerprints. Independent forward-testing found two request-provenance gaps; regression tests now preserve manifest-only request identity, reject conflicting state/approval identities and avoid attributing unbound sibling state.

The suite now has thirteen skill entry points and 75 distributed files. Both new provider skills remain explicit-only; motion-video-producer owns source selection and assembly, including custom Three.js/HTML generators. Source/data tests do not establish actual Three.js rendering, HyperFrames media playback, listening, live video model compatibility or finished campaign quality. No paid provider calls were made.

## Conversational continuation increment 0.6.1

Validated on 2026-10-15: 99 offline tests passed. Nine new regressions cover Python continue/history commands, inherited settings and measured duration, three-turn resumption after a process restart, deliberate branches, approval bound to the parent/edit, pending/stateless/unknown rejection, unchanged parent files after timeout, mismatched parent/asset identities, cycles and external/legacy history. Dry-run/history need no key or network and write no runs. Both changed skills passed structural validation; repository/Claude manifests passed, and two 75-file archives were byte-identical.

An independent forward-test passed eleven checks using fresh Python processes and synthetic transport, including two successive edits, an earlier-version branch, inherited settings, approval rejection and unresolved-turn recovery boundaries. No live conversational generation or provider retrieval was performed. Local history and mocked chaining verify request/state handling, not server-side context availability, retention or actual edit fidelity. Existing rendering limitations above remain unchanged.

## HyperFrames routing notes 0.6.2

Reviewed all 21 published entry points from HyperFrames revision 03a9fab9a7b1c8742198bca8f475d04a51feaf5e on 2026-10-15. The packaged routing map covers every published skill and verifies each immutable source link against that checkout; its entry points match the linked Git revision. Selected deeper creative, storyboard, animation-adapter, media-treatment, audio and CLI references were also inspected. Six revised skill entry points passed structural validation, repository/Claude manifest checks passed and two 76-file archives were byte-identical. The reference CLI's Node >=22 requirement was verified separately from the bundled composer's requirements.

This increment changes guidance and packaging metadata only. No code regressions, HyperFrames runtime commands, provider calls, rendering or listening checks were repeated; it does not establish installation or improved production quality. Prior executable validation remains recorded above. Upstream code, media and workflows are referenced rather than bundled.

## Public release baseline and automation

Validated on 2026-10-15. Public versioning starts at `v0.1.0`; the historical increment numbers above describe earlier implementation checks and are retained as recorded. Both client manifests were aligned with the public tag and the new imrenagicom repository. The tag was pushed and the validated 76-file ZIP attached to its GitHub release.

All 102 offline Python regressions passed with Python 3.12, Pillow and FFmpeg available; no image tests were skipped. Three release regressions cover synchronized manifest/package/lockfile versions, unchanged locked dependencies, actual allowlisted ZIP contents, invalid versions and missing metadata. Ten Node tests cover patch/minor/major selection, ordinary and documentation commits, breaking footers and `!`, highest-bump selection, no-change reruns and inclusion of skill documentation in release notes. Tests exposed an incompatible latest changelog preset; the pinned 9.x preset passes against semantic-release's current writer. Repository validation, both Claude manifest validations, diff checks and two byte-identical archive builds passed.

The workflow validates before publishing, uses `[self-hosted, linux]` for both jobs, serializes releases and gives only the release job `contents: write`. Release preparation builds outside the repository and commits only the changelog and version metadata before tagging. CI uses the automatic GitHub token and publishes no npm package. An authenticated live dry-run and the first self-hosted Actions run still require verification after committing/pushing this setup; these offline checks do not prove runner availability or GitHub publication.

`npm ci` succeeds, but `npm audit` reports fourteen upstream development-tool advisories (twelve high, two moderate), including braces/micromatch and dependencies bundled within semantic-release's npm dependency. A compatible `npm audit fix` did not resolve them; no forced downgrade or unverified dependency override was applied. These release-tool dependencies are excluded from the distributed skill ZIP. No paid provider calls, new production renders, browser inspection or listening review were performed for this change.

## GitHub-hosted runner switch

On 2026-10-15, verified that this repository is public and that GitHub documents standard hosted runners as free and unlimited for public repositories. Both jobs now use `ubuntu-latest`. The previous self-hosted run was queued because no matching runner was available. The earlier authenticated semantic-release dry-run passed and selected `v0.1.1`; it did not create that tag or publish a release. Hosted validation and publication will be checked after this change is pushed. The local test results and dependency-audit limitations above remain applicable.

## Marketing Performance plugin split

Validated on 2026-10-16:

- Moved `marketing-brief` to the independently packaged Marketing Performance plugin; creative handoffs accept supplied briefs or optionally invoke the new owner without cross-plugin filesystem links.
- All 102 offline Python regressions passed in a Python 3.12 virtual environment with Pillow; all 10 Node release checks passed. Release fixtures verified both archive identities, synchronized versions and the absence of the moved skill from Creative.
- Four changed skill entry points passed skill-creator structural checks. Both Claude plugin manifests and the marketplace passed CLI validation.
- Both allowlisted archives built outside the repository: 73 Creative files and 5 Performance files. Local package/resource-link and diff checks passed.

No global plugin installation, live campaigns, paid provider calls, rendering or attribution collection was performed. Historical visual/provider checks above were not rerun.

## Campaign UTM workflow

Validated on 2026-10-16:

- All 116 offline Python regressions passed with Pillow installed and no skips. Fourteen new tests cover inherited/exact taxonomy values, Unicode and delimiter encoding, preserved raw queries/click IDs/fragments, existing UTM conflicts, malformed plans/URLs/macros, duplicate IDs/URLs, publication metadata, no-write dry-runs, exact input/CSV exports, retained prior revisions, duplicate JSON keys and symlink refusal.
- The Performance archive was built twice with byte-identical results, then extracted into a temporary directory. Its helper successfully validated the bundled fictional plan without the Creative plugin or external Python dependencies.
- Both Performance skill entry points passed skill-creator structural checks; both plugin resource inventories and all packaged links passed the repository validator (85 files total: 73 Creative, 12 Performance). Both final archives built outside the repository. Claude Performance/marketplace validation and diff checks passed; Creative manifest and 10 Node release checks had passed during the preceding split increment and were unchanged here.
- Behavioral scenarios were added for later-chat resumption, published-link identity, existing taxonomies, dynamic/app attribution boundaries and commit-ready records. They document expected behavior, not completed independent model evaluations.

No live campaign, redirects, analytics receipt, conversion attribution, global installation, paid generation or video rendering was tested. The helper validates individual static snapshots; published-history comparison, taxonomy choices, campaign notes and live measurement evidence remain responsibilities of the skill workflow.

## Campaign Manager rename

Validated on 2026-10-16: renamed the skill folder, frontmatter, UI name and invocation to `campaign-manager`; updated README links, the brief handoff, package inventory and archive/helper regression paths. All 116 offline Python regressions passed without skips, including standalone extracted-archive execution. Both changed skill entry points passed structural validation; package/resource checks, a Performance archive build, Claude Performance/marketplace validation and diff checks passed. This rename did not change URL generation or measurement behavior; no live attribution checks were performed.

## Marketing copywriter

Validated on 2026-10-16:

- Added `marketing-copywriter` to Marketing Performance with normal automatic discovery, channel-specific guidance for ads/social, landing pages, email and localization, and portable handoffs to the plugin's existing brief and campaign skills. Video scripting remains an optional Creative handoff.
- All 116 offline Python regressions passed in a Python 3.12 virtual environment with Pillow and no skips. Updated the expected skill inventory and release regression to verify that the copywriter entry point, UI metadata and reference ship only in the Performance archive. All 10 Node release checks passed.
- The new entry point passed skill-creator structural validation. Both Claude plugin manifests and the marketplace passed CLI validation. Repository resource/link validation passed for 88 files: 73 Creative and 15 Performance. Two Performance archives built outside the repository were byte-identical; extraction confirmed the copywriter resources and sibling handoff targets. A Creative archive also built successfully. Diff checks passed.

The added behavioral scenarios are an evaluation plan, not completed independent model evaluations. No live copy campaign, platform acceptance, native-language review, global plugin installation, paid generation, rendering or listening review was performed. These checks establish structural and distribution integrity rather than advertising performance or copy quality.

## Copywriter voice and style exploration

Validated on 2026-10-16: expanded the copywriter to produce multiple complete versions with distinct speakers, tones, structures, intended feels and selling intensity. Added a portable reference with personal experience, useful-find, practical, playful and direct-selling approaches, plus fictional examples sharing the same facts. Firsthand narration uses supplied speaker experiences; personal sharing can use a gentle or absent purchase ask when the brief permits. Updated discovery text, usage examples and behavioral scenarios.

All 116 offline Python regressions passed with Pillow and no skips. Skill-creator structural validation, package/resource-link checks, Claude Performance/marketplace validation and diff checks passed. Two 16-file Performance archives were byte-identical; extraction verified the new reference and sibling handoff resources. The release regression now checks that the voice/style reference ships, and the three release regressions passed again after incorporating the automated v0.3.0 metadata. The package inventory contains 89 files across both plugins.

The new scenarios and illustrative copy were reviewed as guidance, not executed as independent model evaluations. No live campaign, audience testing, native-language review, global installation or paid production was performed. Unchanged Node release-tooling checks were not repeated for this guidance update; their prior results remain recorded above.

## Beat planning guidance

Validated on 2026-10-16: strengthened motion-storyboard with job/hero/action choices, per-ratio zones, cue-driven handoffs and editorial review gates, retaining intentional silence and evidence-aware stylization. The changed entry point passed skill-creator structural validation; package inventory/resource links (90 files) and diff checks passed. Hyperframe Pro attribution and distributed MIT notice are retained.

This increment changes guidance only; code regressions were not repeated. Added behavioral scenarios are an evaluation plan, not completed independent model evaluations. No visual, listening, renderer, paid-provider or retention checks were performed.

## Narration loudness and pause classes

Validated on 2026-10-16 with Python 3.12, Pillow, Node and FFmpeg 8.1: all 128 offline Python regressions passed without skips. Twelve new audio regressions cover measured loudness/true peak, unchanged PCM clock/words, original backups and invalidated timing, silent/invalid/mismatched-clock rejection, no-processing/no-write dry-runs, preserved raw paid results after local failure, optional import/generation normalization, exact mixed-class trimming, preserved dramatic gaps, invalid/conflicting/Unicode/repeated anchors and stale measurement removal. Generated narration is mocked; measured audio tests use synthetic PCM and actual local FFmpeg.

motion-voice passed skill-creator structural validation; package/resource links (91 files) and diff checks passed. Loudnorm parameters and fallback behavior were checked against official FFmpeg filter documentation on the same date; the portable reference records the source. No TTS API/model/pricing change was made. New generation normalizes by default and retains a raw backup; imported recordings preserve level by default.

No paid provider requests, human listening, real-speech prosody evaluation, HyperFrames preview/render or finished stereo-mix review was performed. The numeric results establish local synthetic-source processing and state integrity, not audible seam quality or final export loudness. Behavioral scenarios remain an evaluation plan. Unchanged Node release tests were not repeated for this audio increment.

## Video workflow entry point

Validated on 2026-10-16: added normally discoverable marketing-video as the workflow/revision entry point, with motion-video-producer retaining project ownership and final delivery. It maps every Creative stage, optional Marketing Performance strategy, silent/music-led paths, downstream inputs, revision dependencies and exact-request Veo/Omni approval. Updated dual-client discovery descriptions and the explicit inventory to thirteen Creative skills (sixteen across both plugins).

The entry point and revised producer passed skill-creator checks. Repository inventory/resource links passed for 93 files. Both Claude Creative and marketplace validations passed. Two 77-file Creative archives were byte-identical; extraction verified all fourteen entry-point sibling links and independently runnable audio command help. Release regressions check the new entry point and beat/audio references in Creative and exclusion from Performance. All 128 offline Python regressions passed without skips, and all ten Node release tests passed. The preexisting aggregate skill-count assertion was updated for the added skill.

No global plugin installation, independent model forward-test, live provider request, visual/listening review or HyperFrames production render was performed. The entry-point scenarios remain an evaluation plan, and synthetic audio tests do not establish real-speech or final-mix quality.

## Campaign workspace directory and copy/asset revision structure

Validated on 2026-10-18: updated `campaign-manager`, its workspace and link-plan references, the bundled example plan, and `marketing-copywriter` handoff notes to define `<YYYY-MM-DD>-<campaign-name>` campaign directories, separate storyboard/media development (`assets/development/` with `storyboard/`, `images/`, `video/`, `audio/`) from versioned approved assets (`assets/approved/v001/`, `v002/`, ...), and separate working copy (`copy/drafts/`) from versioned approved copy revisions (`copy/approved/v001/`, `v002/`, ...).

Both changed skill entry points (`campaign-manager` and `marketing-copywriter`) passed skill-creator structural validation. Repository package and resource-link validation passed for all 93 files across both plugins, both Claude plugin manifests and the marketplace passed CLI validation, and both plugin archives built deterministically outside the repository. All 129 offline Python regressions passed with Python 3.12 and Pillow installed (0 skips), and diff checks passed. No live campaign publication, analytics collection or paid media generation was performed.

## Multi-platform campaign workspace (`meta-ads`, `instagram`, `linkedin`, `twitter`)

Validated on 2026-10-18: extended `campaign-manager` to organize paid ad and social media campaign hierarchies under `<YYYY-MM-DD>-<campaign-name>/`: `meta-ads/campaigns/<meta-campaign-slug>/adsets/<adset-slug>/ads/<ad-slug>/` alongside `instagram/posts/<post-slug>/`, `linkedin/posts/<post-slug>/`, and `twitter/posts/<post-slug>/`. Added `references/meta-ads.md` defining the 3-tier `campaign.json` (objective/goal, buying type, CBO/ABO budget limits, spend cap, bid strategy), `adset.json` (optimization goal, conversion event, ABO budget, schedule, user targeting `targeting`, and `placements`), and `ad.json` (clean `destination_url`, `utm`, serialized `url_tags`, `link_id`, and approved copy/asset revision pointers), plus `references/social-media.md` defining per-post `post.json`, caption/thread `copy/{drafts,approved/vNNN}`, and `assets/{development,approved/vNNN}` across `instagram`, `linkedin`, and `twitter`, including copying existing approved assets between `meta-ads/` and social media without regenerating or requiring `assets/development/`. Updated `scripts/build_utm.py` to emit `url_tags`, validate `meta-ads` and social media link metadata, and verify `meta-ads/campaigns/...` and `{instagram,linkedin,twitter}/posts/...` trees against root `campaign.json`.

Both changed skill entry points (`campaign-manager` and `marketing-copywriter`) passed skill-creator structural validation. Repository package and resource-link validation passed for all 95 files across both plugins (77 Creative, 18 Performance), both Claude plugin manifests and the marketplace passed CLI validation, and both plugin archives built deterministically outside the repository. All 133 offline Python regressions passed in a Python 3.12 virtual environment with Pillow installed (0 skips), and diff checks passed. No live Meta or social platform API calls, campaign launches or analytics collection were performed.
