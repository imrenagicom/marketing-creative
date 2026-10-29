# Contact-sheet boards

A board renders many low-resolution previews in ONE `gemini-api image` call, which the helpers then crop on your machine. Use one before paying for full keyframes or bible images: preview every camera shot of a sequence, or compare two to twelve design options for one character, location or prop. The idea and cropping workflow come from the marketing-images plugin's `marketing-image-board`. This version shares Video Studio's project files, prompts and `gemini-image` cap.

## When to use one

- **Keyframes:** `keyframes.py board` puts the chosen camera shots (default: all, at most 12) on one sheet for a canvas, in screen order. Use it to check composition, staging, screen direction and continuity across a sequence before the per-shot spend.
- **Bible looks:** `bible.py board --ref <id> --variant "…" --variant "…"` shows design options for one reference. Each option must keep the reference's `preserve` list. Use it when the user hasn't picked a look yet.

Skip a board when the user already supplied or approved the images, or when only one or two frames are needed.

## Commands

```sh
python3 <keyframe-generator>/scripts/keyframes.py board <project> --canvas 16x9 [--shot S01 …] [--grid 2x3] [--image-size 2K]
python3 <keyframe-generator>/scripts/keyframes.py board-preview <project> --board keyframes/boards/16x9/board-v1
python3 <keyframe-generator>/scripts/keyframes.py board-generate <project> --board keyframes/boards/16x9/board-v1
python3 <keyframe-generator>/scripts/keyframes.py board-split <project> --board keyframes/boards/16x9/board-v1 --inset 12
```

`bible.py` has the same `board-preview`, `board-generate` and `board-split` commands. Its boards live in `bible/boards/<ref>/board-vN/`.

- `board` writes `board.json`. It records the cells with their stable IDs (`<shot>-<frame>` or `<ref>-<n>`), the grid, the sheet's aspect ratio, the exact request and its USD estimate. Nothing is sent. By default the grid keeps every cell close to the canvas or sheet ratio. `--grid ROWSxCOLUMNS` overrides it, and unused trailing cells are left grey.
- `board-generate` checks the `gemini-image` cap, records one ledger entry, runs the CLI once and stores `board.png` with provenance. It then splits the sheet into `tiles-v1/<cell>.png`. A board that was already sent is never sent again; plan a new one.
- `board-split` re-crops the stored sheet into a new `tiles-vN/`, with an inset to trim gutters. Splitting needs FFmpeg and never resamples.

## Rules

- **Look at the whole sheet before trusting the tiles.** Splitting assumes the model followed the grid. If cells are merged, shifted or labelled, re-split with an inset or plan a new board deliberately. Never regenerate one in a loop.
- **Tiles are previews, not deliverables.** They are never written to `shots.json` or the bible's `images`, never used as a video take's start frame, and never delivered. More cells mean fewer pixels per cell, and `board-split` reports the actual tile size.
- **Carry the selection forward explicitly.** For keyframes, pass the tiles folder to the next plan: `keyframes.py plan <project> --canvas 16x9 --provider gemini --tiles keyframes/boards/16x9/board-v1/tiles-v1`. Each shot whose `<shot>-<frame>.png` exists gets that tile attached as a composition reference. For the bible, pass the chosen option: `bible.py sheets <project> --provider gemini --tile rooftop=bible/boards/rooftop/board-v1/tiles-v1/rooftop-2.png`. Identity and facts still come from the bible's references, not from the tile.
- **One board is one image request.** Its estimate is a single image at the sheet size, the same as a keyframe of that size, plus input tokens for the attached references.
