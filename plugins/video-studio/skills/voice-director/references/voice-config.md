# voice/voice-config.json — `video-studio/voice-config@1`

| Field | Rule |
| --- | --- |
| `model_id` | default `eleven_v4` |
| `output_format` | default `mp3_44100_128` |
| `mode` | `single` (one continuous take, one speaker) or `lines` (one request per line, joined) |
| `line_gap` | seconds of silence between lines in `lines` mode (default 0.35) |
| `credits_per_char` | the current rate you looked up |
| `rate_checked` | date and source of that rate |
| `voices{speaker}` | `{voice_id, name?, voice_settings?, seed?}` — one entry per script speaker |
| `pronunciation_dictionary_locators` | optional, applied to every request |

`voice_settings` for `eleven_v4`: `stability` (lower = more expressive, higher = more consistent) and `similarity_boost`. Keep `seed` fixed while comparing retakes so changes come from your edits, not randomness.

Speakers are the script's `speaker` ids, which come from the direction lock's characters, so casting stays tied to acting baselines.
