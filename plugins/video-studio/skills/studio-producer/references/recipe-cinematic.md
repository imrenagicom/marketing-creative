# Recipe: cinematic

A short film, brand film or story-led ad built from AI-generated footage. The picture carries the story; dialogue and voice-over are optional. Continuity across shots is the main technical risk, so the continuity bible comes before any paid generation.

## Pipeline

direction → continuity bible → shots (camera, explicit durations) → keyframes → takes (Higgsfield or Gemini API video, approved per request) → dailies QC → retakes → sound design → assembly and mix → finish → final QC.

| Stage | Skill | Produces |
| --- | --- | --- |
| Reference study (optional) | `reference-analyst` | `references/<name>/analysis.json` and a techniques report |
| Direction | `director` | `direction/lock.json` |
| Continuity | `continuity-bible` | `bible/bible.json`, reference images, Higgsfield elements |
| Shots | `shot-designer` | camera shots with framing, movement, action, light, sound, refs, durations, take grouping |
| Dialogue (optional) | `scriptwriter`, `voice-director` | script and voice stems before takes, so takes can lip-sync |
| Keyframes | `keyframe-generator` | start/end frames per shot (image cap) |
| Takes | `ai-video-generator` | `takes/takes.json`, raw takes split into shot clips |
| Dailies | `qc-reviewer dailies` | contact sheets, pillar verdicts, retake list |
| Sound | `sound-designer` | `sound/cues.json` and audio files |
| Assembly | `editor assemble` | timeline, renders, deliveries |

## Defaults

| Setting | Default | Notes |
| --- | --- | --- |
| Length | 15–30 s | Each take is limited by the model's maximum duration |
| Take size | 2–4 consecutive shots per take | Continuity across cuts inside one generation; single-shot takes for retakes |
| Canvases | one take set per canvas | Compose each aspect ratio; reframe is a labelled fallback |
| Audio | diegetic sound first; music only if the direction lock says so | Generated takes may contain sound; decide whether to keep it |
| Timing | shot `duration` (no narration) or word timestamps (dialogue) | `shots.py time` handles both |

## What makes it work

- A strong idea and camera fundamentals before images; beautiful frames cannot fix a weak story.
- Every location reference has a visible, motivated light source.
- Every shot states framing, movement direction with a reason, and specific character action; "cinematic" is never an instruction.
- The four continuity pillars — face, outfit, location, movement — are checked in dailies before anything is assembled.
