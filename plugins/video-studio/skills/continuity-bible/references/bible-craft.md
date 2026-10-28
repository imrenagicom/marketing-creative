# Bible craft

## The four continuity pillars

Every cut is judged against four things; the bible exists to make each one checkable.

| Pillar | Bible support | Typical failure |
| --- | --- | --- |
| Face | character `preserve` (face shape, hair, distinguishing marks), reference sheet, element | different person in profile or close-up |
| Outfit | `preserve` garment details, colours, accessories, which shoulder the bag is on | jacket changes colour, logo appears, bag swaps sides |
| Location | environment `preserve` landmarks, `light_sources`, geography lock | water tower jumps sides, sun moves, room layout changes |
| Movement | screen-direction lock, capture motion rules, shot `screen_direction` | character runs the other way after a cut, camera teleports |

## Writing references

- **Description** is what a stranger needs to recreate the subject: age range, build, hair, clothing layers, colours, materials.
- **Preserve** lists 3–6 features that matter most for recognition. Order by importance.
- **Characters** link to the direction lock's character (`character`), so their acting baseline reaches every prompt.
- **Props and vehicles** list geometry, colour and parts ("four underside thrusters", "red rear light bar") — models love to add or remove parts.
- **Style** references describe the overall look; use them sparingly, they compete with identity.

## Light

Put a visible light source in every location reference and name its direction and colour: a lamp with a golden glow on the kitchen counter, low sun through blinds from the left, monitor glow on the face. Shots then pick their `light_source` from these. This single habit removes much of the "empty", flat look of generated footage.

## Locks

| Kind | Example |
| --- | --- |
| `position` | The driver always drives; the passenger is always front right. |
| `identity` | The pumpkin heads never become human faces. |
| `screen-direction` | The chase moves left-to-right until the turn in S07. |
| `wardrobe` | No outfit changes during the day sequence. |
| `geography` | The window is always behind her left shoulder in the office. |
| `period` | Early-2000s Jakarta: no smartphones, no modern cars. |

## Capture

Declare how the footage was "shot": cinema camera, handheld camcorder, phone selfie, security cam. Add motion rules: for a selfie vlog, every camera move is caused by the subject's arm; for a locked-off documentary, no moves at all. A declared device makes generated motion feel physically caused instead of floating.

## Audio policy

State music, dialogue and sound effects explicitly, including "no music". Video models often add music when not told otherwise.
