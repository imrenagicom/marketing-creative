# Project contract

Every Video Studio skill reads and writes the same JSON files inside one project directory. `studio.py validate` checks all of them and their cross-references. A complete synthetic example lives in [assets/example-project](../assets/example-project/project.json).

```text
<project>/
  project.json            producer
  direction/options.json  director (drafts, free-form within the options shape)
  direction/lock.json     director, after the user approves
  script/script.json      scriptwriter
  voice/voice-config.json voice-director
  voice/takes/<take>/     voice-director (audio, raw provider response)
  voice/words.json        voice-director (selected take's word timings)
  shots/shots.json        shot-designer
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
| `recipe` | `explainer` (v1) |
| `language` | `en`, `id`, or `null` until the user chooses |
| `formats[]` | `{id, width, height}`; ids `16x9`, `9x16`, `4x5`, `1x1` |
| `fps` | 24, 25, 30 or 60 |

## direction/lock.json — `video-studio/direction-lock@1`

| Field | Rule |
| --- | --- |
| `version` | integer, bumped on every approved change |
| `logline` | one sentence |
| `hook` | `{pattern, opening}` — pattern from the director's hook library, opening = what happens in the first 2 s |
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

`keywords` are the words that appear on screen as they are spoken; each must occur in `text`. `delivery` carries acting notes and may include ElevenLabs v4 audio tags such as `[excited]`; tags are spoken direction, not on-screen text.

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
| camera fields | camera shots: `framing`, `movement`, `action`, `light_source`, `sound` |
| `start`, `end` | seconds, written by `shots.py time`; contiguous, covering the narration |

## style.json — `video-studio/style@1`

Visual tokens for compositions: `colors` (`background`, `surface`, `text`, `accent`, `muted` as `#RRGGBB`), `fonts` (`display`, `body` family names and optional local font files), `radius`, `motion` (`ease`, `entrance` seconds). Keep the subject/background contrast rule from the direction lock.

## ledger.json — `video-studio/ledger@1`

`caps{provider: {credits, approved_by, approved_at, basis}}` and `entries[]` with `{id, provider, operation, estimate, actual, status, request_sha256, outputs[], at}`. Status is `planned`, `submitted`, `succeeded`, `failed` or `unknown`.
