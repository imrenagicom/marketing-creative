# Graphic visual modes

These are the layouts the bundled motion-designer generator builds. Fields marked required are checked by `shots.py lint`.

| Mode | Required fields | Optional | Use for |
| --- | --- | --- | --- |
| `kinetic` | — | `layout` (`stack`, `center`) | The spoken line as large type; the line's keywords land in the accent colour on their words. Hooks, punchlines. |
| `title` | `title` | `subtitle` | A countable promise or section title ("3-step capture habit"). |
| `steps` | `items[] {line, text}` | `numbered` (default true) | A checklist or process; each item reveals when its line starts. Each item's `line` must be one of the shot's lines. |
| `ui-card` | `title`, `rows[]` | `highlight` (row index), `label` (default "Illustrative") | A simplified interface: rows of text with one highlighted, a cursor moving to it. Not product evidence. |
| `stat` | `value`, `label` | `prefix`, `suffix`, `from` | A number that counts up as it is said. Only verified numbers. |
| `image` | `asset` (project-relative path) | `caption`, `fit` (`contain`/`cover`) | A real capture, product shot or illustration supplied by the user. |
| `end-card` | `title` | `subtitle` | The CTA, held at the end. |

Every graphic shot also shows kinetic keywords for its lines (the words listed in the script's `keywords`) unless `visual.keywords` is `false`, so on-screen text stays tied to the narration.

## Choosing a mode

- Hook → `kinetic` (or `image` if the result is the hook).
- Promise → `title`.
- Steps or reasons → `steps`, or alternate `ui-card` / `kinetic` per step for variety.
- Proof → `stat` (verified) or `image` (real capture).
- CTA → `end-card`.

Need something the modes cannot express (a product animation, a 3D object, a chart)? Plan it as `kinetic` with a note in `motivation`, and tell the user a custom scene is needed; motion-designer can add a project-local generator.
