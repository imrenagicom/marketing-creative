# Take prompt anatomy

The compiler follows the structure that works for multi-shot video models: tell the model what it is making, who and what must stay identical, where things are, what happens when, and what to avoid.

| Section | Source | Purpose |
| --- | --- | --- |
| TITLE | direction lock logline | The story in one line |
| FORMAT | take duration, canvas, bible capture look, shot count | Sets length, frame and look; says the shots are hard cuts at given times |
| REFERENCE ROLES | bible references in the take's shots | Each subject's role, description and preserved features; "never redesign or morph" |
| LOCKS | bible locks | Positions, screen direction, geography, period |
| ENVIRONMENT | bible environment and light sources | Location and motivated light the model must keep |
| TIMELINE | shots: start–end, action, framing, movement, light, sound, dialogue | One timed beat per shot so the model cuts where the edit expects |
| CAMERA LANGUAGE | rule plus bible motion rules and screen directions | Motivated moves only; consistent direction |
| PERFORMANCE | direction lock acting baselines | How characters move and speak |
| AUDIO | bible audio policy | Explicit music/dialogue/sound decisions, including "none" |
| AVOID | bible negatives | Concrete failure modes to rule out |
| FINAL PRIORITY | fixed | Identity and geography over everything else |
| CONTINUITY (retakes) | anchors | Continue from the previous shot's last frame (and end on the next shot's first) |

## Writing upstream so the prompt is good

The compiled prompt is only as specific as the shot list and bible. Fix vagueness there:

- Action names hands, eyes and body: "clips the parcel into the yellow clamp; the green lights blink once", not "interacts with the drone".
- Movement names a direction and a reason: "slow crane up following the drone".
- Light names a visible source and direction from the environment.
- Sound names what is heard in the shot.
- Dialogue lines carry the language and speaker; generate the voice first if the model takes audio references.

## Single take vs several

One request covering 2–4 consecutive shots keeps faces, wardrobe and light consistent across those cuts. Long takes risk one bad shot spoiling the whole request; give hard or risky shots their own take, and use single-shot retakes for repairs.
