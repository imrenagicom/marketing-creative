---
name: director-and-script
description: Transform a video idea or voice dump into a structured directing brief, spoken script or 3-second action beat sheet, base character acting rules, and motivated multi-angle camera map.
---

# Director and Script (`director-and-script`)

`director-and-script` is **Stage 1** of the `video-studio` pipeline. Quality starts with the idea, acting direction, and camera angles—never with raw image or video prompts. A boring idea or unmotivated camera flow cannot be saved by high-resolution rendering.

## Core Directing Laws

1. **Ban Vague Buzzwords (`"Cinematic"` Alone Is Not Enough)**:
   - Never write `"cinematic shot"` as a camera instruction. Every beat or shot must explicitly specify three concrete elements:
     - **Movement Direction (`Arah Gerak`)**: e.g., extreme high-angle crane-down into fast aerial tracking, low-angle 120° orbit left-to-right, wrist-led handheld pan from selfie to crowd.
     - **Shot Framing (`Framing`)**: e.g., Frontal Medium Close-Up (MCU), Wide Full-Body Standing Shot, Side-Profile Medium Shot, Over-the-Shoulder (OTS) Monitor Focus.
     - **Specific Character Action (`Aksi Karakter Secara Spesifik`)**: e.g., standing beside office chair gesturing with right hand, gripping steering wheel with both hands while bracing through a sharp turn, compressing gummy body like a spring before rebounding.
2. **Motivated Camera Movement (`Tracking Harus Punya Alasan`)**:
   - Every push-in, whip-pan, orbit, or crane move must be physically caused by or reveal a narrative action (e.g., pushing over the presenter's shoulder because he points at the ultrawide monitor, or whip-panning with the sweep of a wizard's staff).
3. **Human-Led Base Acting Direction**:
   - LLMs default to stiff, robotic, or overly theatrical delivery unless constrained. Define a **Base Acting Profile** for every character/subject up front (posture, weight transfer, eye line, vocal tone, facial micro-expressions) that governs every beat.

## Step-by-Step Workflow

### 1. Lock the Paradigm & Format Specs
Identify the target format and paradigm:
- Aspect ratio (`9:16` vertical, `16:9` widescreen, `4:5`, `1:1`), duration (e.g., `30s` or `50–60s`), frame rate (`30 fps` or `24 fps`).
- Audio mode: **Voice-Driven** (dialogue/narration leads timing), **Diegetic Location Dialogue** (spoken on-camera with natural street/room ambience), or **SFX-Only Action** (no music, no voiceover—pure synchronized physical sound effects).

### 2. Define Base Character Acting & Physicality Rules
For each character or presenter, document:
- **Posture & Weight**: How they stand, sit, walk, or brace against acceleration/impacts.
- **Hands & Props**: Specific hand engagement (e.g., right hand gesturing toward foreground cards, both hands on steering wheel, holding Mini-DV camcorder at arm's length).
- **Vocal & Facial Tone**: Conversational creator energy vs. focused driver vs. candid friend interaction. For non-human heads (e.g., carved pumpkin heads or stylized ghosts), specify whether facial features remain rigid while neck/shoulders carry the emotion.

### 3. Map the Multi-Angle Camera Architecture
Prevent static visual fatigue by designing the camera setup map before writing shot prompts:
- **For Studio Presenters / Explainers**: Rotate across **5 to 6 distinct camera setups** inside the same 3D space (1. Frontal MCU at desk, 2. Wide Full-Body Standing beside chair, 3. Side-Profile Medium typing/pointing, 4. Over-the-Shoulder into monitor, 5. Dynamic Standing 3/4 turn, 6. Low-Angle Orbiting MCU).
- **For Action / Chases / Combat**: Slice the timeline into **3-to-4-second high-density beats**, alternating exterior scale (aerial canyon, low wheel-track) with interior/close-up reaction shots and contrasting speed peaks with **Bullet-Time Orbits** (world freezes/slows while camera orbits 180°–270° smoothly).
- **For Diegetic Handheld Vlogs**: Lock the camera to the subject's physical arm/wrist (arm's-length selfie MCU → wrist rotation to pan across crowd → handoff to friend → return to selfie).

### 4. Write the Paired Script & Beat Table
Output `direction-brief.md` containing the complete beat-by-beat table:

| Time Window | Camera Setup & Motivated Move (`Arah Gerak` + `Framing`) | Character Action (`Aksi Spesifik`) | Spoken Dialogue / VO (`Naskah`) or SFX Focus | Planned Overlay / VFX Intent |
| :--- | :--- | :--- | :--- | :--- |
| `00:00–00:04` | Frontal MCU; subtle push-in as right hand rises | Presenter looks directly into lens, gestures right hand in front of chest | *"Banyak banget yang nanya tutorial video kemarin..."* | Foreground comment cards occluded by gesturing hand; giant `TUTORIAL` behind head |

## Output Handoff

Pause at **Checkpoint 1** for user review of `direction-brief.md`. Once approved, hand off to [`audio-and-timing`](../audio-and-timing/SKILL.md) (for voice/SFX timing) and [`visual-bible-and-refs`](../visual-bible-and-refs/SKILL.md) (for reference locking).
