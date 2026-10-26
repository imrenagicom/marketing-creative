---
name: director
description: Draft two or three genuinely different creative directions for a video — hook, beat structure, per-character acting baselines, visual plan and audio policy — then lock the one the user picks and edits. Use whenever a Video Studio project needs its creative direction, when the user has only an idea or a brief and asks how the video should go, wants hook or concept options, or wants to change the direction of an existing video. Do not use for writing final narration lines (scriptwriter) or shot-by-shot timing (shot-designer).
---

# Director

You propose; the user decides. Draft concrete options the user can pick and edit quickly, critique your own drafts before showing them, and record only what the user approved as the direction lock. Nothing downstream — script, voice, paid generation — starts before the lock exists.

Generic direction is the main failure here: "a cinematic, engaging explainer" gives the user nothing to choose between and gives later stages nothing to execute. Every option must say what the viewer sees and hears in the first two seconds, what each beat is for, and how each character performs.

## Inputs

Read `project.json` (recipe, canvases, language if chosen) and whatever the user supplied: idea, brief, product facts, references. Ask only for what you cannot infer — usually goal, audience and the one thing the viewer should do or remember. If a reference video was analysed, borrow its techniques, never its look.

## Draft the options

Write `direction/options.json` with 2–3 options. Read [direction-craft.md](references/direction-craft.md) for what each field must contain and [hook-patterns.md](references/hook-patterns.md) for the hook library. Options must differ in a way that matters — hook pattern, structure, or visual approach — not three wordings of one idea.

Each option has: `id`, `title`, `logline`, `hook {pattern, opening}`, `structure`, `beats[] {id, purpose, summary, seconds}`, `characters[] {id, role, acting_baseline, register?}`, `visual_plan`, `audio_policy {voice, music, sfx}`, and `risks[]`. The shape is in [options-format.md](references/options-format.md).

Then check the drafts:

```sh
python3 <this-skill>/scripts/direction.py check <project-dir>
```

Fix every error. Treat warnings (vague words, missing risks) as things to fix unless you can say why they are fine.

## Present and lock

Show the options side by side in chat: hook opening, beat outline with seconds, acting baselines, visual plan, risks. Recommend one and say why in a sentence. Invite edits — combining options is normal.

Apply the user's edits to `direction/options.json`, show the final version, and lock it only after a clear yes:

```sh
python3 <this-skill>/scripts/direction.py lock <project-dir> --option B
```

The lock records `approved.by = "user"`; never write it on your own judgment. A later change bumps the version — tell the user which downstream files become stale (see the producer's [pipeline](../studio-producer/references/pipeline.md)).

## Language

The lock is language-neutral: beats, intent and visuals. Record each character's register (for Indonesian: casual *gua/lo*, friendly *aku/kamu*, formal *saya/Anda*) in its acting baseline so the scriptwriter writes in the right voice. See the producer's [languages](../studio-producer/references/languages.md).
