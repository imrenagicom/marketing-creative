---
name: editor
description: Render a Video Studio project's compositions into versioned video files, write SRT/VTT captions from the narration timings, and finish deliveries to a loudness target (optionally with burned-in captions) for each canvas. Use whenever compositions are built and the user wants the actual video files, captions or subtitles, a platform-ready export, a re-render after changes, or louder/quieter or broadcast-level audio. Not for changing visuals (motion-designer) or judging the result (qc-reviewer).
---

# Editor

Produce the files people will actually upload, without ever overwriting an earlier version. In the explainer recipe the HyperFrames composition already is the timeline (shots, keywords, narration on their tracks); your work is rendering it, captioning it and finishing the audio to the platform's level. Footage-based recipes will add timeline assembly here later.

Read [delivery.md](references/delivery.md) for platform targets, caption rules and versioning.

## Render

```sh
python3 <this-skill>/scripts/edit.py render <project-dir> [--canvas 9x16]
```

Each run creates the next `renders/v<N>/` with one MP4 per canvas, a render log and `manifest.json` (file hashes, composition inputs, whether GSAP was local). Rendering uses `npx --yes hyperframes@0.8.206`, which downloads that pinned package on first use; set `VIDEO_STUDIO_HYPERFRAMES` to use a locally installed binary instead. Rendering is local and free but slow; run it in the background for long videos.

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
