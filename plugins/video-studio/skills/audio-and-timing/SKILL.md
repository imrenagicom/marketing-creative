---
name: audio-and-timing
description: Generate or align voiceover before video production for natural expression timing, or design synchronized SFX-only and beat-grid timelines including acoustic perspective shifts and bullet-time audio dilation.
---

# Audio and Timing (`audio-and-timing`)

`audio-and-timing` is **Stage 2** of the `video-studio` pipeline. Video is locked to time: generating or structuring the audio spine *before* final visuals ensures that character lip-sync, facial expressions, camera cuts, and programmatic overlays hit exact millisecond cues.

## Three Audio Modes

### Mode A: Voice-First Architecture (Presenter, Tutorial & Explainer)
1. **Generate Voice Before Video**:
   - Synthesize the dialogue or narration (e.g., ElevenLabs v4) before generating any talking-head or character clips.
   - Having the audio waveform first guarantees that character expressions, breaths, and sentence transitions have natural timing (`timing yang pas`) rather than forcing speech into an arbitrary video clip length.
2. **Extract Word & Phrase Timestamps**:
   - Record exact start/end timestamps (`timing-map.json`) for:
     - **Primary Hero Keywords**: Words that trigger giant background typography behind the presenter's head (`TUTORIAL`, `WORKFLOW`, `CHATGPT`, `SEEDANCE`, `KONTINUITAS`, `SAVE`, `FOLLOW`).
     - **Secondary Connector Phrases**: Words that ride the foreground kinetic rail (`yang nanya`, `buat`, `dan`, `video INI!`).
     - **Camera Cut & Wipe Cues**: Exact pause boundaries between sentences where camera setups switch or graphic shutter wipes fire.

### Mode B: Diegetic Location Audio (Handheld Vlog & Street Realism)
1. **Spoken Lip-Sync + Environmental Depth**:
   - Anchor exact time windows (e.g., `00–08s`, `15–21s`, `21–30s`) for on-camera spoken lines so the generative video model lip-syncs clearly without rushed delivery.
   - Layer authentic location acoustics around the voice: footsteps on concrete, crowd chatter at realistic distance, passing motorcycles, water splashing, or clothing rustle—without overpowering the primary voice.
2. **Strict Music Ban When Realism Demands It**:
   - For raw consumer DV/camcorder vlogs, explicitly forbid background music, studio voiceover, or cinematic trailers stingers so the footage feels 100% captured in-camera.

### Mode C: Synchronized SFX-Only Action (Cinematic Chase & 3D Combat)
1. **Per-Beat Physical Sound Design**:
   - Map every 3-second action beat to concrete physical sound layers: propulsion/engine pitch, Doppler pass-bys, staff swings, elastic impacts, stone debris, or volumetric smoke turbulence.
2. **Acoustic Perspective Shifts (Exterior vs. Interior)**:
   - When cutting from an aerial/street camera into a vehicle cabin, shift the soundstage from open rushing wind and distant city ambience to enclosed cabin vibration, muffled sirens, and steering handling noise.
3. **Bullet-Time Audio Dilation**:
   - When entering a bullet-time slow-motion orbit, stretch, pitch-drop, and muffle environmental sounds, engines, and sirens into a deep resonant hum; the instant normal speed resumes, surge the full-frequency roar and rushing air back sharply.

## Output Artifact (`timing-map.json`)

Produce `timing-map.json` (or an annotated audio cue table in `direction-brief.md`) containing:
- Total duration, FPS, and audio mode (`voice-first`, `diegetic-vlog`, or `sfx-only`).
- Beat windows (`start_sec`, `end_sec`, `camera_setup_id`).
- Word-level timestamps and emphasis tags (`hero_back_plane`, `foreground_rail`, `ui_card_trigger`, `hud_node_trigger`, `shutter_wipe`).
- Positive sound layers and explicit negative audio constraints (e.g., `No background music, no dialogue, no musical stingers`).

Hand off the locked timing map to [`visual-bible-and-refs`](../visual-bible-and-refs/SKILL.md) and [`generative-shot-director`](../generative-shot-director/SKILL.md).
