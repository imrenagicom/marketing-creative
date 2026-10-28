# Languages: English and Indonesian

Both languages are first-class. The language for a video is chosen when the user asks to produce it; ask once if the brief does not say, and record it as `project.language` (`en` or `id`).

## What depends on the language

| Area | English (`en`) | Indonesian (`id`) |
| --- | --- | --- |
| Register (`script.register`) | `casual`, `conversational` or `formal` | `casual` (Jakarta *gua/lo*), `friendly` (*aku/kamu*) or `formal` (*saya/Anda*) |
| Planning pace (before real timestamps) | ~2.6 words/s conversational | ~2.2 words/s conversational (longer words) |
| Code-switching | rare | English product and tech terms are normal; keep them in English when the audience says them in English |
| Pronunciation | brand names | English terms inside Indonesian speech need a pronunciation check |
| Captions | ≤ 42 characters per line | ≤ 38 characters per line (longer words wrap sooner) |

Planning pace is only for estimating length; real word timestamps replace it after voicing.

## Rules

- **Write natively; never translate.** Hooks, idioms and CTAs that land in one language often fall flat when translated. The scriptwriter keeps separate patterns per language.
- **Register belongs to the character.** Record it in the direction lock's acting baseline and in the script; do not mix *gua* and *saya* for one speaker.
- **The direction lock is language-neutral.** Beats, acting intent and visual plan stay the same; language begins at the script.

## Producing the other language later

Branch the project at the script into a new versioned project directory (copy `project.json`, `direction/` and `style.json`; set the new language). Then write a native script, voice it, and re-time shots. Graphic shots are reused with new on-screen text; anything with visible speech must be regenerated.
