---
name: continuity-and-qa
description: Audit rendered frames and transition seams across the 4 Pillars of Continuity, 2.5D rotoscope occlusion cleanliness, chromatic contrast, HUD/UI tracking lock, and audio/lip sync before final multi-ratio delivery.
---

# Continuity and QA (`continuity-and-qa`)

`continuity-and-qa` is **Stage 7** of the `video-studio` pipeline. AI agents frequently miss visual drift, broken rotoscope edges, or mistimed cuts unless they run a structured frame-extraction and seam-inspection protocol.

## Mandatory Inspection Protocol

### 1. Extract Keyframes at Every Beat & Seam
Extract JPEG/PNG inspection frames across the timeline:
- **Every Beat Midpoint**: Verify primary composition, typography legibility, UI card perspective, and subject identity.
- **Every Transition Seam (`T - 2 frames`, `T`, `T + 2 frames`)**: Verify that graphic shutter wipes, monochromatic flashes, or camera cuts contain no white flashes, unmasked frame pops, or dead static frames.

### 2. Audit the 4 Pillars of Continuity (`Kontinuitas`)
Across all generative shots in the sequence, verify:
1. **`Wajah` (Face & Head)**: Facial identity, hair, glasses/props, or non-human head geometry (e.g., carved pumpkin head or ghost eyes) has zero morphing across frontal, profile, and 3/4 angles.
2. **`Outfit` (Wardrobe)**: Exact garment layering, logos/graphics, and colors match in wide standing shots, close-ups, and OTS shots.
3. **`Lokasi` (Spatial Geography)**: Wall murals, shelves, monitors, windows, or horizon landmarks sit on the physically correct side of the frame when camera angles change.
4. **`Gerakan` (Action & Velocity Match)**: Subject posture, hand gestures, and camera momentum flow continuously across cuts without robotic freezes or impossible physics.

### 3. Audit 2.5D Depth, UI Cards & HUD Overlays
When programmatic motion graphics ([`motion-and-compositor`](../motion-and-compositor/SKILL.md)) are layered over footage:
- **Rotoscope Occlusion Check**: Confirm hero midground words (`TUTORIAL`, `WORKFLOW`, `SAVE`, `FOLLOW`) sit cleanly *behind* the subject's hair and shoulders without edge halos, and foreground hand mattes cleanly occlude stacked cards when gesturing.
- **Chromatic Separation Check**: Confirm primary electric-accent graphics pop immediately against the complementary background without requiring muddy dark scrims.
- **Planar & Point Tracking Lock**: Confirm 3D perspective UI cards stay pinned to physical monitor bezels without sliding, and HUD node dots (`WAJAH`, `LOKASI`, `OUTFIT`, `GERAKAN`, cheekbone tracker) point to their exact anatomical/environmental targets.

### 4. Audio, Lip-Sync & Encoding Verification
- Verify spoken dialogue lip-syncs naturally to the voice stem and SFX impacts/bullet-time slowdowns align to the frame with `timing-map.json`.
- Verify output container specs (`H.264 High Profile`, `30 fps` or `24 fps`, `AAC Stereo 44.1/48 kHz`) and safe-zone compliance across every requested aspect ratio (`9:16`, `16:9`, `4:5`, `1:1`).

## Output Report (`qa-report.md`)

Generate a structured QA report embedding the extracted frame grid, pass/fail scores per pillar, and exact timestamped remediation instructions if any shot or overlay needs re-rendering before **Checkpoint 4 (Final Sign-Off)**.
