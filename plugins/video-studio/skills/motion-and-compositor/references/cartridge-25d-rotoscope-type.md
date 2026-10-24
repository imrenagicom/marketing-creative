# Craft Cartridge: 2.5D Depth Layering & Rotoscoped Typography (`cartridge-25d-rotoscope-type`)

Use this cartridge to construct the signature 3-plane z-depth look where giant kinetic display words sit behind the presenter's head and shoulders while secondary connector words and interactive cards sit in front.

## 1. The 4-Layer Z-Index Stack

Structure the composition stage into four explicit depth planes:

```html
<div id="stage" style="position:relative; width:1080px; height:1920px; overflow:hidden; background:#09090B;">
  <!-- Plane 1 (z-index: 10): Full-frame base video plate -->
  <video id="bg-plate" src="assets/base-video.mp4" style="position:absolute; inset:0; z-index:10;" />

  <!-- Plane 2 (z-index: 20): Midground Hero Typography (Behind Subject Head/Torso) -->
  <div id="midground-hero-type" style="position:absolute; inset:0; z-index:20;"></div>

  <!-- Plane 3 (z-index: 30): Rotoscoped Subject Torso/Head Alpha Matte -->
  <video id="subject-matte" src="assets/subject-matte.webm" style="position:absolute; inset:0; z-index:30; pointer-events:none;" />

  <!-- Plane 4 (z-index: 40): Foreground Connector Words, HUD Nodes & Social Cards -->
  <div id="foreground-overlays" style="position:absolute; inset:0; z-index:40;"></div>

  <!-- Plane 5 (z-index: 50, Optional): Isolated Gesturing Hand Matte (In Front of Cards) -->
  <video id="hand-matte" src="assets/hand-matte.webm" style="position:absolute; inset:0; z-index:50; pointer-events:none;" />
</div>
```

## 2. Typographic Hierarchy & Spatial Placement

- **Midground Hero Keywords (`z-index: 20`)**:
  - **Words**: Primary anchor nouns/verbs (`TUTORIAL`, `WORKFLOW`, `CHATGPT`, `VOICE`, `SEEDANCE`, `HYPER FRAMES`, `TIMING`, `KONTINUITAS`, `SAVE`, `FOLLOW`).
  - **Styling**: Ultra-bold condensed or geometric display sans (`font-weight: 800–900`), uppercase, Electric Cobalt Blue (`#1D63FF`–`#2563EB`) or crisp white (`#FFFFFF`), `font-size: 130px–180px` on a `1080px` wide canvas.
  - **Placement**: Positioned in the upper-chest to crown-of-head band (`top: 18%–34%`) so the bottom `20–35%` of the letterforms are naturally occluded by the presenter's hair, ears, and shoulders on Plane 3, while the upper `65–80%` remains unmistakably legible.
- **Foreground Connector Rail (`z-index: 40`)**:
  - **Words**: Conversational bridge phrases (`yang nanya`, `ayo kita bedah`, `buat`, `dan`, `video INI!`).
  - **Styling**: Medium/bold clean sans (`font-size: 44px–64px`), white (`#FFFFFF`) with subtle dark ambient shadow (`0 8px 24px rgba(0,0,0,0.45)`).
  - **Placement**: Lower-chest or desk-level foreground (`top: 52%–68%`) sitting cleanly in front of the presenter's shirt.

## 3. Hand-Occluded Foreground Cards (The Hook Technique)

In opening hooks (e.g., `00:00–00:03` stacked X/Twitter comment replies `"Tutor bang"`, `"info tutorialnya"`):
1. Stagger 3–4 dark-mode social reply cards (`border-radius: 16px`, `#121214`, `1px solid rgba(255,255,255,0.12)`) popping upward with snappy spring overshoot (`back.out(1.7)`) on Plane 4 (`z-index: 40`).
2. Render the presenter's gesturing right hand on Plane 5 (`z-index: 50`) so the hand physically passes *in front* of the floating cards as if holding or presenting them in real space.
