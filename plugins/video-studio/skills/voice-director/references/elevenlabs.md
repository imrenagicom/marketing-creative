# ElevenLabs via the CLI

Verified 2026-10-26 against the installed `elevenlabs` CLI 1.7.1 (`--help` and `--schema`) and the [elevenlabs/skills](https://github.com/elevenlabs/skills) repository. Re-check models, parameters and prices when they matter; record the date and source in `voice-config.json`.

## Why the CLI

- No SDK code to maintain; every endpoint is a subcommand.
- `--dry-run` validates a request locally without sending it (it does not return a price).
- `--schema` prints a subcommand's request and response fields; use it instead of guessing flags.
- `--format json` gives parseable output; `--no-extract` returns the full response body.
- `elevenlabs auth login` stores the key in the OS keychain; `ELEVENLABS_API_KEY` also works. Never print or commit a key. `elevenlabs auth status` checks sign-in without revealing it.

If the craft skills from elevenlabs/skills are installed (`text-to-speech`, `speech-to-text`, `music`, `sound-effects`, …), load the relevant one for model and setting advice.

## Calls this skill uses

| Need | Command | Notes |
| --- | --- | --- |
| Narration with timings | `text-to-speech convert_with_timestamps --voice-id <id> --json - --format json --no-extract` | Body: `text`, `model_id`, `language_code`, `output_format`, optional `voice_settings`, `seed`, `previous_text`, `next_text`, `pronunciation_dictionary_locators`. Response: `audio_base64`, `alignment {characters, character_start_times_seconds, character_end_times_seconds}` |
| Align a supplied recording | `forced-alignment create --file <audio> --text "<transcript>" --format json` | Response includes `words[] {text, start, end}` |
| Multi-speaker in one call | `text-to-dialogue convert_with_timestamps` | Available; the helper uses per-line TTS instead for now |
| Pronunciation | `pronunciation-dictionaries …` | Create once per project; pass locators in voice-config |
| Voice design | `text-to-voice …` | Paid; propose before running |
| Perform it yourself, change the voice | `speech-to-speech …` | Keeps the user's timing and emotion |
| Transcribe existing footage | `speech-to-text … --model-id scribe_v2` | Word timestamps; `keyterms` for names in both languages |
| Usage | `usage …`, `user …` | Reconcile actual credits against the ledger |

## Models

| Model | Use |
| --- | --- |
| `eleven_v4` | Default for narration. Highest quality and emotional range; supports audio tags such as `[whispers]`, `[laughs]`, `[excited]`, `[sarcastic]`. Only `stability` and `similarity_boost` voice settings apply; no `style`, `speed` or SSML. |
| `eleven_multilingual_v2` | Very long-form stability; no `language_code` |
| `eleven_flash_v2_5` | Low latency; not needed for produced video |

Set `language_code` to `en` or `id` from the script. For Indonesian with English terms, test the terms in a short `plan`-sized sample before a full take, and add them to a pronunciation dictionary if needed.

## Cost

Speech is billed per character; the rate depends on the model and plan. Look it up at generation time and record it as `credits_per_char` with `rate_checked`. The helper's estimate is characters × rate; reconcile with `elevenlabs usage` afterwards and record actual credits in the ledger when known.
