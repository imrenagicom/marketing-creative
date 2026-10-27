# Delivery

## Loudness targets

| `--target` | Integrated | True peak | Use |
| --- | --- | --- | --- |
| `social` (default) | −14 LUFS | −1 dBTP | TikTok, Reels, Shorts, YouTube, web |
| `podcast` | −16 LUFS | −1 dBTP | Spoken-word platforms |
| `broadcast` | −23 LUFS | −1 dBTP | EBU R128 delivery |

These are common starting targets, not placement guarantees; platforms normalize playback themselves and change policies. Check a platform's current spec when it matters and record the source.

## Canvases

Deliver each canvas the project asked for at its native size (1080×1920, 1920×1080, 1080×1350, 1080×1080), H.264 + AAC 48 kHz, `+faststart`. Never crop one canvas from another; motion-designer composes each separately.

## Captions

- Sidecar `.srt`/`.vtt` per language: always.
- Burned-in: when the user or platform wants muted-viewing support and the kinetic keywords are not enough. Keep burned captions inside the safe area, away from platform UI.
- Cue rules: one script line or sentence per cue where possible, max two lines, 0.8–6 s.
- Indonesian and English captions use their own line lengths (38 / 42 characters).

## Versioning

- `renders/v1/`, `v2/`, … are never overwritten; each has `manifest.json` with hashes and the composition inputs it came from.
- Deliveries live in `renders/v<N>/delivery/` and record measured loudness.
- When something changes upstream (new take, restyle), render a new version; keep the old one until the user says it can go.
- Generated media stays in the project directory, outside the plugin and out of git.
