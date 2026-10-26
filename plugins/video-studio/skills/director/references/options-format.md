# direction/options.json

```json
{
  "schema": "video-studio/direction-options@1",
  "options": [
    {
      "id": "A",
      "title": "Three-step habit",
      "logline": "A productivity coach shows a three-step capture habit that stops ideas getting lost.",
      "hook": {
        "pattern": "pain-question",
        "opening": "Chat bubbles pile up on a dark screen while the narrator asks whether you keep losing your best ideas; 'best ideas' lands in the accent colour on the word."
      },
      "structure": "problem → promise → three numbered steps → CTA",
      "beats": [
        {"id": "B1", "purpose": "hook", "summary": "Name the pain: ideas lost in random chats.", "seconds": 3},
        {"id": "B2", "purpose": "promise", "summary": "Promise a three-step habit.", "seconds": 3},
        {"id": "B3", "purpose": "steps", "summary": "Capture, tag, review — one checklist item per step.", "seconds": 9},
        {"id": "B4", "purpose": "cta", "summary": "Save this and try it for a week.", "seconds": 3}
      ],
      "characters": [
        {"id": "narrator", "role": "friendly productivity coach",
         "acting_baseline": "Warm and quick, slightly amused by the problem, leans on the numbers, never salesy.",
         "register": "conversational"}
      ],
      "visual_plan": "Dark surface with one warm accent; spoken keywords land on the word; the checklist builds one item per step; the end card repeats the CTA.",
      "audio_policy": {"voice": "one narrator", "music": "none", "sfx": "soft tick on each checklist item"},
      "risks": ["The pain question is generic; a specific scenario from the audience would land harder."]
    }
  ]
}
```

A real file has 2–3 options. `direction.py lock` copies the chosen option into `direction/lock.json` with the version and the user's approval stamp; `title` and `risks` stay in the options file.
