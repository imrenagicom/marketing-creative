---
name: visual-bible-and-refs
description: Establish the visual bible, complementary color contrast, practical lighting anchors in location plates, and strict multi-reference identity locks (@Image1, @Image2, @Image3) across the 4 Pillars of Continuity.
---

# Visual Bible and References (`visual-bible-and-refs`)

`visual-bible-and-refs` is **Stage 3** of the `video-studio` pipeline. Multi-shot AI video collapses into generic "slop" when character identity drifts, lighting feels flat because the video model has to guess where light comes from, or foreground typography blends into a muddy background. This skill locks the visual system and reference sheets before any video credits are spent.

## 1. Complementary Two-Tone Chromatic Contrast

Design every scene around high-separation complementary contrast so the subject and motion graphics pop immediately without heavy drop shadows or dark scrims:
- **Example Archetype (`Electric Cobalt Blue vs. Warm Amber`)**:
  - **Primary Accent & Subject Wardrobe (`#1D63FF` – `#2563EB`)**: Worn by the presenter or hero subject and echoed across primary kinetic keywords, UI accent buttons, tracker dots, and shutter wipe flashes.
  - **Environment & Practical Lighting (`#D97706` – `#F59E0B`)**: Warm tungsten/amber background environment (warm LED strip shelving, glowing amber PC cooling fans, golden lamp glow, warm sunlight through blinds, or orange-red moon/lava cracks).
- Document the exact hex range and role assignment in `visual-bible.md`.

## 2. Practical Lighting Anchors in Location Plates

Never feed an unlit or ambiguously lit environment into a generative video model:
- **Bake Visible Light Sources into `@Image` Location References**: When generating or selecting a location reference image (a studio workspace, a kitchen, a city street, or a wasteland), explicitly include practical light sources inside the frame—such as a warm table lamp with a golden glow, amber LED shelf strips, window blinds casting directional sunbeams, or glowing ground fissures.
- **Reference the Light Source in Every Shot Prompt**: State where the primary key light, rim light, and localized interactive lights (e.g., red-blue police strobes, white-blue underside thrusters, orange magical staff glow) originate and how they reflect off skin, clothing, glass, and asphalt.

## 3. Master Reference Role & Position Locks (`@Image1..N`)

Assign every reference asset an immutable `@Image` tag and role contract:
- **Presenter / Studio Workflow (3-Reference Lock)**:
  - `@Image1` — **Character Reference (`Karakter`)**: Exact facial features, hair, proportions, and wardrobe (front, 3/4, and profile consistency).
  - `@Image2` — **Workspace / Environment Reference (`Workspace`)**: Exact room layout, wall murals, shelving, monitors, and practical lighting geometry.
  - `@Audio1` — **Voice Input (`Voice`)**: The locked voiceover stem driving lip-sync and facial performance.
- **Multi-Character / Vehicle Action Workflow**:
  - `@Image1` — **Primary Subject / Driver / Fighter A**: Exact anatomy, costume, signature props, and physical material behavior (e.g., rigid carved pumpkin head with muscular human body in brown suit; or elastic gummy ghost fabric silhouette).
  - `@Image2` — **Secondary Subject / Passenger / Fighter B**: Exact identity, outfit, and power/interaction rules.
  - `@Image3` — **Hero Vehicle / Prop**: Exact geometry, panel color, roof glass, wheel layout, and functional mechanisms (e.g., four underside thrusters, no wings).
  - **Position Lock**: Explicitly lock spatial roles across the entire film (e.g., *"@Image1 ALWAYS drives; @Image2 ALWAYS sits in the front passenger seat; never swap seats, duplicate characters, or exchange powers"*).

## 4. The 4 Pillars of Continuity (`Kontinuitas`)

Every reference sheet and scene bible must define verifiable anchors across four pillars:
1. **`Wajah` (Face & Head Identity)**: Exact facial structure, eye shape, hair texture, or non-human head geometry across frontal, profile, and 3/4 angles.
2. **`Outfit` (Wardrobe & Material Specs)**: Layer-by-layer clothing breakdown (e.g., royal blue oversized tee with cream/yellow flame-and-star graphic over black long-sleeve base layer, black trousers, white clogs) plus cloth physics rules.
3. **`Lokasi` (3D Spatial Geography)**: A consistent 3D mental map of the environment (where the windows, wall mural, shelves, and dual monitors—or horizon landmarks and moon direction—sit relative to the subject) so cutting from a wide shot to an over-the-shoulder or side-profile shot preserves physical geography.
4. **`Gerakan` (Movement & Physics Signature)**: How the subject's body, clothing, and props react to inertia, gravity, and action across cuts.

## Output Handoff

Pause at **Checkpoint 2** to review `visual-bible.md` and the static `@Image` reference sheets. Once approved, hand off to [`generative-shot-director`](../generative-shot-director/SKILL.md) or [`motion-and-compositor`](../motion-and-compositor/SKILL.md).
