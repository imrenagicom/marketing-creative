# Composition craft

## style.json — `video-studio/style@1`

```json
{
  "schema": "video-studio/style@1",
  "colors": {"background": "#0F1115", "surface": "#1A1D24", "text": "#F4F1EA", "accent": "#FF9F43", "muted": "#8A8F98"},
  "fonts": {"display": "Inter", "body": "Inter"},
  "radius": 28,
  "motion": {"ease": "power3.out", "entrance": 0.35}
}
```

- Derive tokens from the direction lock's contrast rule and the brand, not from a reference video's look.
- The accent is for what matters right now: the spoken keyword, the active step, the number. If everything is accent, nothing is.
- Check text contrast against `background` and `surface` (aim for WCAG AA, 4.5:1 for body-size text).
- Fonts must be available at render time; prefer local files or localize web fonts before final renders.

## Per-canvas layout

| Canvas | Layout | Safe area (top/right/bottom/left) |
| --- | --- | --- |
| 9:16 | centered stack, larger type | 12% / 7% / 22% / 7% — platform UI covers the bottom |
| 16:9 | left-aligned, content ≤ 75% width | 8% / 7% / 10% / 7% |
| 4:5 | centered stack | 8% / 7% / 12% / 7% |
| 1:1 | centered stack | 8% / 7% / 10% / 7% |

Review each canvas separately: long Indonesian words wrap sooner, and a layout that fits 16:9 can overflow 9:16.

## Motion vocabulary

- **Entrances** ~0.2–0.4 s with an ease-out; exits faster than entrances.
- **Cue on the word.** Keyword chips appear 50 ms before their word starts and leave shortly after the line ends.
- **One focal change at a time.** When a new step appears, dim the previous one.
- **Transitions** follow the shot list: wipe for section changes, fade for endings, push for forward sequences.
- **Motivated movement only.** A cursor moves to the thing being named; a counter counts as the number is said.

## Depth and text behind the subject

Placing type behind a person or product needs a per-frame alpha matte of the subject. The plan (design doc) is local SAM 2.1 for video and BiRefNet for stills, with Higgsfield background removal as a paid fallback for stills; the v1 generator does not yet compose mattes. Until it does, keep type beside or below the subject rather than faking occlusion, and tell the user when a direction relies on it.

## Illustrative vs real

UI cards are labelled "Illustrative" by default. When a claim depends on the real product, use `image` shots with real captures supplied by the user.
