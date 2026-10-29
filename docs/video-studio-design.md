# Video Studio plugin design

Status: explainer path (v1) and cinematic footage path (v2) implemented in
`plugins/video-studio/` (2026-10-27). All earlier open questions are resolved below.

`video-studio` is a new skill plugin, designed from scratch and independent of
the existing Marketing Creative skills. It covers cinematic films, explainers,
2D/3D animation, UGC/talking-head ads, product demos and music videos.

## Implementation status (2026-10-27)

| Area | State |
| --- | --- |
| `studio-producer`, `director`, `scriptwriter`, `voice-director`, `shot-designer`, `motion-designer`, `editor`, `qc-reviewer` | Implemented for the explainer recipe (v1), with offline tests |
| `reference-analyst`, `continuity-bible`, `keyframe-generator`, `ai-video-generator`, `sound-designer`; editor footage assembly; qc dailies | Implemented for the cinematic recipe (v2), with offline tests and mocked providers |
| Multi-shot takes, cut-detection splitting, single-shot retakes | Implemented; takes whose detected cuts disagree with the plan stop at `needs-split` |
| Higgsfield integration | Helpers prepare, fingerprint and record requests; the agent calls the MCP. Model limits and media roles not verified against `models_explore` (not exposed in the build session) |
| Subject mattes (SAM 2.1 / BiRefNet) for text behind the subject | Not built yet; the composer keeps type beside the subject |
| Graphic shots inside films (titles over footage) | Not built yet; footage assembly handles camera shots only |
| UGC and music-video recipes | Not built yet |

Contracts are JSON (not YAML as first sketched) so every helper stays standard-library only; field references live in `studio-producer/references/project-contract.md`.

## Design principles

1. **Skills follow production stages, not genres.** Genres reuse the same
   crafts in different proportions. Each genre is a *recipe* (a reference file)
   that the producer uses to choose skills, defaults and take sizes.
2. **Direction before generation.** Concept, beats, acting baselines and
   camera plan are locked before any paid media is generated. A weak idea
   cannot be rescued by better images.
3. **The agent proposes, the user decides.** The director drafts concrete
   options; the user picks and edits; the edited version becomes the
   direction lock.
4. **Audio first.** Voice and word-level timestamps come before video
   generation. They set shot durations and kinetic-text cues.
5. **Structured contracts, not prose hand-offs.** Skills communicate through
   versioned project files with stable IDs.
6. **Providers are references, not skills.** Provider APIs change faster than
   craft. Provider knowledge lives in per-provider reference files.
7. **Paid calls are explicit.** Cost estimates, approvals, submission identity
   and recovery state are recorded; uncertain submissions are never resubmitted
   automatically.

## Craft lessons from the reference set

Drawn from a local reference set: one analysed vertical tutorial video, a
directing-tips note and five long-form video-generation prompts. The set is not
committed. We adopt the *techniques*; the reference's palette, typography,
camcorder aesthetic and presenter persona are deliberately not copied and
become optional style-library entries at most.

| Lesson | Where it lands |
| --- | --- |
| Lock concept, script and shot prompts before generating | Pipeline order; direction lock gate |
| A boring idea can't be saved by images; know camera fundamentals | director, shot-designer |
| Give each character a baseline acting direction and speaking/movement tone | director, continuity-bible, prompt compiler |
| Hook patterns: social proof/demand, cold open mid-action, establishing reveal, POV selfie greeting | scriptwriter hook library |
| Retention: hook → promise → numbered beats/escalation → withheld reveal → payoff, cliffhanger or value-tied CTA | scriptwriter structure |
| Replace "cinematic" with movement direction + framing + specific character action | shot schema required fields; linter |
| Camera movement must have a reason | shot schema `motivation`; linter |
| Put a motivated light source in location references | continuity-bible environment masters |
| Four continuity pillars: face, outfit, location, movement | continuity-bible; qc-reviewer dailies |
| Reference roles, position locks, screen direction, generated negatives | continuity-bible; prompt compiler |
| Generate voice before video; pass voice as a reference | voice-director runs first; audio bridge |
| Avoid avatar fatigue: several setups in one location, cut every ~3–7 s, wipes mask angle changes | shot-designer coverage rules; motion-designer transitions |
| Graphics explain: one keyword per phrase synced to VO, callouts point at what is said, simplified UI cards instead of raw captures, depth layering, subject/environment contrast | motion-designer |
| Prompt anatomy: title, format, reference roles, locks, environment, timed beats (action/camera/sound/VFX), camera language, lighting, performance, physics, audio policy, negatives, final priority | ai-video-generator prompt compiler |
| Actions have anticipation, acceleration, impact, recoil, recovery | prompt compiler physics section |
| The capture device is a declared look (camera motion caused by the character's arm, period accuracy, single continuous take) | continuity-bible capture-device spec |

Subject descriptions record what continuity needs (identity, wardrobe,
proportions), not sexualised detail.

## Skill set (13)

### Pre-production

| Skill | Owns |
| --- | --- |
| `studio-producer` | Entry point and orchestration. Intake or accepts a supplied brief, picks a recipe, plans the pipeline, sets budgets, keeps project state and resumes mid-project without restarting intake. |
| `reference-analyst` | Breaks a reference video into shots, timing, hook, camera setups, graphics and audio techniques. Separates transferable technique from the reference's style. |
| `director` | Drafts 2–3 genuinely different directions (hook, beats, per-character acting baselines, camera plan, light and audio policy), self-lints them, and records the user's edited choice as the direction lock. |
| `scriptwriter` | Narration, dialogue and on-screen text with hook library, retention structure, language and delivery notes, and words-per-second timing. |
| `shot-designer` | Shot list with stable IDs, required shot fields, take grouping proposal, storyboard/animatic, and the shot linter. |
| `continuity-bible` | Reference roles, character sheets (front/side/back), environment masters with motivated light, props, position/role locks, capture-device spec, audio policy, generated negative constraints. |

### Production

| Skill | Owns |
| --- | --- |
| `voice-director` | Voice casting/design, TTS and dialogue with audio tags, speech-to-speech performance transfer, pronunciation, word timestamps. Runs before video generation. |
| `keyframe-generator` | Start/end frames and stills per shot from bible references with lighting baked in. |
| `ai-video-generator` | Prompt compiler (shots + bible + voice → provider prompt) and paid video takes. Opt-in; per-request approval. |
| `motion-designer` | Code-driven animation (Remotion/HTML/Three.js/Lottie): kinetic keywords synced to timestamps, callouts, simplified UI cards, depth layering, transitions that mask cuts. |
| `sound-designer` | Diegetic-first sound, explicit music policy, SFX and ambience, acoustics (interior/exterior, distance), time-stretch for slow-motion beats, beat-aligned music. |

### Post-production

| Skill | Owns |
| --- | --- |
| `editor` | Timeline-as-data assembly rendered with ffmpeg, pacing, captions, J/L cuts, and delivery: independently composed 16:9, 9:16, 4:5 and 1:1 variants, loudness targets, codecs, versioned exports. |
| `qc-reviewer` | Dailies mode after each take (frame extraction, four-pillar and bible checks, cut-plan verification, retake list) and final mode before release. |

Deferred to later versions, folded into the skills above for now: localisation
and dubbing (voice-director + editor), screen-recorded product demos and 3D
scenes (motion-designer).

## Pipeline

```text
reference-analyst (optional)
  → director: options → user edit → direction lock
  → scriptwriter
  → voice-director: stems + word timestamps
  → shot-designer: shots timed to audio, take grouping, lint
  → continuity-bible: references, elements, negatives
  → keyframe-generator
  → ai-video-generator: takes (approved per request)
  → qc-reviewer (dailies) → retakes
  → motion-designer
  → sound-designer
  → editor → delivery variants
  → qc-reviewer (final)
```

Supplied briefs, scripts, selected directions or existing media enter at the
matching stage; the producer does not restart intake.

## Genre recipes

| Recipe | Lead skills | Lighter use | Default take size |
| --- | --- | --- | --- |
| Cinematic / brand film (no dialogue) | continuity-bible, keyframe, ai-video, sound | motion (titles) | 2–4 shots per sequence |
| Explainer | scriptwriter, motion-designer, voice | keyframe | 1 shot |
| 2D / 3D animation | continuity-bible, motion-designer, shot-designer | ai-video | 1–2 shots |
| UGC / talking head | scriptwriter, voice, editor | keyframe | 1 shot |
| Vlog / found footage | continuity-bible (capture device), ai-video | sound | 1 continuous take |
| Product demo | motion-designer, editor, voice | — | 1 shot |
| Music video | sound (first), ai-video, editor | — | 1–2 shots on the beat grid |

## Shared contracts

All files are versioned inside the project's run directory; selected finals
stay separate from low-resolution previews.

- **`project.json`** — brief, recipe, formats, budgets, current stage. Written
  by the producer, read by every skill.
- **`direction/lock.json`** — chosen direction, hook pattern, beat outline,
  per-character acting baselines, camera plan, light and audio policy. Versioned;
  changes propagate downstream explicitly.
- **Shot registry** — one record per shot with a stable ID (`S03`). Required
  fields: `framing`, `movement` (direction), `motivation`, `action`,
  `light_source`, `sound`, `transition`, `refs`, `duration` (from timestamps),
  `take` (grouping). A regenerated clip replaces the asset, never the ID.
- **Take registry** — one record per generation request (`T03 = S04–S06`) with
  compiled prompt, references, provider/model, settings, approval fingerprint,
  job ID and status.
- **Asset registry** — every file with source, prompt, settings and status
  (draft / selected / final).
- **Cost ledger** — estimates, approvals, actual spend and recovery state per
  paid call.
- **Timeline** — the editor's output is JSON (an EDL), rendered on demand, so
  any shot can be swapped and re-rendered cheaply.

## Shot linter

Run by `shot-designer` and by `director` on its own drafts. Flags:

- vague style words without concrete instructions (`cinematic`, `epic`, …);
- missing framing, movement direction, motivation or specific action;
- unmotivated camera moves;
- screen-direction flips across a cut;
- static runs longer than ~7 s or too few distinct setups for the length;
- shots without a lit source or audio intent;
- takes exceeding the selected model's maximum duration.

## Generation mode (v1)

The shot registry is the only data model. The generation unit is a **take**
covering one or more consecutive shots.

- The prompt compiler renders a take's shots as the timed-beat anatomy above.
- Multi-shot takes are split back to shot IDs with scene-cut detection
  (ffmpeg). `qc-reviewer` checks the detected cuts against the plan; mismatches
  are flagged, never silently remapped.
- A failed shot inside a multi-shot take is retaken alone, using the
  neighbouring shots' last/first frames as start/end anchors.
- Model maximum durations are read from the provider catalog at run time.

Build order: single-shot takes and the shot registry first (enough for the
explainer path end to end); multi-shot takes and cut-detection splitting second
(cinematic path).

## Providers

Provider knowledge lives in `references/providers/` inside the skills that use
it. Model IDs, parameters and media roles below were read from tool
definitions and the upstream repository on 2026-10-26 and must be re-verified
against the provider catalog (`models_explore`, `elevenlabs models`, official
docs) when implementing; record the verification date and source.

### ElevenLabs (audio)

- Execution: the `elevenlabs` CLI (v1.7.1 observed). `--dry-run` validates
  without sending (no cost returned), `--schema` exposes parameters,
  `--format json --query` gives parseable output, credentials are stored by
  `elevenlabs auth` in the OS keychain.
- Craft reference: [elevenlabs/skills](https://github.com/elevenlabs/skills)
  for models, settings and audio tags; load the installed skill when present.

| Need | Capability |
| --- | --- |
| Narration with acting | `text-to-speech convert_with_timestamps`, `eleven_v4`, audio tags (v4: no `style`/`speed`) |
| Multi-character dialogue | `text-to-dialogue convert_with_timestamps` |
| Word timestamps | the above, or `forced-alignment create` for existing VO |
| Character voice design | `text-to-voice` |
| User performs, character speaks | `speech-to-speech` |
| Brand pronunciation | `pronunciation-dictionaries` |
| Transcripts/captions of existing footage | `speech-to-text`, `scribe_v2`, `keyterms` |
| SFX and loops | `text-to-sound-effects` (0.5–30 s, `loop`) |
| Acoustics | `audio-effects` (reverb environments, distance) |
| Beat-aligned music | `music` with composition plans, `music_v2_5` |
| Score after picture lock | video-to-music with `add_sfx`, `separate_tracks` |
| Localisation | `dubbing`, `audio-isolation` |

### Higgsfield MCP (image and video)

| Skill | Tool |
| --- | --- |
| continuity-bible | `manage_reference_elements` (character / environment / prop); prompts embed `<<<uuid>>>`; `kling3_0` also needs a `start_image` |
| keyframe-generator | `generate_image` (general default `gpt_image_2_5`; element-aware `nano_banana_pro`, `seedream_*`; `soul_*` for reusable characters) |
| ai-video-generator | `generate_video` (`seedance_2_5` general, `kling3_0` multi-shot/audio/motion transfer, `cinematic_studio_3_0`, `minimax_h3` 2K keyframes); `hf_mult_motion_control` for performance transfer from a driving video |
| editor | `reframe` (fallback only; variants are composed independently), `upscale_video` |
| cost ledger | `get_cost: true` preflight; on transport timeout keep the job ID and do not resubmit |

### Gemini API CLI (image and video)

An alternative provider added 2026-10-29 through the `gemini-api` CLI
([reference](../plugins/video-studio/skills/studio-producer/references/gemini-api.md)).
The helpers (`studio-producer/scripts/gemini.py`) derive the command from the
stored, fingerprinted request and run it themselves: `gemini-api image` for
bible references and keyframes under a USD `gemini-image` cap, and
`gemini-api video --async` for takes under per-request `gemini-video`
approval, recording the interaction id before polling with `--resume`.
Previews use the CLI's offline `--dry-run`. There are no elements, so bible
images go in as inputs, and a start keyframe binds as the first input frame.
Native video is 16:9 and 9:16 only, 3–10 s per generation; other canvases stay on
Higgsfield or a labelled, approved reframe.

### Audio bridge

ElevenLabs produces the voice stem and timestamps; the stem is uploaded to
Higgsfield (`media_upload` → PUT → `media_confirm`) and passed as the
audio/voice reference for lip-synced takes; timestamps set each take's
`duration`. Speech is not generated through Higgsfield's audio tool because it
does not return timestamps.

## Cost and approval

- **ElevenLabs: per-project cap, approved once.** The producer estimates
  credits from script characters × allowed takes plus SFX/music seconds. Calls
  run without prompting while the ledger is under the cap; each call logs its
  request, output and actual credits (`elevenlabs usage`). Warn at ~80%; a call
  that would exceed the cap stops and asks. Re-approve when the script, cast or
  language set changes the estimate.
- **Higgsfield video: per-request approval.** Show provider/model, compiled
  prompt, references and roles, duration, aspect ratio and the `get_cost`
  estimate. Approval is bound to a fingerprint of the exact request; any change
  needs re-approval. Batches can be reviewed together but each take is approved
  individually.
- **Higgsfield images: per-project image cap, approved once.** Keyframes,
  stills, background removal and outpaints are cheap individually but need
  many iterations, so per-request approval would stall look development. The
  producer estimates the cap from shots × keyframes per shot × allowed
  variants, using `get_cost` for each model. Each batch logs its count,
  estimate and actual credits; warn at ~80%; stop and ask before exceeding.
  Images that feed a video take are still shown in that take's per-request
  approval.
- **Higgsfield reframe and upscale: per-request.** They process video and
  cost about as much as video generation.
- **Gemini API: the same split.** Images run under a per-project `gemini-image`
  cap in USD; every `gemini-api video` request is approved by fingerprint.
- General production permission never enables paid generation.

## Credentials and outputs

- The ElevenLabs CLI keeps its key in the OS keychain via `elevenlabs auth`;
  the README must say so. Never print or commit keys.
- Higgsfield access is via the user's connected MCP server.
- The `gemini-api` CLI reads an exported `GEMINI_API_KEY` or its own keychain
  entry (`gemini-api configure`); helpers never read or print it.
- Generated media, runs and private references stay outside the plugin source,
  in versioned run directories.

## Evaluation scenarios

| Scenario | Observable acceptance criteria |
| --- | --- |
| One-line idea, no brief | Director returns 2–3 directions differing in hook, structure or camera approach, each with acting baselines and motivated camera plan; nothing paid runs before a lock |
| Supplied script | Producer starts at voice-director; no intake interview |
| Draft shot uses "cinematic, epic" only | Linter flags it and proposes framing, movement direction, motivation and action |
| Explainer recipe | Voice and timestamps precede shots; single-shot takes; shot durations match word cues |
| Cinematic recipe, 4-shot take, model splits only 3 cuts | qc-reviewer flags the mismatch; no silent remap; single-shot retake with neighbour anchors offered |
| Character outfit drifts in shot S05 | Dailies names the pillar (outfit), the shot and a retake request using the bible reference |
| ElevenLabs call would exceed the cap | Stops, reports ledger and estimate, asks to raise the cap |
| Higgsfield prompt edited after approval | Fingerprint mismatch blocks submission until re-approved |
| Transport timeout on a paid take | Job ID kept, status checked, no automatic resubmission |
| 16:9 master, 9:16 needed | Variant composed independently; reframe offered only as a labelled fallback |
| Brief does not name a language | Producer asks once (English or Indonesian) before scripting; no translation of an existing script |
| Indonesian script with English product names | Register recorded in acting baseline; pronunciation dictionary covers the English terms |
| Existing English video needs an Indonesian version | Project branches at script; lip-synced takes queued for regeneration, non-speaking takes re-timed |
| Text-behind-subject requested, local segmentation missing | Falls back to layering without occlusion and reports the missing dependency |

## Depth layering and segmentation

Text behind the subject is a supported technique. `motion-designer` owns it;
it needs a per-frame alpha matte of the subject for each selected shot.

| Input | Tool | Why |
| --- | --- | --- |
| Video shot (any subject) | **SAM 2.1**, run locally: point or box prompt on one frame, mask carried through the shot | Free, works for people, products and characters, masks stay consistent across frames, Apache-2.0 |
| Still image / keyframe | **BiRefNet**, run locally | Free, high-quality edges including hair, MIT |
| Local models unavailable | Higgsfield `remove_background` on stills only, under the image cap | Paid fallback; no per-frame video matting |

- Mattes are generated only for **selected** takes, after dailies QC, and
  stored as assets keyed by shot ID (`S03.matte`), separate from the colour
  footage.
- A helper script wraps both models with a dry run, a device choice
  (Apple Silicon MPS, CUDA or CPU) and a preview contact sheet. Python
  dependencies are optional extras; skills fall back to front/back layering
  without occlusion when they are missing, and say so.
- `qc-reviewer` checks mattes for edge flicker, missing limbs or hair, and
  frames where the mask is lost.
- Not chosen: Robust Video Matting (GPL-3.0, people only) and MediaPipe
  selfie segmentation (rough edges; acceptable for previews only).
- Model licences, sizes and Apple Silicon support must be re-verified when
  implementing.

## Languages

English and Indonesian are both first-class. The language for a video is
chosen when the user asks to produce it; the producer asks once if the brief
does not say.

- `project.json` records `language` (`en` or `id`). The direction lock stays
  language-neutral (beats, acting, camera); language starts at the script.
- **Write natively, never translate.** `scriptwriter` keeps separate hook
  libraries, CTA patterns and examples for each language.
- **Indonesian register is an explicit choice:** casual Jakarta (`gua/lo`),
  friendly (`aku/kamu`) or formal (`saya/Anda`), with code-switching rules for
  English product and tech terms. It belongs to each character's acting
  baseline.
- **Timing differs.** Words-per-second defaults are set per language (Indonesian
  words are longer, so fewer fit in each second), and are always replaced by
  real word timestamps after voicing.
- **Voice:** `eleven_v4` with `language_code` set; pronunciation dictionaries
  cover English brand terms spoken in Indonesian; Scribe `keyterms` cover
  both languages.
- **On-screen text:** kinetic keywords, captions and UI cards follow the
  script language; caption line length and line breaks are set per language.
- **Making the other language later** branches the project at the script.
  New voice, timestamps and shot durations follow. Takes without visible
  speech can be reused if they are re-timed; lip-synced takes must be
  regenerated in the new language.

## Repository and packaging

`video-studio` is a new plugin directory inside this repository,
`plugins/video-studio/`, alongside the existing plugins and packaged the same
way. Adding it touches:

- `plugins/video-studio/.codex-plugin/plugin.json`,
  `.claude-plugin/plugin.json` and `plugin.json` (Antigravity), with matching
  metadata and version;
- `scripts/validate_package.py` (`PLUGINS` allowlist) and
  `scripts/build_plugin.py --plugin video-studio`;
- `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json` and
  `.agents/plugins.json`;
- release wiring (`release.config.mjs`, `scripts/prepare_release.py`) and the
  validate workflow;
- tests and the README.

Skills are created with the `skill-creator` skill and validated as the
repository guidance describes.
