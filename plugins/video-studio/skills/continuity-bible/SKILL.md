---
name: continuity-bible
description: Build and maintain the continuity bible for a Video Studio film — character, environment, prop and vehicle references with features that must never change, motivated light sources, position and screen-direction locks, the declared camera look, reference images and Higgsfield elements — so every generated shot keeps the same face, outfit, location and movement. Use whenever a cinematic or footage project needs consistent characters or locations, before keyframes or AI video generation, or when generated shots drift in identity, wardrobe, geography or lighting.
---

# Continuity Bible

AI video drifts unless every request carries the same references and rules. The bible is that single source: what each character, place and object looks like, what must never change, where the light comes from, and how the camera behaves. Keyframe and video prompts are compiled from it; dailies are checked against it.

Read [bible-craft.md](references/bible-craft.md) before writing entries.

## Write `bible/bible.json`

From the direction lock and the user's material (photos, product shots, character ideas), write references — `{id, role, name, description, preserve[], images[], light_sources[]}` — plus `locks[]`, `capture` and `audio_policy` (fields in the producer's [project contract](../studio-producer/references/project-contract.md)).

- **Preserve lists** name the concrete features that must survive every shot: "short black bob", "teal waterproof jacket", "yellow cargo clamp". Vague entries ("stylish outfit") cannot be checked.
- **Every environment has visible, motivated light sources** ("low sun from frame left, warm orange"). Without them the model guesses and the film looks flat and inconsistent.
- **Locks** fix what continuity depends on: who sits where, which way the action moves, where landmarks are, period accuracy.
- **Capture** declares the camera or device look and its motion rules ("handheld camcorder: every move comes from the operator's arm").

```sh
python3 <this-skill>/scripts/bible.py check <project-dir>
python3 <this-skill>/scripts/bible.py negatives <project-dir>
```

`check` warns about missing images, references without Higgsfield elements and thin preserve lists. `negatives` derives the negative constraints every prompt will carry.

## Reference images and elements

Supplied photos go in `bible/images/` and the reference's `images`. For references without images, `bible.py sheets` writes image requests (character turnarounds, environment masters with their light). They run under the **Higgsfield image cap** (ask the producer for one if none is approved):

1. Get the estimate with `generate_image` and `get_cost: true`.
2. `bible.py reserve <project> --ref <id> --estimate <credits>` — checks the cap and records the job.
3. Call `generate_image` with the request, download the result, then `bible.py add-image <project> --ref <id> --entry <ledger id> --file <path> --job-id <id>`.
4. On a refusal run `bible.py fail --entry <id>`; on a timeout add `--uncertain`, check the job, and never resubmit automatically.

Show the user the images before using them; approved images are the identity from then on.

For characters, environments, props and vehicles, create a Higgsfield element from the best image (`media_upload` → PUT → `media_confirm`, then `manage_reference_elements` with `action: "create"`), wait until it is `completed`, and record it with `bible.py link <project> --ref <id> --element <uuid>`. Prompts for element-aware models then use `<<<uuid>>>` placeholders; other models receive the reference images as media.

## Keep it current

When the user approves a change (new outfit, new location), update the bible, re-run `negatives`, and tell them which keyframes and takes are now stale.
