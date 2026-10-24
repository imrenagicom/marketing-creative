# Craft Cartridge: Multi-Angle Studio Presenter (`cartridge-multi-angle-presenter`)

Use this cartridge when directing an AI-generated or hybrid presenter tutorial/explainer (`9:16` or `16:9`) inside a consistent studio workspace.

## 1. The 3-Reference Consistency Anchor

Pass three synchronized references into every shot generation (such as Seedance via Wizstar AI):
- **`@Image1` — `Karakter` (Character Sheet)**: Locks facial features, hairstyle, skin tone, and exact layered wardrobe (e.g., electric cobalt-blue graphic tee over black long-sleeve base layer, black trousers, white clogs).
- **`@Image2` — `Workspace` (Environment Plate)**: Locks the 3D studio geography—street-art wall mural, warm amber LED strip shelving, dual monitors (one ultrawide landscape + one portrait vertical monitor), glowing amber PC tower, and window blinds.
- **`@Audio1` — `Voice` (ElevenLabs v4 Stem)**: Drives exact lip-sync, breath pauses, and facial micro-expressions.

## 2. The 6-Camera Virtual Room Setup Map

Eliminate static "avatar fatigue" by cutting across six distinct, physically consistent camera angles inside the same room:
1. **Setup 1 — Frontal Medium Close-Up (MCU)** (`00:00–00:04`, `00:32–00:34`, `00:40–00:52`):
   - Eye-level direct contact at desk; presenter gestures with right hand in front of torso (leaving clear negative space above/behind shoulders for rotoscoped hero text and in front of chest for floating comment cards).
2. **Setup 2 — Wide Full-Body Standing Shot** (`00:04–00:08`):
   - Presenter stands beside the office chair in full body, gesturing toward the dual-monitor desk setup to establish room geography and full outfit continuity.
3. **Setup 3 — Side-Profile Medium Shot (Left-to-Right)** (`00:08–00:17`):
   - Presenter seated in profile typing on the mechanical keyboard and pointing toward the portrait and landscape monitors.
4. **Setup 4 — Over-the-Shoulder (OTS) Monitor Focus Shot** (`00:17–00:24`, `00:30–00:31`):
   - Camera looks over the presenter's right shoulder and pushes smoothly toward the ultrawide monitor screen, creating a clean planar surface for 3D corner-pinned UI cards.
5. **Setup 5 — Dynamic Standing Three-Quarter Shot** (`00:25–00:30`):
   - Presenter stands in front of the desk turning from the workspace back toward the lens with energetic hand movement.
6. **Setup 6 — Low-Angle Orbiting MCU** (`00:34–00:39`):
   - Subtle low-angle push and lateral orbit around the presenter, creating strong parallax across the warm amber background shelves to demonstrate motivated camera tracking.

## 3. Cut & Action Continuity Rules

- **Match Action Across Cuts (`Gerakan`)**: If the presenter begins turning toward the monitor at the end of Setup 2, Setup 3 or Setup 4 must open with that turn completing or the hand arriving at the keyboard/screen.
- **Leave Intentional Graphic Zones**:
  - In Frontal and 3/4 shots, keep `20–25%` headroom above the crown of the head so giant behind-the-head typography (`TUTORIAL`, `WORKFLOW`, `SAVE`, `FOLLOW`) remains readable when occluded by hair and shoulders.
  - In OTS and Side-Profile shots, keep the physical monitor bezels cleanly visible inside the frame so [`video-scene-tracker`](../../video-scene-tracker/SKILL.md) can extract 4-corner planar coordinates.
