---
name: motion-composer
description: Deprecated Marketing Creative skill for HyperFrames compositions for each ratio. For new work use motion-designer (video-studio plugin). Use this only to resume or revise an existing Marketing Creative project.
---

# Motion Composer

> **Deprecated.** Marketing Creative is being retired in favour of Video Studio and Marketing Images. For new work, use `$motion-designer` (video-studio plugin). Use this skill only to resume or revise an existing Marketing Creative project, and keep that project's files intact.

Read the approved/supplied briefs, script, style, storyboard, asset manifest and placement profiles. Read [runtime.md](references/runtime.md) before writing composition HTML. HyperFrames owns timeline seeking, timed clip visibility, media playback and rendering. Load its current installed domain skills when available.

The producer owns source selection and assembly. Read its [asset assembly](../motion-video-producer/references/asset-assembly.md) for imported footage/image provenance, source windows and sound policy. Combine reviewed frozen media with local Three.js scenes and HTML components through a project-owned custom generator when needed. Paid Veo/Omni requests remain explicitly approved upstream; a missing visual never authorizes a provider fallback.

Use the [HyperFrames capability map](../motion-video-producer/references/hyperframes-routing.md) for targeted implementation: core for mounts/media timing, registry for reusable primitives, animation's Three.js/Lottie adapters for custom scenes, keyframes for camera/reframe motion, audio for the placed mix and studio for editable track organization. Read the matching installed reference before coding; use a compatible custom generator and fingerprint imported dependencies. A referenced adapter does not add those capabilities to the bundled example automatically.

## Build from intent and resolved timing

Validate/resolve the project using the [project tool](../motion-video-producer/scripts/project.py). Keep semantic cues in the storyboard and absolute seconds in generated timing. Build with a generator; output HTML can be rebuilt, but preserve and reconcile any user/Studio edits before regeneration.

Use [the bundled generator](scripts/compose.mjs) as a small construction example and starting contract, not a full design engine. It supports five construction primitives (type, UI tour, counter, collage, character stage), supplied images/footage, shared style tokens, optional aligned narration and all four canvas presets:

```sh
node <this-skill>/scripts/compose.mjs <project-dir> --gsap <local-gsap.min.js>
```

The local GSAP file is copied into each variant for offline reproducibility. Without `--gsap`, the pinned CDN is a development fallback; freeze it locally before final export. Use the [example data](assets/example/storyboard.json) and [visual examples](../motion-art-director/references/visual-examples.md) to understand what to adapt. The generator's fictional UI is not product evidence. Use image/footage modes for supplied captures. For interactive product reconstruction or more complex motion, register a project-local generator and custom visual modes through the shared contract; retain real product components, language and behavior.

## Adapt the composition

Read [placements](../motion-video-producer/references/placements.md). Generate each requested variant at its actual canvas dimensions, with placement-specific padding and a distinct layout where needed. Treat dimensions as configuration; no export/snapshot step may assume 1920×1080. Review text wrapping, crops, UI focus, camera clearance, captions and CTA for every variant.

Register one paused GSAP timeline per composition. Use explicit start/end states, seeded randomness if needed, and time-derived motion. Animate inner visual nodes, not runtime visibility on clips. Keep required fonts/media local, uniquely ID media, and let the framework control playback. For modular scenes, follow the runtime's sub-composition contract rather than adding a second player.

## Verify and deliver

Run [motion-video-qa](../motion-video-qa/SKILL.md): data checks → framework lint/check → snapshots at boundaries and midpoints → visual review → authorized render → export/audio verification. A plain browser opened on the generated HTML is not the HyperFrames preview. Distinguish source validation, browser inspection, runtime validation and actual encoded delivery.

Do not overwrite outputs from changed source without reconciling edits. Use `--force` only after preserving needed changes and when a rebuild is authorized.
