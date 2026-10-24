# Craft Cartridge: HUD Overlays, Tracked Callout Nodes & Shutter Wipes (`cartridge-hud-and-shutter-seams`)

Use this cartridge to add technical directing callouts, motion-tracked node pointers, viewfinder brackets, and graphic shutter transitions between workflow steps.

## 1. Camera Viewfinder HUD (`FRAMING` Beat)

When illustrating camera framing or composition rules:
- Draw four crisp white corner brackets (`┌ ┐ └ ┘`, `stroke-width: 4px`, `28px × 28px` arms) around the presenter's head/shoulders bounding box (`framing_hud_box` from `spatial-track.json`).
- Animate the brackets snapping inward from `1.25x` scale to `1.0x` over `0.25s` (`power4.out`) while the bold Electric Blue header `FRAMING` locks centered above the top edge.

## 2. Single-Point Motion Tracker (`TRACKING` Beat)

When illustrating motivated camera tracking during an orbiting shot:
- Attach a `22px` Electric Blue circle (`#1D63FF`) with a `3px` crisp white stroke and subtle outer pulse ring directly to the tracked `[x, y]` coordinates of a facial landmark (`cheekbone_node` in `spatial-track.json`).
- Update its `translate3d(x, y, 0)` every frame so the dot stays glued to the presenter's cheekbone as the camera orbits, paired with a clean leader line to the label `TRACKING harus punya alasan`.

## 3. Multi-Node Continuity Callouts (3-Slot UI & 4-Pillar Beats)

Use SVG leader lines (`stroke: #FFFFFF`, `stroke-width: 2.5px`, either `stroke-dasharray: 6 6` dashed or solid angled elbows) anchored by Electric Blue circular node dots (`r="7"`, `fill="#1D63FF"`, `stroke="#FFFFFF"`):
- **Monitor-to-Desk Dashed Callouts**: Connect the three reference slots inside the floating `Seedance` UI card down to three bold foreground pill labels (`KARAKTER`, `WORKSPACE`, `VOICE`) resting across the lower third. Animate `stroke-dashoffset` so the dashed lines draw downward in a `0.08s` stagger.
- **4-Node Continuity Breakdown**: Simultaneously lock four white leader lines with blue anchor dots onto:
  1. Presenter's eye (`WAJAH`)
  2. Background LED shelf (`LOKASI`)
  3. Shirt star graphic (`OUTFIT`)
  4. Presenter's shoulder/arm (`GERAKAN`)

## 4. Graphic Shutter Bar Wipes (Masking Camera Cuts)

When cutting between different studio camera setups (e.g., Side-Profile to OTS, or OTS to Standing 3/4), mask the seam with a **6-to-8-frame Graphic Shutter Wipe**:
1. Slice 4 to 6 horizontal bars alternating Electric Cobalt Blue (`#1D63FF`) and crisp White (`#FFFFFF`) across the full frame (`stagger: 0.02s`, `power3.inOut`).
2. At the midpoint frame (`100%` coverage), switch the underlying video clip and fire a 2-frame monochromatic blue tint flash (`mix-blend-mode: screen`, `opacity: 0.45 → 0`) paired with a tight whoosh/riser sound effect.
3. Retract the bars off the opposite edge to reveal the new camera setup already in motion.
