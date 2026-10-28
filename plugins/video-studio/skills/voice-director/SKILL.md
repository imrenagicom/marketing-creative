---
name: voice-director
description: Cast, generate and direct narration or dialogue with ElevenLabs for a Video Studio project, or align a supplied recording, producing the narration take and word-level timestamps that time every shot. Use whenever an approved script needs a voice, the user wants a retake, a different voice or delivery, correct pronunciation of a brand or English term in Indonesian speech, or has recorded their own narration that needs timing. Runs before any visuals are timed. Not for music or sound effects.
---

# Voice Director

The narration is the clock for the whole video: shot lengths and on-screen keywords follow its word timestamps. Your job is a take that performs the acting baseline, pronounces every name correctly, and comes with timings you have checked against the script.

Read [elevenlabs.md](references/elevenlabs.md) for the CLI, models and verified details, and [performance.md](references/performance.md) for directing delivery and judging takes.

## Before any paid call

1. Confirm `script/script.json` is approved and `studio.py validate` passes.
2. Cast the voice. Use an existing voice id from the user, or list/preview voices (`elevenlabs voices …`) and propose two or three that fit the acting baseline and language. Voice design (`text-to-voice`) is a separate paid call; propose it rather than running it.
3. Write `voice/voice-config.json` (fields in [voice-config.md](references/voice-config.md); a starting point is [voice-config.example.json](assets/voice-config.example.json)). Record the credit rate you looked up and the date in `credits_per_char` and `rate_checked`.
4. Make sure an ElevenLabs cap is approved (`ledger.py show`); if not, the producer proposes one. Then run the dry run:

   ```sh
   python3 <this-skill>/scripts/voice.py plan <project-dir>
   ```

   It prints the exact requests, character count, estimate and whether the cap allows it. Nothing is sent.

## Generate

```sh
python3 <this-skill>/scripts/voice.py generate <project-dir> --note "first take"
```

- `single` mode (one narrator) sends the whole script as one continuous take for consistent prosody. `lines` mode sends one request per line with neighbouring text as context and joins them with `line_gap` seconds of silence — use it for several speakers or when only some lines change.
- The helper checks the cap, records the call before sending, saves audio and raw alignment under `voice/takes/<take>/`, converts character timings to word timings (dropping `[audio tags]`) and validates them against the script. The first take becomes `voice/words.json`; later takes wait for `select`.
- If a call fails cleanly the ledger marks it failed. If the outcome is uncertain it stays `unknown`; check the ElevenLabs history before doing anything else and never resubmit automatically.

## Supplied narration

If the user recorded the voice, align it instead of generating:

```sh
python3 <this-skill>/scripts/voice.py align <project-dir> --audio take.wav --estimate <credits>
```

The transcript must match what was said; fix the script first if they ad-libbed.

## Judge, retake, select

Listen to the take (or ask the user to). Check pace against the acting baseline, emphasis on keywords, names and English terms, and clipped starts. Retake only what needs it — prefer `lines` mode for single-line fixes — and give each retake a `--note`. Choose the take with:

```sh
python3 <this-skill>/scripts/voice.py select <project-dir> --take <take-id>
```

Selecting a new take makes shot timing stale; hand off to `shot-designer` to re-time. Report honestly whether anyone actually listened; validated timings are not a listening check.
