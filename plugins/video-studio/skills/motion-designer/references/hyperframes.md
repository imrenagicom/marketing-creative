# HyperFrames runtime

HyperFrames (`hyperframes` on npm, Apache-2.0, HeyGen) turns HTML + a paused GSAP timeline into video. It is not bundled; install it per machine or run it with `npx`. Verified 2026-10-27 with `hyperframes@0.8.206` (Node ≥ 22, FFmpeg) by linting and rendering the example project to 1080×1920 and 1920×1080 MP4 with narration. Check `npx hyperframes --help` before relying on other flags; versions move quickly.

## Composition contract the generator follows

- A root element `#root` with `data-composition-id="main"`, `data-start="0"`, `data-width`, `data-height`, `data-duration`.
- Timed elements carry `class="clip"`, `data-start`, `data-duration` and `data-track-index` (scenes on track 2, narration on track 10). The runtime controls their visibility; animate inner elements, never the clip's own visibility.
- One paused GSAP timeline registered as `window.__timelines["main"]`, with absolute times in seconds.
- Hidden start states come from `fromTo` tweens (which render their start state immediately), not from CSS that would fight GSAP transforms.
- Audio: `<audio id="narration" src="assets/…" data-start="0" data-duration="…" data-track-index="10" data-volume="1">`. The runtime plays and mixes it; never call `play()` or seek media yourself.
- No randomness, clocks or network-loaded required media at render time. Local fonts are safest (`hyperframes-localize-fonts` can vendor web fonts).

## Commands

Run from the canvas directory (`compositions/<canvas>/`):

| Purpose | Command |
| --- | --- |
| Lint | `npx hyperframes lint . --json` |
| Live preview | `npx hyperframes preview` (managed in non-interactive shells; `--stop` to end) |
| Render | `npx hyperframes render -o <project>/renders/v<N>/<canvas>.mp4` |
| Measure audio | `npx hyperframes audio <file>` |

Rendering is local and free but takes time (about 30 s for a 20 s 1080p clip on an Apple Silicon laptop). Never run `hyperframes publish` without the user asking; it uploads the project.

## Known lint warnings on bundled output

`timeline_track_too_dense` and `nested_structure_needs_subcomposition` suggest moving each scene into its own sub-composition file. They do not block rendering. A future generator version may emit sub-compositions; until then, report them as known warnings rather than errors.
