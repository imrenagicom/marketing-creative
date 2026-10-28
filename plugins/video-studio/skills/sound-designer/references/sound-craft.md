# Sound craft

## Layers

| Layer | Source | Level (start) | Notes |
| --- | --- | --- | --- |
| Dialogue / narration | voice-director | 0 dB | Always intelligible; everything else ducks under it |
| Sound effects | one cue per shot from `shot.sound` | −6 dB | Sync-critical sounds (clicks, impacts) should land on the visible action |
| Ambience | one looping bed per environment | −18 dB | Continuous across cuts in the same place; this is what makes separate takes feel like one location |
| Music | only when the audio policy asks | −16 dB | Ducked under speech; explicit "none" is respected |
| Take audio | generated with the video | off by default | Often contains unwanted music or mismatched sound; keep it only after listening |

## Writing sound prompts (in the shot list)

Describe what is heard and how it sounds: "boots crunching on wet gravel, close, quick rhythm" beats "footsteps". Include distance (close, distant), space (small room, open rooftop) and material. Interior and exterior shots should sound enclosed or open accordingly.

Special moments:

- **Slow motion / bullet time**: muffled, stretched environment, low drone; full sound returns sharply when speed returns.
- **Cuts between places**: change the ambience bed exactly on the cut.
- **Silence**: a deliberate drop to near-silence before an impact is stronger than more sound.

## ElevenLabs calls

Verified 2026-10-27 with the CLI (`--dry-run`):

| Cue | Command | Body |
| --- | --- | --- |
| Sound effect / ambience | `text-to-sound-effects convert --json - -o <file>` | `text`, `duration_seconds` (0.5–30), `loop`, `prompt_influence`, optional `model_id` |
| Music | `music compose --json - -o <file>` | `prompt` + `music_length_ms` + `model_id` (`music_v2_5`) + `force_instrumental`, or a `composition_plan` with sections |

For music that follows the beats, a composition plan (sections with durations matching the beats) gives more control than one prompt; `music compose_detailed` returns the plan with the audio. Video-to-music (`music video_to_music`) can score the assembled cut with separate music and effects stems.

Credits: sound effects and music are billed by length; record the current rates in `sound-config.json` and reconcile with `elevenlabs usage`.
