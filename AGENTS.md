# Repository guidance

## Purpose and layout

Marketing Creative, Marketing Performance and Video Studio are shared Codex, Claude Code and Google Antigravity skill plugins. Read
README.md for the workflow, configuration and validation commands, then
read the relevant skill entry point and its linked references before editing.

- `plugins/marketing-creative/skills/`, `plugins/marketing-performance/skills/`
  and `plugins/video-studio/skills/`
  own skill instructions, UI metadata,
  references, executable helpers and example assets. Install and package each
  complete tree because skills within a plugin share resources.
- Each plugin's `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json` and
  `plugin.json` (Antigravity) must agree on shared metadata and version. Root
  marketplace and `.agents/` workspace files own discovery; update their
  descriptions when the suite changes.
- `scripts/validate_package.py` defines the explicit distribution allowlist;
  `scripts/build_plugin.py` builds the deterministic archive.
- `tests/` contains offline regressions. `docs/skill-evaluation.md` covers
  behavioral scenarios; `docs/validation.md` records actual validation and
  its limits. Preserve the distinction between historical and new checks.
- `third-party/` inside the plugin contains required upstream license notices.
  Keep notices and attribution when adapting upstream material.

## Skill and tool changes

Use the installed `skill-creator` skill for creating or substantially updating
skills. Keep entry points concise and put conditional schemas and procedures
in linked references. Keep skill names, folder names and invocation metadata
consistent. Resource links must work in an installed plugin, without private
machine paths.

Preserve downstream entry points: supplied briefs, selected concepts and
existing media should not restart campaign intake. Image boards choose a
useful concept count and sheet/grid ratio; 3×3 is an example. Reference images
are optional and may have distinct roles. Keep generation and cropping layout
calculations consistent, stable concept IDs intact, and selected final assets
separate from low-resolution previews. Video production supports independently
composed 16:9, 9:16, 4:5 and 1:1 variants.

Verify current provider models, API contracts, prices and placement requirements
against official documentation when changing those integrations. Record the
verification date and source. Do not silently substitute models or turn a
provider response into a claim of visual quality or advertising performance.

Paid helpers must offer a useful dry-run and preserve submission identity,
successful outputs and recovery state. Do not automatically resubmit uncertain
paid operations. Use synthetic fixtures and mocked providers for routine tests;
live provider calls require authorization within the user's task scope.

Keep marketing-veo-video and marketing-omni-video explicitly opt-in. The user
requires approval of their prepared paid requests, including provider/model,
prompt/media, settings and current estimate; general production permission
does not enable them. Preserve their invocation policy and approval fingerprint
checks. motion-video-producer owns mixed-media assembly and final QA, with
project-local custom generators for Three.js/HTML scenes when needed.

## Credentials and generated files

Credentials belong in `~/.config/marketing-creative/.env` or a secret manager.
Helpers read exported environment variables and do not automatically load
`.env`. Keep README configuration instructions consistent with that behavior.
Never print or commit credentials, source-image payload dumps, environments,
rendered media or private campaign material.

Keep generated runs and release archives outside the plugin source. `samples/`
and `local-docs/` are ignored local work, not release content. Preserve unrelated
edits and existing outputs; use versioned run directories rather than overwrite
user material. Expand the package allowlist narrowly when adding a new resource.

## Validation

Use Python 3.10+ with Pillow installed from the image producer's
`scripts/requirements.txt` in a virtual environment, plus Node.js for the video
composition tests. Run the relevant checks before committing an increment:

```sh
python -m unittest discover -s tests -v
python scripts/validate_package.py
git diff --check
```

For skill entry-point changes, also run the installed skill-creator's
`scripts/quick_validate.py` against each changed skill. For packaging or manifest
changes, build archives outside the repository and validate the Claude and
Antigravity plugins and marketplace when the CLIs are available:

```sh
python scripts/build_plugin.py --output /tmp/marketing-creative-plugin.zip
python scripts/build_plugin.py --plugin marketing-performance --output /tmp/marketing-performance-plugin.zip
python scripts/build_plugin.py --plugin video-studio --output /tmp/video-studio-plugin.zip
claude plugin validate ./plugins/marketing-creative
claude plugin validate ./plugins/marketing-performance
claude plugin validate ./plugins/video-studio
claude plugin validate ./.claude-plugin/marketplace.json
agy plugin validate ./plugins/marketing-creative
agy plugin validate ./plugins/marketing-performance
agy plugin validate ./plugins/video-studio
```

Test meaningful behavior and recovery, not exact generated prose. Do not count
skipped image tests as passing image validation. Documentation-only changes
usually need diff/link checks rather than a full regression run. Report missing
dependencies and unperformed live, visual, listening or render checks explicitly;
mocked API results and package checks do not establish production quality.

## Incremental commits

Use the installed `$commit` skill for each commit. Make small, coherent commits
as validated increments are completed during the work, rather than leaving all
changes for one final commit. Keep implementation, its necessary tests and its
usage documentation together; independent repository guidance can be a separate
commit. Respect an explicit user request to defer commits.

Before each commit, inspect status, unstaged/staged diffs and recent history.
Stage specific files and review the staged changes. Preserve unrelated work;
avoid `git add .` and `git add -A`. Use semantic commit subjects under 72
characters, lowercase after the colon, with a body explaining material context.
Do not amend existing commits or bypass hooks unless explicitly requested.
Verify status after every commit and report the resulting commit IDs. Push only
when the user explicitly requests it.
