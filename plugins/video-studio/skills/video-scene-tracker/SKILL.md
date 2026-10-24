---
name: video-scene-tracker
description: Extract foreground subject rotoscope alpha masks, 3D planar monitor corner-pin coordinates, and 2D motion tracker nodes from base video clips so programmatic motion graphics composite with true spatial depth.
---

# Video Scene Tracker (`video-scene-tracker`)

`video-scene-tracker` is **Stage 5** of the `video-studio` pipeline—the bridge between raw or AI-generated video footage and programmatic 2.5D motion graphics. Without accurate spatial coordinates and subject segmentation masks, "behind-the-head" typography bleeds across faces, 3D monitor UI cards float off-angle, and HUD callout nodes miss their targets.

## Three Core Extraction Passes

### 1. Multi-Plane Subject Segmentation (Rotoscope Alpha Masks)
To composite 3-plane 2.5D depth (`Background Plate` → `Midground Hero Typography` → `Foreground Subject Mask` → `Foreground Overlay Rail`), extract per-frame or keyframed segmentation mattes:
- **Torso & Head Matte (`subject-matte.webm` / SVG clip-path keyframes)**: Cleanly separates the presenter's hair, head, and shoulders from the studio background so giant hero display words (`TUTORIAL`, `WORKFLOW`, `TIMING`, `SAVE`, `FOLLOW`) sit *behind* the subject on the midground plane.
- **Independent Hand / Arm Foreground Matte (`hand-matte.webm`)**: When the presenter gestures in front of floating UI or social comment cards (such as presenting stacked X/Twitter reply cards in the opening hook), isolate the gesturing hand/forearm on a top-most z-plane so the hand physically occludes the cards.

### 2. 3D Planar Quad Extraction (Monitor & Surface Corner-Pins)
When a scene includes physical monitors, laptops, or desk surfaces that will display simplified dark-mode UI mockups:
- Sample keyframes across the clip window (e.g., `00:06–00:08` landscape monitor, `00:12–00:17` portrait monitor, `00:20–00:25` OTS ultrawide monitor).
- Record normalized `[x, y]` coordinates (`0.0–1.0` or pixel space `1080×1920`) for all four bezel corners (`top_left`, `top_right`, `bottom_right`, `bottom_left`).
- Compute or export the CSS `matrix3d(...)` / perspective transform and rotation angles (`rotateX`, `rotateY`, `rotateZ`) so [`motion-and-compositor`](../motion-and-compositor/SKILL.md) can corner-pin or slightly hover the dark UI card in matching 3D perspective.

### 3. 2D Feature & Node Point Trackers
For HUD viewfinders, single-point motion trackers, and multi-node continuity callouts:
- **Head Bounding Box (`framing_hud_box`)**: `[x, y, width, height]` trajectory of the subject's head for snapping viewfinder brackets (`┌ ┐ └ ┘`).
- **Single-Point Facial Tracker (`cheekbone_node`)**: Frame-by-frame `[x, y]` coordinates of a distinct facial landmark (e.g., right cheekbone during a low-angle camera orbit) so a tracked node dot stays locked to the skin.
- **Multi-Node Callout Anchors (`continuity_nodes`)**: Simultaneous `[x, y]` anchor coordinates for multi-target leader lines—e.g., `WAJAH` (eye/brow), `LOKASI` (background LED shelf), `OUTFIT` (shirt star graphic), and `GERAKAN` (shoulder/arm).

## Output Artifact (`spatial-track.json`)

Write `spatial-track.json` containing:
- Video resolution (`width`, `height`), `fps`, and total frame count.
- `rotoscope_layers`: paths to alpha-channel WebM/PNG-sequence mattes and active time ranges.
- `planar_surfaces`: array of tracked quads with keyframed corner coordinates and CSS perspective transforms.
- `point_trackers`: named `[x, y]` coordinate tracks and bounding boxes keyed by timestamp/frame.

Hand off `spatial-track.json` directly to [`motion-and-compositor`](../motion-and-compositor/SKILL.md).
