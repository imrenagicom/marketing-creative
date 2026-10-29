---
name: motion-video-producer
description: Deprecated Marketing Creative skill for mixed-media marketing video projects and exports. For new work use studio-producer with editor (video-studio plugin). Use this only to resume or revise an existing Marketing Creative project.
---

# Motion Video Producer

> **Deprecated.** Marketing Creative is being retired in favour of Video Studio and Marketing Images. For new work, use `$studio-producer` with `$editor` (video-studio plugin). Use this skill only to resume or revise an existing Marketing Creative project, and keep that project's files intact.

Own the authorized deliverable and project state. Resume from existing artifacts before asking questions. For an inspection, edit, render or status request, perform that operation without restarting the full workflow.

[marketing-video](../marketing-video/SKILL.md) is the user-facing video workflow entry point and revision router. Direct invocations here remain supported; do not bounce an existing production back through intake. Project state, mixed-media integration and final delivery stay with this producer.

Own the mixed-media timeline and final exports. Provider video skills create source assets or standalone clips; they do not replace this orchestrator, its script/timing decisions or its final QA. Use supplied/local assets and deterministic composition by default. Veo and Omni are optional, explicitly approved additions because they cost more.

## Route the missing work

| Need | Owner |
| --- | --- |
| Campaign strategy or audience/offer decisions | `$marketing-brief` (optional marketing-performance plugin; use the supplied brief or establish the necessary strategic facts directly if unavailable) |
| Distinct creative ideas or a selected creative brief | [creative-ideation](../creative-ideation/SKILL.md) |
| Exact ad script and production direction | [ad-video-director](../ad-video-director/SKILL.md) |
| Contact-sheet image exploration | `$marketing-image-board` (marketing-images plugin) |
| Selected standalone/generated images | `$marketing-image-producer` (marketing-images plugin) |
| User-approved Veo asset/reference/interpolation/extension | [marketing-veo-video](../marketing-veo-video/SKILL.md) |
| User-approved Omni generation/conversational editing/extension | [marketing-omni-video](../marketing-omni-video/SKILL.md) |
| Visual identity, style and motion language | [motion-art-director](../motion-art-director/SKILL.md) |
| Visual beats and semantic timing cues | [motion-storyboard](../motion-storyboard/SKILL.md) |
| Narration, alignment and audio revision | [motion-voice](../motion-voice/SKILL.md) |
| Renderable animation and media placement | [motion-composer](../motion-composer/SKILL.md) |
| Production checks, frame review and delivery validation | [motion-video-qa](../motion-video-qa/SKILL.md) |

A general explainer can bypass ad strategy. A supplied script/concept can enter downstream. Silent work skips voice. Music can drive timing when that is the request. Stage selection does not authorize subagents or require separate chats.

Use the [HyperFrames capability map](references/hyperframes-routing.md) to load relevant installed domains at the stage that needs them. It reviews all 21 upstream skills, including optional product captures, captions/overlays, music-led promos, Figma imports and motion assets. Keep ownership here and derive any runtime handoff from existing briefs; external workflows do not restart strategy, change required ratios or authorize paid providers.

## Resolve and combine assets

Read [asset-assembly.md](references/asset-assembly.md) when combining source media or custom scenes. Plan each beat's asset source, evidence status, framing, source offset and sound policy. Use the [asset importer](scripts/assets.py) to copy supplied/generated images, clips, audio and local scene resources into the project, validate hashes/metadata, retain generation provenance and back up its manifest. Importing does not mark an asset reviewed or update the storyboard automatically.

Choose provider generation only when the user explicitly approves its prepared prompt/media, model, mode, count, settings and current estimate. A general video request, available API key or an agent's choice of provider is not approval. Continue independent local work while the paid option is pending. Each additional generation/edit/extension must be covered by explicit approval of that request; uncertain jobs are resumed or investigated, never automatically regenerated.

For conversational Omni changes, retain the selected run directory in project notes and use its Python history/continue commands to preserve prior interaction context. Track the new selected run after each completed revision and import it under a new asset ID. Keep earlier versions available for rollback or deliberate branching; an unresolved turn is recovered before another paid modification. Veo uses its documented sourceRun extension flow rather than Omni conversation IDs.

Use image/footage modes for frozen media; use project-owned custom generators for Three.js, HTML components, layered overlays and audio mixes. A custom generator can combine those scenes and ordinary media in the same timeline. The bundled renderer is a construction example, not a Three.js engine. The composer authors source, scene adapters and per-ratio layout; the producer owns sequencing, source selection and final integration.

## Maintain one project

Read [project-contract.md](references/project-contract.md) and [placements.md](references/placements.md). The bundled [project tool](scripts/project.py) initializes profiles, validates artifacts and resolves word/seconds cues. Invoke it by its actual installed path; it locates its resources relative to its own file, independent of working directory or client-specific environment variables.

```sh
python3 <this-skill>/scripts/project.py init <project-dir> --id demo --ratios 16:9 9:16 4:5 1:1 --duration 8
python3 <this-skill>/scripts/project.py resolve <project-dir>
python3 <this-skill>/scripts/project.py validate <project-dir>
```

Initialization creates an explicitly labeled fictional construction example. Replace its content and requirements before making a real ad. Do not overwrite an existing project. A new output ratio needs its own layout, frame review and export check. Duration cutdowns with different narration use separate project directories sharing the briefs/concept.

## Execute and resume

For narrated work: establish script → art direction → actual audio/alignment → resolved storyboard → composition → QA → export. Art direction and provisional storyboard can start earlier, but final timing follows the recording. For silent work, use explicit seconds or a supplied beat grid.

Use HyperFrames as the default render runtime. When available, read its installed entry/core/domain skills for the current technical contract; they own framework setup, media behavior and renderer commands. The bundled [runtime reference](../motion-composer/references/runtime.md) gives the minimum handoff and dependency checks. Missing runtime does not prevent planning or artifact checks; state precisely what remains unverified.

Preserve existing selection and render authorization. Ask for creative decisions only when materially unresolved; do not add a universal approval step at every stage. Paid service calls, publishing and campaign changes require scope authorization; local reversible work proceeds. Do not claim a render or review happened when only structural validation ran.

## Revisions

Route a changed claim to scripting; a visual complaint to art/storyboard/composition; a spoken-line replacement or duration trim to voice. Reproduce reported problems at the affected moments. Regenerate timing after audio/script/storyboard/profile changes, rebuild, then review neighboring beats and all affected outputs. Generator output is disposable: preserve user edits from Studio before regeneration, migrate them into the generator, and never silently overwrite them.

See [sources.md](references/sources.md) for upstream origins and adaptations.
