---
name: video-studio
description: Route and orchestrate end-to-end video production across AI cinema, 3D action, diegetic handheld vlogs, multi-angle presenter explainers and programmatic 2.5D motion graphics using the 7-stage Spine and Craft Cartridge architecture.
---

# Video Studio (`video-studio`)

`video-studio` is the master entry point and checkpoint router for producing Hollywood-grade generative cinema, diegetic handheld vlogs, standalone motion explainers, and hybrid AI-presenter videos with 2.5D programmatic overlays.

## Core Philosophy

1. **Direction and Camera Angles First (Stop Burning Credits)**: Never start by generating random images or typing vague `"cinematic video"` prompts. Lock the narrative idea, base character acting rules, and motivated camera setup map before generating media.
2. **Voice and Timing Before Visuals**: When a video includes spoken dialogue or narration, generate or lock the voiceover track *before* generating video shots so facial expressions, lip-sync, and cuts land on natural speech cadences.
3. **Spine + Craft Cartridges**: Every project flows through a predictable **7-Stage Spine** with explicit **Human-in-the-Loop Checkpoints**, loading specialized **Craft Cartridges** on demand for the specific visual paradigm.

## Production Paradigms & Routing Recipes

Choose the paradigm that matches the user's goal, or jump directly into any downstream stage when upstream assets already exist:

| Paradigm | Typical Use Case | Spine Route & Active Cartridges |
| :--- | :--- | :--- |
| **1. Hybrid AI Presenter + 2.5D Motion Graphics** | Tech tutorials, product breakdowns, founder explainers (`9:16` or `16:9`) | [`director-and-script`](../director-and-script/SKILL.md) → [`audio-and-timing`](../audio-and-timing/SKILL.md) (Voice First) → [`visual-bible-and-refs`](../visual-bible-and-refs/SKILL.md) (`Karakter` + `Workspace` + `Voice`) → [`generative-shot-director`](../generative-shot-director/SKILL.md) ([`cartridge-multi-angle-presenter`](../generative-shot-director/references/cartridge-multi-angle-presenter.md)) → [`video-scene-tracker`](../video-scene-tracker/SKILL.md) → [`motion-and-compositor`](../motion-and-compositor/SKILL.md) (All 3 Motion Cartridges) → [`continuity-and-qa`](../continuity-and-qa/SKILL.md) |
| **2. Pure Generative Cinema & 3D Action** | High-speed chases, anime/3D combat, sci-fi trailers, bullet-time showcases | [`director-and-script`](../director-and-script/SKILL.md) → [`audio-and-timing`](../audio-and-timing/SKILL.md) (SFX-Only / Beat Grid) → [`visual-bible-and-refs`](../visual-bible-and-refs/SKILL.md) (`@Image1..N` Locks) → [`generative-shot-director`](../generative-shot-director/SKILL.md) ([`cartridge-action-and-bullettime`](../generative-shot-director/references/cartridge-action-and-bullettime.md)) → [`continuity-and-qa`](../continuity-and-qa/SKILL.md) |
| **3. Diegetic Handheld / Realism Vlog** | Consumer Mini-DV camcorder vlogs, street/campus realism, single-take POV stories | [`director-and-script`](../director-and-script/SKILL.md) → [`visual-bible-and-refs`](../visual-bible-and-refs/SKILL.md) (Character + Period/Location Lock) → [`generative-shot-director`](../generative-shot-director/SKILL.md) ([`cartridge-diegetic-handheld-vlog`](../generative-shot-director/references/cartridge-diegetic-handheld-vlog.md)) → [`continuity-and-qa`](../continuity-and-qa/SKILL.md) |
| **4. Standalone Programmatic Motion / UI Explainer** | Code-driven kinetic typography, dark-mode UI showcases, data visualizations | [`director-and-script`](../director-and-script/SKILL.md) → [`audio-and-timing`](../audio-and-timing/SKILL.md) → [`visual-bible-and-refs`](../visual-bible-and-refs/SKILL.md) (Palette & Typography) → [`motion-and-compositor`](../motion-and-compositor/SKILL.md) → [`continuity-and-qa`](../continuity-and-qa/SKILL.md) |

## The 7-Stage Spine & Human Checkpoints

Never advance past a paid or destructive boundary without the corresponding checkpoint sign-off:

1. **Stage 1 — [`director-and-script`](../director-and-script/SKILL.md)**
   - Outputs `direction-brief.md`: Hook, spoken script or 3-second action beat sheet, **Base Acting & Movement Direction** per character, and the **Motivated Camera Setup Map**.
   - **Checkpoint 1 (Zero Cost)**: User approves the story, dialogue, acting rules, and camera angle plan.
2. **Stage 2 — [`audio-and-timing`](../audio-and-timing/SKILL.md)**
   - Outputs `timing-map.json` + voice stems (ElevenLabs v4 workflow) or an SFX-only soundscape specification (exterior vs. interior acoustic perspective, bullet-time audio slowdown/restoration).
   - **Checkpoint 2A (Low Cost)**: User approves voice delivery cadence or beat timing.
3. **Stage 3 — [`visual-bible-and-refs`](../visual-bible-and-refs/SKILL.md)**
   - Outputs `visual-bible.md` + master reference sheets (`@Image1`, `@Image2`, `@Image3`): enforces **Complementary Chromatic Contrast** (e.g., Electric Cobalt Blue subject against Warm Amber environment), **Practical Lighting Anchors** baked into location plates, and the **4 Pillars of Continuity** (`Wajah`, `Outfit`, `Lokasi`, `Gerakan`).
   - **Checkpoint 2B (Static References Only)**: User approves character, workspace, and vehicle/prop reference images before any video generation credits are spent.
4. **Stage 4 — [`generative-shot-director`](../generative-shot-director/SKILL.md)**
   - Compiles multi-beat or per-shot generative prompts with explicit `@Image` role locks, `Arah Gerak` (Camera Movement Direction), `Framing`, `Aksi Karakter Secara Spesifik`, physics rules, and negative constraints.
   - **Checkpoint 3 (Pre-Flight Prompt & Clip Gate)**: User approves the exact shot prompts and cost estimate before generation, then reviews the base video clips.
5. **Stage 5 — [`video-scene-tracker`](../video-scene-tracker/SKILL.md)** *(For Hybrid Overlays)*
   - Analyzes base video clips to output `spatial-track.json`: foreground subject rotoscope alpha masks (head/shoulders/hands), 3D perspective corner-pin coordinates for physical monitors/surfaces, and 2D motion tracker nodes.
6. **Stage 6 — [`motion-and-compositor`](../motion-and-compositor/SKILL.md)**
   - Authors deterministic code-driven scenes and overlays: 3-plane 2.5D depth typography (behind the presenter's head, in front of torso), 3D planar-tracked dark UI cards, HUD viewfinder brackets, node callout leader lines, and graphic shutter bar wipes.
7. **Stage 7 — [`continuity-and-qa`](../continuity-and-qa/SKILL.md)**
   - Audits extracted frames across every beat and transition seam against the 4 Pillars of Continuity, occlusion mask cleanliness, chromatic contrast, and audio/lip sync.
   - **Checkpoint 4 (Final Delivery Sign-Off)**: User approves the frame contact sheet and final render across target aspect ratios (`9:16`, `16:9`, `4:5`, `1:1`).
