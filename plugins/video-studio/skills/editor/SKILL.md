---
name: editor
description: Render a Video Studio project's compositions, or assemble a film's selected footage clips with its dialogue and sound mix, into versioned video files; write SRT/VTT captions from speech timings; and finish deliveries to a loudness target (optionally with burned-in captions) for each canvas. Use whenever compositions are built and the user wants the actual video files, captions or subtitles, a platform-ready export, a re-render after changes, or louder/quieter or broadcast-level audio. Not for changing visuals (motion-designer) or judging the result (qc-reviewer).
---

# Editor

Produce the files people will actually upload, without ever overwriting an earlier version. In the explainer recipe the HyperFrames composition already is the timeline, so you render it. In the cinematic recipe you assemble the timeline yourself from the selected take clips and the sound plan.

Read [delivery.md](references/delivery.md) for platform targets, caption rules and versioning.

## Render

```sh
python3 <this-skill>/scripts/edit.py render <project-dir> [--canvas 9x16]
```

Each run creates the next `renders/v<N>/` with one MP4 per canvas, a render log and `manifest.json` (file hashes, composition inputs, whether GSAP was local). Rendering uses `npx --yes hyperframes@0.8.206`, which downloads that pinned package on first use; set `VIDEO_STUDIO_HYPERFRAMES` to use a locally installed binary instead. Rendering is local and free but slow; run it in the background for long videos.

## Assemble footage (cinematic)

```sh
python3 <this-skill>/scripts/edit.py assemble <project-dir> [--canvas 16x9]
```

For each canvas it writes `timeline.json` from the shot plan and the selected clip per shot, then renders `renders/v<N>/<canvas>.mp4`: each clip is scaled to cover the canvas, centre-cropped, trimmed (or held on its last frame) to the planned shot length, and `fade` transitions fade in. Audio: dialogue or narration on top, placed sound cues (looping beds repeat), ambience and music ducked under speech with a sidechain compressor, and the takes' own audio only when `use_take_audio` is set. It refuses shots without a selected clip — select after dailies first.

Dialogue and voice-over audio is placed from the film's start, so generate it on the film's timeline (voice-director lines mode with gaps, then time shots to the words). Centre-crop can cut important action on a canvas the take was not composed for; assemble each canvas from its own takes.

## Captions

```sh
python3 <this-skill>/scripts/edit.py captions <project-dir>
```

Writes `captions/<lang>.srt` and `.vtt` from `voice/words.json`: cues follow script lines and sentence ends, at most two lines, wrapped to the language's line length (42 characters English, 38 Indonesian), 0.8–6 s each. Captions transcribe what is spoken; `[audio tags]` never appear.

## Finish

```sh
python3 <this-skill>/scripts/edit.py finish <project-dir> [--version N] [--target social|podcast|broadcast] [--burn-captions]
```

Two-pass loudness normalization into `renders/v<N>/delivery/`, re-measured afterwards and recorded in the manifest. Video is stream-copied unless captions are burned in. Burn-in needs an ffmpeg built with libass; the helper checks first and tells you if it is missing — deliver the sidecar captions instead rather than faking it.

Default to sidecar captions plus the kinetic keywords already on screen; burn in full captions when the platform or user asks (many social viewers watch muted).

## Handoff

Hand the version number to `qc-reviewer`. Tell the user where the deliveries are, which canvases and targets were produced, and that nobody has watched them yet unless someone has.
