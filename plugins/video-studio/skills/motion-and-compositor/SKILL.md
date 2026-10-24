---
name: motion-and-compositor
description: Build deterministic programmatic motion graphics and hybrid 2.5D video compositions featuring rotoscoped behind-subject typography, 3D planar-tracked dark UI cards, HUD callout nodes, and graphic shutter wipes.
---

# Motion and Compositor (`motion-and-compositor`)

`motion-and-compositor` is **Stage 6** of the `video-studio` pipeline. It builds deterministic, seekable HTML/CSS/GSAP/Canvas compositions (such as HyperFrames compositions) either as standalone motion-graphics explainers or composited in 2.5D depth over generative/live video plates using coordinates from [`video-scene-tracker`](../video-scene-tracker/SKILL.md).

## Load the Matching Motion Craft Cartridges

Load the relevant craft cartridges before authoring scene code:
- **[`references/cartridge-25d-rotoscope-type.md`](references/cartridge-25d-rotoscope-type.md)** — For 3-plane z-depth layering (`Background Video` → `Midground Hero Display Words Behind Head` → `Rotoscoped Subject Matte` → `Foreground Connector Rail & Hand-Occluded Cards`).
- **[`references/cartridge-3d-planar-ui-cards.md`](references/cartridge-3d-planar-ui-cards.md)** — For simplified, high-contrast dark-mode UI mockups corner-pinned in 3D perspective onto physical monitors (`ChatGPT` checklist card, `ElevenLabs v4` pill waveform card, `Seedance` 3-slot reference card).
- **[`references/cartridge-hud-and-shutter-seams.md`](references/cartridge-hud-and-shutter-seams.md)** — For camera viewfinder brackets (`┌ ┐ └ ┘`), single-point cheekbone trackers, 4-node continuity leader lines (`WAJAH`, `LOKASI`, `OUTFIT`, `GERAKAN`), and horizontal bar shutter wipes.

## Core Compositing Laws

1. **Never Slap Flat Text Over the Center of a Face**:
   - Use multi-plane z-index stacking so large display keywords (`TUTORIAL`, `WORKFLOW`, `TIMING`, `SAVE`, `FOLLOW`) sit on the **Midground Plane (`z-index: 20`)** *behind* the segmented presenter matte (`z-index: 30`), while smaller secondary connector phrases (`yang nanya`, `buat`, `dan`, `video INI!`) sit on the **Foreground Plane (`z-index: 40`)** over the lower torso.
2. **Never Use Tiny, Unreadable Raw Screen Recordings**:
   - Replace dense browser screenshots with **simplified, high-contrast dark-mode UI cards (`#18181B`)** containing 3–4 oversized, legible elements (a prompt header, animated checkmarks, a responsive vertical pill waveform, or 3 square reference thumbnails + a glowing blue `Generate` pill button) mapped in 3D perspective over the monitor.
3. **Chromatic Discipline**:
   - Echo the subject's primary accent color (e.g., Electric Cobalt Blue `#1D63FF`–`#2563EB`) across all hero keywords, active UI pills, tracker dots, and shutter wipe bars so graphics unify with the wardrobe and pop against the warm background.
4. **Deterministic, Frame-Accurate Seekability**:
   - Drive animations from a single paused master timeline synced to `timing-map.json`. Never use `Date.now()`, unseeded `Math.random()`, or runtime network fetches that break deterministic frame capture.

## Workflow

1. Ingest `timing-map.json`, `visual-bible.md`, and (for hybrid videos) base video plates + `spatial-track.json`.
2. Set up the multi-plane DOM/Canvas stage at target resolution (`1080×1920` for `9:16`, `1920×1080` for `16:9`).
3. Author each beat's kinetic typography, 3D UI cards, HUD callouts, and shutter wipes using the loaded cartridges.
4. Hand off the rendered composition to [`continuity-and-qa`](../continuity-and-qa/SKILL.md) for frame and seam verification.
