# Project contract

Every Video Studio skill reads and writes the same JSON files inside one project directory. `studio.py validate` checks all of them and their cross-references. Synthetic examples: the explainer [assets/example-project](../assets/example-project/project.json) and the cinematic [assets/example-cinematic](../assets/example-cinematic/project.json).

```text
<project>/
  project.json            producer
  direction/options.json  director (drafts, free-form within the options shape)
  direction/lock.json     director, after the user approves
  script/script.json      scriptwriter
  voice/voice-config.json voice-director
  voice/takes/<take>/     voice-director (audio, raw provider response)
  voice/words.json        voice-director (selected take's word timings)
  bible/bible.json        continuity-bible (footage recipes)
  bible/images/           continuity-bible (reference images)
  shots/shots.json        shot-designer
  keyframes/              keyframe-generator
  takes/takes.json        ai-video-generator
  takes/<take>/           ai-video-generator (raw take, split shot clips)
  sound/cues.json         sound-designer
  timeline.json           editor (footage assembly)
  style.json              motion-designer (visual tokens)
  compositions/<canvas>/  motion-designer (HyperFrames input)
  renders/v<N>/           editor
  qc/report.json          qc-reviewer
  ledger.json             producer (caps and paid calls)
  .history/               previous versions of overwritten contract files
```

IDs are short slugs (`B1`, `L03`, `S04`) and never change once downstream files use them.

## project.json — `video-studio/project@1`

| Field | Rule |
| --- | --- |
| `id`, `title` | slug and human title |
| `recipe` | `explainer` or `cinematic` |
| `language` | `en`, `id`, or `null` until the user chooses |
| `formats[]` | `{id, width, height}`; ids `16x9`, `9x16`, `4x5`, `1x1` |
| `fps` | 24, 25, 30 or 60 |

## direction/lock.json — `video-studio/direction-lock@1`

| Field | Rule |
| --- | --- |
| `version` | integer, bumped on every approved change |
| `logline` | one sentence |
| `hook` | `{pattern, opening}` — pattern from the director's hook library, opening = what happens in the first 2 s |
| `structure` | the story shape, for example problem → promise → steps → CTA |
| `beats[]` | `{id, purpose, summary, seconds?}` in story order |
| `characters[]` | `{id, role, acting_baseline, register?}`; the narrator is a character |
| `visual_plan` | how the picture carries the argument (layouts, motion vocabulary, contrast rule) |
| `audio_policy` | `{voice, music, sfx}` decisions, including "none" |
| `approved` | `{by: "user", at}` — required; the lock is not valid without it |

## script/script.json — `video-studio/script@1`

| Field | Rule |
| --- | --- |
| `language` | must equal `project.language` |
| `register` | en: `casual`/`conversational`/`formal`; id: `casual`/`friendly`/`formal` |
| `lines[]` | `{id, beat, speaker, text, delivery?, keywords[], on_screen?}` |

`keywords` are the words that appear on screen as they are spoken; each must occur in `text`. `delivery` carries acting notes for humans. ElevenLabs v4 audio tags such as `[excited]` may lead `text`; they are sent to speech generation as direction, are never spoken or shown, and are dropped from word timings.

## voice/words.json — `video-studio/words@1`

| Field | Rule |
| --- | --- |
| `audio` | project-relative path of the selected narration |
| `duration` | seconds |
| `language` | equals the script language |
| `source` | `elevenlabs-tts` or `forced-alignment` |
| `words[]` | `{text, start, end, line}` in time order; `line` is a script line id |

## shots/shots.json — `video-studio/shots@1`

| Field | Rule |
| --- | --- |
| `shots[]` | in screen order |
| `id`, `beat`, `lines[]` | each script line belongs to at most one shot |
| `kind` | `graphic` (motion design) or `camera` (footage; later recipes) |
| `motivation` | why this picture appears now — what the narration needs shown |
| `transition` | into this shot: `cut`, `wipe`, `fade`, `push` |
| `visual` | graphic shots: `{mode, …}` with mode `title`, `kinetic`, `steps`, `ui-card`, `stat`, `image`, `end-card` |
| camera fields | camera shots: `framing`, `movement`, `action`, `light_source`, `sound`, `refs[]` (bible ids), `screen_direction` (`left-to-right`, `right-to-left`, `toward-camera`, `away-from-camera`, `neutral`), `keyframes {start, end}` |
| `duration` | seconds; required for footage shots when there is no narration |
| `take` | take id; shots sharing a take are consecutive and generated together |
| `max_take_seconds` | top level; the chosen model's maximum duration (default 15) |
| `start`, `end` | seconds, written by `shots.py time` from word timestamps or durations; contiguous |

## bible/bible.json — `video-studio/bible@1`

| Field | Rule |
| --- | --- |
| `references[]` | `{id, role, name, description, preserve[], images[], light_sources[]?, character?, higgsfield_element_id?}`; role `character`, `environment`, `prop`, `vehicle` or `style` |
| `preserve[]` | the features that must never change (face shape, hair, garment details, geometry) |
| `light_sources[]` | required for environments: visible, motivated sources the model can follow |
| `locks[]` | `{kind, text}` with kind `position`, `identity`, `screen-direction`, `wardrobe`, `geography` or `period` |
| `capture` | `{look, motion_rules[]}` — the declared camera or device look |
| `audio_policy` | `{music, dialogue, sfx}` |

## takes/takes.json — `video-studio/takes@1`

| Field | Rule |
| --- | --- |
| `takes[]` | `{id, canvas, shots[], provider, model, duration, aspect_ratio, prompt, medias[], approval, job_id, status, output, clips{shot: path}}` |
| `shots[]` | consecutive shots in screen order |
| `status` | `draft`, `approved`, `submitted`, `succeeded`, `failed`, `unknown`, `selected`, `rejected` |
| `approval` | `{fingerprint, ledger_entry, estimate}`; required before submission |

Only one selected take may cover a shot on a canvas.

## sound/cues.json — `video-studio/sound@1`

`cues[] {id, kind (sfx, ambience, music), shot?, start, duration, file, gain_db, loop?}` placed on the project timeline, plus `music_policy` and `ducking` settings used by the editor's mix.

## style.json — `video-studio/style@1`

Visual tokens for compositions: `colors` (`background`, `surface`, `text`, `accent`, `muted` as `#RRGGBB`), `fonts` (`display`, `body` family names and optional local font files), `radius`, `motion` (`ease`, `entrance` seconds). Keep the subject/background contrast rule from the direction lock.

## ledger.json — `video-studio/ledger@1`

`caps{provider: {credits, approved_by, approved_at, basis}}` and `entries[]` with `{id, provider, operation, estimate, actual, status, request_sha256, outputs[], at}`. Status is `planned`, `submitted`, `succeeded`, `failed` or `unknown`.
