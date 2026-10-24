---
name: generative-shot-director
description: Compile production-grade multi-beat and per-shot generative video prompts with @Image role locks, motivated camera vectors, physics/lighting rules, and negative constraints using specialized craft cartridges.
---

# Generative Shot Director (`generative-shot-director`)

`generative-shot-director` is **Stage 4** of the `video-studio` pipeline. It transforms the approved `direction-brief.md`, `timing-map.json`, and `visual-bible.md` into deterministic, multi-beat or per-shot prompts for generative video engines (Seedance 2.5, Veo, Omni, Kling, Runway).

## Load the Matching Craft Cartridge First

Before drafting any shot prompt, load the Craft Cartridge that matches the project's paradigm:
- **[`references/cartridge-multi-angle-presenter.md`](references/cartridge-multi-angle-presenter.md)** — For virtual-studio talking-head explainers cutting across 6 camera setups with `Karakter` + `Workspace` + `Voice` references.
- **[`references/cartridge-action-and-bullettime.md`](references/cartridge-action-and-bullettime.md)** — For 30-second high-speed chases, 3D/anime combat, multi-reference vehicle/character locks, and 180°–270° bullet-time slow-motion orbits.
- **[`references/cartridge-diegetic-handheld-vlog.md`](references/cartridge-diegetic-handheld-vlog.md)** — For consumer Mini-DV camcorder realism, wrist-led selfie pans, autofocus hunting, and culturally authentic street/campus vlogs.

## Mandatory Prompt Architecture

Every compiled generative prompt must include these nine structured blocks in order:

1. **Title & Format Header**:
   - Exact duration (e.g., `30 seconds` or `8 seconds`), aspect ratio (`16:9` or `9:16`), visual medium (`cinematic photorealistic CGI`, `3D supernatural action`, or `handheld Mini-DV camcorder footage`), pacing, and reference mode (`Generate entirely from the master reference images/audio and text`).
2. **Reference Roles (`@Image1..N`, `@Audio1`)**:
   - Explicit identity, wardrobe, proportion, and material rules for each reference tag. State clearly whether background characters are generated from text only (`禁止标记或引用其他角色参考图` / `Do not reference other character sheets for crowd extras`).
3. **Position & Power Lock**:
   - Immutable rules preventing seat swapping, character duplication, costume drift, or premature ability reveals (e.g., `"Do not summon the giant smoke creature before 00:20"`).
4. **Environment & Spatial Geography**:
   - Foreground, midground, and background depth layers, horizon/landmark continuity, and how action physically disturbs the environment (dust bursts, ash spirals, reflection streaks).
5. **Time-Sliced Storyboard (`00:00–00:03`, `00:03–00:06`, ...)**:
   - Every 3-to-6-second beat must explicitly declare:
     - **Action (`Aksi Karakter Secara Spesifik`)**: Anticipation, acceleration, impact/gesture, recoil, and recovery.
     - **Camera (`Arah Gerak` + `Framing`)**: Exact lens framing and motivated movement vector.
     - **VFX / Lighting Interaction**: Localized glows, exhaust, particles, or exposure shifts.
     - **Audio / Dialogue / SFX**: Exact spoken line in quotes or synchronized physical sound effects.
6. **Camera Language Summary**:
   - Global rules preserving screen direction (no arbitrary left-right flips), banning unmotivated camera rotation or teleportation, and maintaining readable faces/silhouettes.
7. **Lighting & Materials**:
   - Practical key light source from `visual-bible.md`, localized interactive lighting, and surface reflection behavior (paint, glass, skin, cloth, asphalt).
8. **Motion, Physics & Performance**:
   - Weight transfer, cloth inertia, elastic vs. rigid anatomy rules, and natural conversational vs. combat pacing.
9. **Audio Design & Negative Constraints**:
   - Explicit positive audio rules and an exhaustive `NEGATIVE CONSTRAINTS` block (`No identity changes, no outfit changes, no seat swapping, no distorted hands, no extra limbs, no teleportation, no random explosions, no subtitles, no title cards, no watermarks`).

## Checkpoint 3 (Pre-Flight Approval Gate)

Always present the compiled prompt file (`shot-prompts.md`) and any cost/credit estimate to the user at **Checkpoint 3** before invoking any paid video generation API or external provider. Once base video clips are generated and approved, hand off to [`video-scene-tracker`](../video-scene-tracker/SKILL.md) (for hybrid overlays) or [`continuity-and-qa`](../continuity-and-qa/SKILL.md).
