# Dailies review

Dailies catch drift while a retake is still cheap — before sound and assembly build on a bad clip.

## What to look at

| Pillar | Compare against | Fail when |
| --- | --- | --- |
| Face | character reference images and `preserve` | a different person, changed hair or features in any frame |
| Outfit | `preserve` garments, colours, accessories | colour or garment changes, items appear, disappear or switch sides |
| Location | environment images, landmarks, `light_sources`, geography lock | landmarks move, layout changes, light comes from the wrong side |
| Movement | shot `screen_direction`, neighbouring shots, capture motion rules | action reverses across a cut, camera teleports, physics breaks |

Also note readable problems outside the pillars: distorted hands, duplicated characters, unwanted text or logos, generated music the bible ruled out. Record them in the closest pillar's note.

## Automated checks

- **aspect**: the clip matches its canvas ratio (a mismatch usually means the wrong `aspect_ratio` was sent).
- **duration**: the clip is within 0.5 s of the planned shot length (larger gaps mean the split or the model's timing is off).

## After review

- All pillars pass → select the clips (`takes.py select`).
- A pillar fails → plan a single-shot retake for that shot (`takes.py retake`), approve and run it, and review the retake.
- The whole take fails (identity lost throughout) → fix the bible or prompt upstream before spending on another full take.
- Selecting without review needs `--skip-dailies "<reason>"`, recorded on the take; use it only when the user says so.
