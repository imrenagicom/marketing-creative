# Craft Cartridge: 3D Planar-Tracked Dark UI Cards (`cartridge-3d-planar-ui-cards`)

Use this cartridge when showcasing software tools, AI prompts, audio generation, or multi-reference workflows inside a video without showing tiny, unreadable raw screen captures.

## 1. Design Principle: Simplified High-Contrast Mockups Over Raw Captures

Raw desktop screenshots fail on vertical (`9:16`) and social feeds because 12px UI chrome turns into illegible gray noise. Always construct **purpose-built, simplified dark-mode UI cards** (`#141418` to `#18181B`, `border: 1.5px solid rgba(255,255,255,0.14)`, `border-radius: 20px`, `box-shadow: 0 24px 60px rgba(0,0,0,0.65)`) containing only the 3–4 visual elements that tell the story of that beat.

## 2. Three Canonical Card Archetypes

### Archetype A: The Prompt & Checklist Card (`ChatGPT` Step)
- **Visual Structure**:
  - Header bar with tool icon + bold title (`ChatGPT`).
  - User prompt bubble in high-contrast text: `"Bikinin konsep, naskah, dan prompt video"`.
  - Three sequential status rows that animate from spinner to Electric Blue checkmark (`✓ Konsep`, `✓ Naskah`, `✓ Prompt`) synced to the voiceover list.

### Archetype B: The Voice Waveform Card (`ElevenLabs v4` Step)
- **Visual Structure**:
  - Vertical dark panel mapped onto a portrait monitor (`ElevenLabs Eleven v4`).
  - Animated row of 16–24 vertical pill bars (`#1D63FF` to `#60A5FA`) oscillating to the actual voiceover amplitude.
  - Status pill transitioning from `"Generating voice..."` to `"✓ Voice ready"` with a subtle blue glow pulse.

### Archetype C: The Multi-Reference Slot Card (`Seedance via Wizstar AI` Step)
- **Visual Structure**:
  - Wide floating dark window over the ultrawide monitor.
  - Three square reference cards side-by-side (`border-radius: 14px`, `#222228`):
    1. `Karakter` (thumbnail of `@Image1` presenter portrait)
    2. `Workspace` (thumbnail of `@Image2` studio room)
    3. `Voice` (blue audio waveform icon)
  - Full-width or bottom-right Electric Blue CTA pill button (`Generate`) that depresses and flashes on click.

## 3. 3D Perspective Corner-Pinning (`CSS perspective` & `matrix3d`)

Read the monitor quad coordinates from `spatial-track.json` ([`video-scene-tracker`](../../video-scene-tracker/SKILL.md)) and apply matching 3D perspective so the card sits locked to (or hovering `12px` in front of) the physical monitor screen:
- Wrap the card container in `perspective: 1200px; transform-style: preserve-3d;`.
- For angled side-profile or over-the-shoulder monitors, apply the tracked `rotateY(...) rotateX(...) rotateZ(...)` or exact 4-corner homography `matrix3d(...)` and interpolate across camera push-ins so the card scales and tilts in lockstep with the physical bezel.
