# Workspace campaign records

Honor an existing campaign root and source of truth. The following layout under `marketing/campaigns/` is the default for new campaigns:

```text
marketing/campaigns/
  INDEX.md
  UTM_CONVENTIONS.md
  <YYYY-MM-DD>-<campaign-name>/
    README.md
    MARKETING_BRIEF.md       # when created or supplied as a file
    campaign.json
    MEASUREMENT.md
    CHANGELOG.md
    copy/
      drafts/                # working copy drafts, voice/style explorations, review notes
      approved/
        v001/                # approved copy revision (channel copy, variant IDs, mapping)
        v002/                # subsequent approved copy revision when re-approved
    assets/
      development/           # storyboard and work-in-progress creative production
        storyboard/          # concepts, scripts, visual direction, beat sheets, storyboard.json
        images/              # reference images, contact-sheet boards, cropped tiles, candidate renders
        video/               # video projects, scene generators, Veo/Omni runs, draft renders/QA
        audio/               # voice configs, raw/normalized narration takes, alignment, music/SFX
      approved/
        v001/                # approved deliverable revision ready for campaign manager / publishing
          MANIFEST.md        # or assets.json: creative_id mapping, ratios, hashes, source runs
          images/            # approved final image and carousel deliverables
          video/             # approved final encoded video deliverables (16:9, 9:16, 4:5, 1:1)
          audio/             # approved standalone audio/voiceover deliverables when needed
        v002/                # subsequent approved asset revision
    tracking/
      v001/
        campaign.json        # immutable generation snapshot
        utm-links.csv
        UTM_PLAN.md
```

Name each new campaign directory `<YYYY-MM-DD>-<campaign-name>` (for example `2026-10-18-taskapp-activation`), using the campaign creation or planned start date in ISO `YYYY-MM-DD` format followed by a lowercase, nonpersonal hyphenated campaign slug. Use that same `<YYYY-MM-DD>-<campaign-name>` slug as the local `campaign_id` in `campaign.json` and `INDEX.md`.

Reuse an existing campaign record for follow-up work; do not create a duplicate directory or rename an active campaign just because the chat or calendar date changed, and do not force a migration of legacy non-dated campaign directories unless requested. Check `INDEX.md` and existing directories before assigning a new campaign folder. Create only the subdirectories needed for the current task (or requested scaffold). If the workspace has no writable local directory, explain the limitation and provide the proposed files; do not claim they were saved.

## What to record

- **INDEX.md:** campaign ID (`<YYYY-MM-DD>-<campaign-name>`), product, objective, lifecycle status, record path, and current revisions for tracking (`tracking/vNNN`), approved copy (`copy/approved/vNNN`) and approved assets (`assets/approved/vNNN`) when present. Update only the affected rows. A campaign's lifecycle status is separate from its links' or assets' publication status.
- **UTM_CONVENTIONS.md:** exact source/medium vocabulary, campaign/creative/placement naming, optional field meanings, existing aliases, analytics/channel assumptions, owner and dated changes. Preserve established casing; suggest normalization for new values without rewriting historical tags.
- **Campaign README.md:** product and objective, audience/market/language when known, destination/CTA, relevant channels and variants, supplied brief path, facts/evidence, assumptions, open decisions and owner, active tracking/copy/asset revision paths (`tracking/vNNN`, `copy/approved/vNNN`, `assets/approved/vNNN`), and exact publishing handoff. Do not invent budgets, schedules or campaign results. Link to source documents rather than duplicating a supplied brief.
- **campaign.json:** current complete link plan; retain published and retired IDs. Link `creative_id` and `utm_content` values to the stable variant IDs in `copy/approved/vNNN/` and `assets/approved/vNNN/`. Snapshots under `tracking/vNNN/` preserve earlier inputs and exports.
- **copy/drafts/ and copy/approved/vNNN/:** keep working copy, voice/style explorations, localization drafts and editorial notes in `copy/drafts/`. When the user approves copy for a channel or variant set, save the clean approved text and variant mapping in a fresh `copy/approved/v001/` directory (then `v002/`, `v003/`, and so on for later approved revisions).
- **assets/development/ and assets/approved/vNNN/:** keep exploratory and in-progress creative work under `assets/development/`:
  - `storyboard/`: creative concept selections, scripts (`SCRIPT.md`, `script.json`), visual/art direction (`STYLE.md`), beat sheets, `storyboard.json` and resolved timing (`timing.resolved.json`).
  - `images/`: reference assets, contact-sheet board runs (such as `board-v1/`), locally cropped tile previews (`tiles-v1/`) and candidate generations.
  - `video/`: video producer projects, custom Three.js/HTML scene generators, opt-in Veo/Omni runs (`veo-v1/`, `omni-v1/`), and draft compositions or QA frame snapshots.
  - `audio/`: `voice-config.json`, raw and loudness-normalized narration takes, word-level alignments, pause rules and music/SFX stems.
  When creative assets are reviewed and approved, promote or record the approved deliverables in a fresh `assets/approved/v001/` directory (and `v002/`, `v003/`, etc. for subsequent approved revisions) under `images/`, `video/` and/or `audio/`, alongside a manifest (`MANIFEST.md` or `assets.json`) mapping each `creative_id` to its approved file, placement ratio, hash and source development run.
- **MEASUREMENT.md:** primary conversion and its definition, analytics destination/property if known, attribution scope, relevant auto-tagging, validation status/evidence/date, and unresolved implementation work. Keep measurement unknowns explicit.
- **CHANGELOG.md:** dated decisions, link additions/replacements, approved copy/asset revision promotions (`copy/approved/vNNN`, `assets/approved/vNNN`), status transitions, reason and affected IDs. Distinguish planned, approved, actually published and retired items; generating an export or approving an asset does not publish it.

For a small tagging request these files can be brief, and `copy/` or `assets/` directories can be omitted until copy or creative work exists. Do not manufacture a research report or force a full marketing interview. If the user requests no filesystem changes, deliver the records in chat and respect that override.

## Revision and publication rules

Before changing the current plan, compare it with the latest snapshot. Existing published/retired link IDs retain their destination and UTM values. A changed tracking tuple or destination needs a new link ID; record its predecessor. When a new approved copy revision (`copy/approved/v002`) or approved asset revision (`assets/approved/v002`) materially changes the creative variant being measured, assign a new `creative_id` / `link_id` (and `utm_content` when distinct reporting is desired) while retaining the published link's history; if it is a pre-launch fix to an unpublished draft, update the draft entry in a new revision and document the promotion in `CHANGELOG.md`.

Tracking exports (`tracking/vNNN`), approved copy (`copy/approved/vNNN`) and approved assets (`assets/approved/vNNN`) always go into a new unused `vNNN` revision directory. Never overwrite previous revisions or repair an interrupted run by deleting it. Inspect retained files, then use the next unused revision. Preserve user-written campaign notes, development runs and unrelated local edits.

Keep campaign records in the product workspace, not in this plugin's source, global skill directories or temporary folders. Use relative links within the campaign directory where possible. Do not silently change `.gitignore`, initialize Git or stage files. Keep raw customer data, credentials and signed/private URLs out of all campaign directories; follow the workspace's Git policy for binary media in `assets/development/` and `assets/approved/` rather than staging or committing large binaries automatically.

## Validation evidence

Local helper checks establish syntax, required fields, unique IDs and encoded parameter round-trips only. Also compare taxonomy values, campaign identity, destination, and `creative_id`/placement mapping against the brief, active `copy/approved/vNNN` and `assets/approved/vNNN` revisions, and prior `tracking/vNNN` revisions.

When live verification is authorized and tools are available, test a representative URL per destination/redirect path, record the final destination and whether parameters/click IDs survive, and inspect receipt in the intended analytics tool under the applicable consent state. Check the intended signup/purchase event separately when in scope. Do not trigger real purchases or mutate tracking settings merely to test a URL. Avoid visiting links that themselves perform an action.

Record checks as passed, failed or pending with evidence and date. HTTP success alone does not prove analytics collection; a collected visit does not prove conversion attribution. Assign blockers to the publishing or engineering owner and do not describe pending links as attribution-verified.
