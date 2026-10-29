---
name: motion-storyboard
description: Deprecated Marketing Creative skill for visual beats, timing cues and per-ratio framing. For new work use shot-designer (video-studio plugin). Use this only to resume or revise an existing Marketing Creative project.
---

# Motion Storyboard

> **Deprecated.** Marketing Creative is being retired in favour of Video Studio and Marketing Images. For new work, use `$shot-designer` (video-studio plugin). Use this skill only to resume or revise an existing Marketing Creative project, and keep that project's files intact.

Read the script, selected creative brief, visual direction, assets and placement profiles. Decide what each beat shows before coding. A sentence, a visual beat, a camera move and a scene change are different units.

Read [beat-planning.md](references/beat-planning.md) before choosing visuals or repairing a slide-like cut. Fill the beat sheet before composition: job → hero → action → framing/zones → cues → handoff. Choose the visual treatment from the meaning and evidence of the line; a polished visual in the wrong treatment still fails to explain it.

## Define each beat

Read the [project contract](../motion-video-producer/references/project-contract.md). Record stable ID; persuasive/narrative job; main visual and state/action change; cue start/end; framing and focal point; exact overlay; required assets/proof; transition; optional sound cue; caption and per-ratio layout decisions.

Use word anchors when aligned narration exists, seconds for deliberate silent timing, or times derived from an approved music beat grid. Resolve anchors through the [project tool](../motion-video-producer/scripts/project.py). Identify the script segment and an exact phrase; repeated phrases require an explicit occurrence. Missing/ambiguous matches fail instead of guessing.

Plan one visual response to each meaningful information change, not one scene per sentence. Keep enough time for comprehension. Intentional empty space or silence is allowed; mark an intentionally blank visual beat explicitly. Do not force real-screen assets into conceptual/illustrated explainers or add counters unsupported by the script.

Give the hero enough room to make its key detail readable in every requested ratio. Declare media, type/caption and optional character zones; crop or resequence competing information instead of shrinking everything. Tie exits and incoming action to the next semantic cue, and check that each visible object still belongs to the current beat. Record deliberate holds/blank beats with their purpose rather than filling them with decoration.

For mixed-media beats, identify supplied/generated image or footage, authored HTML component or Three.js scene, plus stable asset IDs, measured source window and mute/retain/mix policy. Mark proposed paid generation as pending explicit approval; do not assume it exists. Use measured results and review extension joins before final timing. Request/import assets through motion-video-producer rather than having the storyboard silently invoke providers.

Use hyperframes-creative's beat-direction and storyboard-recipe when a visual review board helps; sample posed frames from the assembled composition so the board tests actual layout. Use hyperframes-animation/registry for concrete motion choices, music-to-video only when the track drives pacing, and talking-head-recut/embedded-captions for matching footage treatments. Read the [capability map](../motion-video-producer/references/hyperframes-routing.md); translate upstream formats into this project's stable beats and cues, keeping storyboard proof separate from image concept boards.

## Plan adaptations

For every required ratio, record subject framing, text zones, captions, crop and interaction focus. Use per-variant beat overrides when needed. If the same copy is unreadable, shorten the overlay or change layout while preserving claims and exact mandated copy. A different duration/argument needs a separate cutdown, not distorted timing.

## Handoff and revisions

Write `storyboard.json`, resolve it to `timing.resolved.json`, and provide a readable beat sheet. Review opening, transitions and ending as well as midpoints. Actual audio can invalidate provisional seconds; re-resolve before composition.

Apply the reference's editorial review gates before handoff. Resolver coverage and sampled browser checks do not automatically establish correct visual treatment, hero readability, zone separation or meaningful action. Send these decisions and any unresolved checks to motion-composer and motion-video-qa.

For revisions, preserve stable beat IDs where their meaning remains. Check the beats either side and all affected ratio overrides. Pass unresolved evidence/asset requirements to the composer explicitly.
