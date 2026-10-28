---
name: sound-designer
description: Design and generate the sound of a Video Studio film — per-shot sound effects, looping ambience beds for each location and optional music — with the ElevenLabs CLI under the project's approved budget, placed on the shot timeline with levels the editor mixes under dialogue. Use whenever a cinematic project's takes are selected and need sound, the user asks for sound effects, ambience, atmosphere, foley or a score, or generated take audio should be replaced or supplemented. Not for narration or dialogue voices (voice-director).
---

# Sound Designer

Sound sells what the picture shows: footsteps on gravel, rotor hum, the room tone that makes cuts feel like one place. Start from the shot list's `sound` fields and the audio policy, generate only what the film needs, and leave intelligible dialogue on top.

Read [sound-craft.md](references/sound-craft.md).

## Configure and plan

Write `sound/sound-config.json` (start from [sound-config.example.json](assets/sound-config.example.json)) with the current credit rates you looked up and the date, and whether to keep the generated takes' own audio (`use_take_audio`). Then:

```sh
python3 <this-skill>/scripts/sound.py plan <project-dir>
```

The dry run writes `sound/plan.json`: one sound-effect cue per shot with a `sound` field (up to 30 s), one looping ambience bed per bible environment, and a music cue only when the audio policy asks for music. It prints each cue's estimate and whether the ElevenLabs cap allows the total. Edit cue prompts in the shot list or bible and re-plan rather than hand-editing requests.

## Generate

```sh
python3 <this-skill>/scripts/sound.py generate <project-dir> [--cue sfx-S03]
```

Each cue checks the cap, is recorded before it is sent, and lands in `sound/<kind>/<cue>-v<N>.mp3` (earlier versions are kept). Placed cues go into `sound/cues.json` with start, duration, loop and gain. A refused call is marked failed; an empty or missing output stays unknown and counted — check the ElevenLabs history before trying again.

Adjust levels with `sound.py gain --cue amb-rooftop --db -20`. Listen to the cues against the selected clips before handing off; say plainly if nobody has listened.

## Handoff

`editor assemble` mixes dialogue or narration, the placed cues (ducking ambience and music under speech) and, if `use_take_audio` is true, the takes' own sound.
