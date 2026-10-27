---
name: motion-designer
description: Build the motion-graphics picture for a Video Studio project as HyperFrames compositions — kinetic keywords that land on the spoken word, step lists, UI cards, counters, images and end cards, composed separately for each canvas (9:16, 16:9, 4:5, 1:1) and synced to the narration. Use whenever a project has timed shots and needs its visuals built, restyled or adapted to another aspect ratio, or the user wants to tweak animation, colours or typography. Not for rendering, captions or loudness (editor).
---

# Motion Designer

Turn the timed shot list into compositions where every visual change is cued by the narration. You own the look (style tokens), the per-canvas layouts and the animation; HyperFrames owns seeking, timing of clips, media playback and rendering.

## Inputs

`shots/shots.json` timed by `shots.py time` against the selected take, `script/script.json` keywords, `voice/words.json`, and `style.json` (create it if missing — see [composition-craft.md](references/composition-craft.md)). Read [hyperframes.md](references/hyperframes.md) for the runtime contract and verified commands before changing generated HTML.

## Build

```sh
node <this-skill>/scripts/compose.mjs <project-dir> --gsap <path/to/gsap.min.js>
```

- Writes `compositions/<canvas>/index.html`, copies the narration and image assets beside it, and records hashes in `build.json`.
- Each canvas is laid out for its own dimensions and safe areas (centered stack for vertical and square, left-aligned for wide); nothing is cropped from another canvas.
- Every graphic shot shows its lines' keywords as they are spoken; `kinetic` shots reveal the whole line word by word with keywords in the accent colour. Cue times come from the word timestamps, never from estimates.
- Pass a local GSAP 3.14.2 file with `--gsap` for reproducible renders (`npm i gsap@3.14.2`). Without it the pinned CDN URL is used; treat that as a development fallback and say so.
- The generator refuses to run when shots are untimed, timed against another take, or include camera shots (footage arrives with later recipes).

## Edits and rebuilds

Hand edits to generated HTML are allowed, but the next build will refuse to overwrite an edited file. Reconcile the edit — usually by moving it into `style.json`, the shot's `visual` fields, or a project-local generator — then rebuild with `--force`. Never use `--force` just to get past the check.

Need a scene the bundled modes cannot express (product animation, chart, 3D)? Write a project-local generator that emits the same composition contract, and keep it in the project, not the plugin.

## Verify

1. `npx hyperframes@0.8.206 lint <canvas-dir> --json` — no errors. The bundled output currently draws "sub-composition" and "dense track" warnings; they are structural suggestions, not failures.
2. Preview (`npx hyperframes preview`) or render a draft and look at the boundaries and midpoints of every shot, for every canvas: text overflow, keyword timing, contrast, safe areas.
3. Hand off to `editor` for final renders, captions and loudness.

Report which canvases were built, linted, previewed and actually watched; generated HTML is not proof that the video looks right.
