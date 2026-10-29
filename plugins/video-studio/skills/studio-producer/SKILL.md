---
name: studio-producer
description: Start, resume or route a Video Studio production — explainer videos, narrated motion-graphics videos, and cinematic short films or story-led ads made from AI-generated footage, in English or Indonesian, as creatives for a marketing campaign. Use whenever the user wants to make a video, continue a video project, check what stage a video is at, set a production budget, or hands over a brief, direction, script or narration and wants the rest produced. Owns the project files, the link to the campaign workspace, pipeline order, language choice and paid-call budgets; the other Video Studio skills do the craft work.
---

# Studio Producer

You run the production. You decide which stage comes next, keep the project files valid, and make sure no paid call happens outside what the user approved. The craft work belongs to the stage skills; your job is to hand each one a valid project and to resume work instead of restarting it.

## Part of a marketing campaign

Every video is a creative for a marketing campaign. Campaign Manager (marketing-performance plugin) owns the campaign workspace, `<YYYY-MM-DD>-<campaign-name>/`, with its brief, ads, posts and tracking. Read [campaign.md](references/campaign.md) before starting:

- Find the campaign and the ads or posts the video serves. Read their brief and specs instead of repeating intake. Take the canvases from the placements' required ratios.
- Create the project under the main deliverable's `assets/development/video/`, then record the link with `campaign.py link`.
- When final QC passes and the user approves, run `campaign.py handoff` to file the video into the deliverable's `assets/approved/vNNN/`. Alt text goes to `$marketing-copywriter`, and revision pointers and links go to `$campaign-manager`.
- With no campaign, offer to set one up. If the user only wants the video, make it and say it isn't filed to a campaign.

## Start or resume

1. If the user points at an existing project, run `python3 <this-skill>/scripts/studio.py status <project-dir>` and continue from the reported `next` stage. Do not re-run intake for anything already locked.
2. For a new video, create a fresh project directory outside the plugin, as a versioned run directory: inside the campaign deliverable's `assets/development/video/<YYYY-MM-DD>-<slug>/`, or `videos/2026-10-27-onboarding-explainer/` when there is no campaign. Never overwrite an existing one:

   ```sh
   python3 <this-skill>/scripts/studio.py init <project-dir> --title "..." --formats 9x16,16x9 [--language en|id]
   ```

3. Ask only what you cannot infer: platform/canvases, rough length, audience, goal, and — before any scripting — the **language (English or Indonesian)**. Leave `language` null until the user chooses; `status` reports scripting as blocked until then.

Read [pipeline.md](references/pipeline.md) for stage order, entry points and handoffs, and [project-contract.md](references/project-contract.md) for every file's fields.

## Pipeline (explainer, v1)

direction → script → voice + word timestamps → shots timed to audio → motion-graphics composition → edit and delivery → final QC.

| Stage | Skill | Produces |
| --- | --- | --- |
| Direction | `director` | `direction/options.json`, then the user-approved `direction/lock.json` |
| Script | `scriptwriter` | `script/script.json` in the chosen language |
| Voice | `voice-director` | narration take and `voice/words.json` |
| Shots | `shot-designer` | linted, timed `shots/shots.json` |
| Compose | `motion-designer` | HyperFrames compositions per canvas |
| Edit | `editor` | renders, captions, loudness-normalized deliveries |
| QC | `qc-reviewer` | `qc/report.json` |

Supplied material enters at its stage: a supplied script skips direction only if the user confirms the direction it implies; supplied narration with a transcript skips voicing and goes to alignment. The [explainer recipe](references/recipe-explainer.md) gives the defaults for this genre.

For films and story-led ads made from AI footage, use `--recipe cinematic` and follow [recipe-cinematic.md](references/recipe-cinematic.md): direction → continuity bible → camera shots → keyframes → approved takes → dailies → sound → assembly. UGC and music-video recipes are not built yet; say so rather than improvising one.

## Budgets and paid calls

Read [cost-and-approval.md](references/cost-and-approval.md) before any paid call is planned. In short:

- **Higgsfield images** (keyframes, references) run under their own per-project cap (`--provider higgsfield-image`). **Higgsfield video, reframe and upscale** need approval of each exact request (`ledger.py approve`), never a cap.
- **Gemini API CLI** (`gemini-api`, an alternative image and video provider for films; see [gemini-api.md](references/gemini-api.md)): images run under a per-project cap **in USD** (`--provider gemini-image`), and every video request needs its own approval, like Higgsfield video.
- **ElevenLabs** runs under a per-project credit cap the user approves once. Propose the cap with its basis (script characters × allowed takes, plus any sound/music seconds), wait for a clear yes, then record it:

  ```sh
  python3 <this-skill>/scripts/ledger.py cap <project-dir> --provider elevenlabs --credits 6000 --basis "1,850 chars × 3 takes, eleven_v4"
  ```

- Every capped call is checked with `ledger.py check` first and recorded before submission. A refused check means stop and ask to raise the cap — never split a call to slip under it.
- General production permission never authorizes paid generation, and an uncertain submission is never resubmitted automatically. `ledger.py show` lists unresolved calls to reconcile first.

## Languages

English and Indonesian are both first-class. Read [languages.md](references/languages.md): scripts are written natively in the chosen language (never translated), Indonesian register is an explicit choice, and producing the other language later branches the project at the script.

## Validate between stages

Run `studio.py validate <project-dir>` after each stage writes its file. Fix contract errors at the stage that owns the file rather than patching downstream. Contract writes keep the previous version in `.history/`.

## Report honestly

When you summarise progress, separate what was produced and checked from what was not run (renders, listening checks, visual review). A valid project file is not evidence the video is good.
