---
name: marketing-video
description: Deprecated Marketing Creative skill for a marketing video or explainer from a brief, concept, script or existing media. For new work use studio-producer (video-studio plugin), which runs the whole pipeline inside the campaign workspace. Use this only to resume or revise an existing Marketing Creative project.
---

# Marketing Video

> **Deprecated.** Marketing Creative is being retired in favour of Video Studio and Marketing Images. For new work, use `$studio-producer` (video-studio plugin), which runs the whole pipeline inside the campaign workspace. Use this skill only to resume or revise an existing Marketing Creative project, and keep that project's files intact.

Turn the requested starting material into the requested video deliverable. First identify whether this is a new video, a revision, planning only or an export of an existing project. Reuse established decisions and artifacts; a supplied script, concept, recording or composition enters at the missing stage. An inspection or caption-only edit does not restart production.

Read [motion-video-producer](../motion-video-producer/SKILL.md) for project setup, mixed-media assembly, runtime handoff and recovery. This entry point selects the path and explains stage handoffs; the producer remains responsible for the authoritative project, source selection, requested variants and final exports. Stage routing does not imply subagents or separate chats. Load only the skill and linked references needed for the current work.

## Establish the deliverable

Recover the goal, audience, exact claims/offer/CTA, brand, language, intended length, requested ratios and available sources from the user's material. Ask only for missing decisions that materially affect the result; use stated assumptions for routine choices. A general explainer can skip campaign strategy and sales structure. Preserve exact user-mandated wording and distinguish product proof from illustrative media.

Confirm the output from the request: script/plan, editable project, finished encoded video, or a focused revision. Produce every requested 16:9, 9:16, 4:5 and/or 1:1 variant as its own composition. When ratios are unspecified, use the stated placement to choose a sensible starting format and state the assumption; do not silently promise four variants. Different narration/duration cutdowns use separate projects sharing the selected briefs/concept.

## New-video path and owners

For narrated work, the dependency chain is:

`topic/brief → selected concept → exact script + visual direction → actual voice/alignment → resolved beat plan → assets + composition → QA → encoded exports`

Art direction, asset planning and a provisional beat sheet can begin earlier. Final cues follow measured audio and source media. Silent work skips voice and uses deliberate seconds; music-led work uses the chosen track's verified beat/phrase map. Do not add narration just to satisfy the chain.

| Work needed | Skill to read/use | Handoff to the next stage |
| --- | --- | --- |
| Campaign goal, audience, offer or evidence unresolved | `$marketing-brief` in the optional Marketing Performance plugin | Strategic brief; use an existing brief or establish the necessary facts directly if that plugin is unavailable |
| Choose among creative approaches | [creative-ideation](../creative-ideation/SKILL.md) | Distinct concepts and selected creative brief; skip if the concept is already selected |
| Exact spoken/onscreen script and shot direction | [ad-video-director](../ad-video-director/SKILL.md) | Supported exact script/copy and production handoff; adapt to an explainer rather than impose sales copy |
| Brand, imagery, type and motion language | [motion-art-director](../motion-art-director/SKILL.md) | STYLE.md and visual direction appropriate to each requested ratio |
| Generate/import narration or revise a take | [motion-voice](../motion-voice/SKILL.md) | Measured WAV, word alignment and hashes; preview paid TTS, preserve supplied takes, choose loudness and pause classes deliberately |
| Decide what each moment shows | [motion-storyboard](../motion-storyboard/SKILL.md) | Readable job/hero/action/zones/cues beat sheet, storyboard.json and resolved timing; apply editorial review gates before coding |
| Explore image concepts when useful | `$marketing-image-board` (marketing-images plugin) | Stable concept IDs and locally cropped previews; references are optional, grid/count follow the task |
| Create selected final image assets | `$marketing-image-producer` (marketing-images plugin) | Full-resolution selected assets and provenance; board previews are not final production assets |
| Generate a specifically approved video asset | [marketing-veo-video](../marketing-veo-video/SKILL.md) or [marketing-omni-video](../marketing-omni-video/SKILL.md) | Selected reviewed clip, measured metadata and saved recovery identity; optional branches, never prerequisites |
| Import assets and maintain the production project | [motion-video-producer](../motion-video-producer/SKILL.md) | Frozen asset manifest, source windows/sound policy, project profiles and current timing; replace initialization's fictional demo before real production |
| Author animation and place/mix media | [motion-composer](../motion-composer/SKILL.md) | Editable generator plus separately composed requested ratios; use a project-local custom generator for Three.js/HTML scenes or advanced audio |
| Verify and deliver | [motion-video-qa](../motion-video-qa/SKILL.md) | Actual frame/listening review and encoded-file checks per requested variant, with unperformed checks stated |

Use the producer's [HyperFrames capability map](../motion-video-producer/references/hyperframes-routing.md) for external runtime domains: core/registry/animation/keyframes for implementation, media-use for frozen music/SFX and source treatments, hyperframes-audio for the placed mix, and CLI for preview/check/render. Music-to-video applies when the track drives pacing. Captions, talking-head overlays, Figma imports and product captures are conditional workflows. Availability of a reference checkout does not prove tools or renderer are installed.

## Checkpoints and delivery

Before composition, confirm that exact copy, beat jobs/heroes, ratio-specific zones, cue anchors, asset evidence and sound policy agree. Resolve actual word cues and measured clip windows; missing assets or anchors remain explicit, never guessed. SFX/layout notes need implementation in the generator; recording a note does not place it.

Verify cheapest first: project/cue/hash checks → build and framework lint/check → snapshots at boundaries/midpoints/transition extremes → actual frame and audio review → authorized render → encoded dimensions/duration/audio checks and final frame review. A request for a finished video normally includes local rendering; preserve existing authorization rather than adding an approval gate to each stage. A plan-only request stops at the plan. Missing runtime allows independent planning/data checks, with render/preview limitations reported.

Deliver the actual encoded files and editable source when requested, identify which ratios passed which checks, and name material unresolved limitations. Provider success, structural validation or FFprobe alone does not establish visual quality, natural speech or a balanced mix. Publishing, ad-account changes and messaging are separate actions requiring scope authorization.

## Revisions: start at the changed dependency

| Request | Route and propagation |
| --- | --- |
| Too long | Voice: preview pause classes/trim while preserving deliberate holds; tighten visual holds; rewrite/re-record only if necessary. Do not speed approved narration or impose an unverified universal duration ceiling |
| Change a spoken line/CTA | Voice: exact matched replacement with context, backup and sample-exact retiming. Update script, deleted cue anchors, pause policy, captions and claim-bearing visuals, then resolve/build/QA |
| Weak hook, slide-like beat or wrong visual | Reproduce the affected frames; art/storyboard decide job, hero, treatment, zones and handoff; composer implements. Preserve audio unless the script needs a change |
| Loudness or music/SFX balance | Voice normalize for source level; composer/runtime audio for placed mix. Listen to affected joins and final mix, and recheck encoded audio |
| New aspect ratio | Producer adds a profile; storyboard/composer reframe zones; QA reviews and verifies the new export |
| Caption/hashtags only | Edit the requested text. External caption copy needs no video render; burned-in caption changes require rebuild/render/QA |
| Export an existing project | Producer/composer/QA inspect current inputs/build/runtime and render the requested variants without repeating strategy |

Edit authoritative artifacts and generator source; preserve Studio/user changes before rebuilding. Audio/script/storyboard/profile changes require refreshed resolved timing and compositions. Review neighboring beats and every affected ratio. Local reversible revisions proceed within the request.

Veo and Omni remain explicitly opt-in: present the prepared provider/model, prompt/media, settings and current estimate and obtain approval for that exact paid request before submitting. General video-production permission or an available API key does not enable them. Preserve saved job/conversation identities; recover uncertain jobs without automatic resubmission. Other paid services also stay within authorized scope, use their dry-runs and preserve successful outputs.
