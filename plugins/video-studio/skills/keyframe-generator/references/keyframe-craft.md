# Keyframe craft

## What a keyframe must get right

- **Framing**: the shot size and angle from the shot list (low wide at shoe level, MCU, over the shoulder).
- **Identity**: every preserved feature of every character and prop in frame.
- **Light**: the shot's `light_source` matching the environment's sources and direction.
- **Geography**: landmarks where the bible's geography lock puts them; screen direction consistent with neighbouring shots.
- **The moment**: start frames show the action's opening pose, end frames its closing pose. Choose poses that make the motion between them obvious and physically possible.

## Start only, or start and end?

| Use | When |
| --- | --- |
| Start frame only | Most shots; the video model invents the motion from the prompt |
| Start + end | Precise moves (a hand placing an object, a turn to camera), or matching the next shot's first frame for a seamless cut |

## Prompt edits worth making

- Put the most important subject first.
- Replace any vague phrase the shot list let through with concrete pose, prop and light detail.
- For vertical canvases, describe the composition vertically (subject in the upper third, legs cropped at the knee).
- Keep negatives short and concrete; long negative lists dilute the prompt.

## Models

`nano_banana_pro` honours element placeholders and is the default for identity-critical frames. `gpt_image_2_5` is the Higgsfield default for general generation and text. `minimax_h3` is listed for 2K keyframes. Read on 2026-10-27 from the MCP tool descriptions; check the current catalog (`models_explore` when available) for aspect ratios and media roles before relying on them.
