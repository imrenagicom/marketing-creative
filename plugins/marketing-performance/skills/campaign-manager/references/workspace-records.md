# Workspace campaign records

Honor an existing campaign root and source of truth. The following layout under `marketing/campaigns/` is the default for new campaigns:

```text
marketing/campaigns/
  INDEX.md
  UTM_CONVENTIONS.md
  <YYYY-MM-DD>-<campaign-name>/
    README.md
    MARKETING_BRIEF.md                 # when created or supplied as a file
    campaign.json                      # canonical campaign-wide link plan & platform ad mapping
    MEASUREMENT.md
    CHANGELOG.md
    tracking/
      v001/
        campaign.json                  # immutable generation snapshot
        utm-links.csv
        UTM_PLAN.md
    meta/                              # ad platform directory (currently Meta; extensible to other platforms)
      README.md                        # optional Meta account, pixel, and page notes
      campaigns/
        <meta-campaign-slug>/
          campaign.json                # Meta campaign goal (objective), buying type, and budget limit (CBO/ABO)
          adsets/
            <adset-slug>/
              adset.json               # optimization goal, schedule, placements/ratios, and user targeting
              ads/
                <ad-slug>/
                  ad.json              # format, CTA, destination_url, utm, url_tags, link_id, and active revisions
                  copy/
                    drafts/            # working primary text, headline, description, and style explorations
                    approved/
                      v001/            # approved ad copy revision
                      v002/            # subsequent approved ad copy revision
                  assets/
                    development/       # storyboard and work-in-progress creative production for this ad
                      storyboard/      # concepts, scripts, visual direction, beat sheets, storyboard.json
                      images/          # reference images, contact-sheet boards, cropped tiles, candidate renders
                      video/           # video projects, scene generators, Veo/Omni runs, draft renders/QA
                      audio/           # voice configs, raw/normalized narration takes, alignment, music/SFX
                    approved/
                      v001/            # approved deliverable revision ready for publishing
                        MANIFEST.md    # or assets.json: creative_id, ratios, hashes, Meta media IDs, source runs
                        images/        # approved final image and carousel deliverables
                        video/         # approved final encoded video deliverables (16:9, 9:16, 4:5, 1:1)
                        audio/         # approved standalone audio/voiceover deliverables when needed
                      v002/            # subsequent approved asset revision
```

Name each new campaign directory `<YYYY-MM-DD>-<campaign-name>` (for example `2026-10-18-taskapp-activation`), using the campaign creation or planned start date in ISO `YYYY-MM-DD` format followed by a lowercase, nonpersonal hyphenated campaign slug. Use that same `<YYYY-MM-DD>-<campaign-name>` slug as the local `campaign_id` in root `campaign.json` and `INDEX.md`.

Reuse an existing campaign record for follow-up work; do not create a duplicate directory or rename an active campaign just because the chat or calendar date changed, and do not force a migration of legacy non-dated campaign directories unless requested. Check `INDEX.md` and existing directories before assigning a new campaign folder. Create only the subdirectories needed for the current task (or requested scaffold). If the workspace has no writable local directory, explain the limitation and provide the proposed files; do not claim they were saved.

## What to record

- **INDEX.md:** campaign ID (`<YYYY-MM-DD>-<campaign-name>`), product, objective, active platforms (such as `meta`), lifecycle status, record path, and current tracking revision (`tracking/vNNN`). Update only the affected rows. A campaign's lifecycle status is separate from its links' or ads' publication status.
- **UTM_CONVENTIONS.md:** exact source/medium vocabulary, campaign/creative/placement naming, optional field meanings, existing aliases, analytics/channel assumptions, owner and dated changes. Preserve established casing; suggest normalization for new values without rewriting historical tags.
- **Campaign README.md:** product and objective, audience/market/language when known, destination/CTA, active platforms and hierarchy (`meta/campaigns/<meta-campaign-slug>/adsets/<adset-slug>/ads/<ad-slug>/`), supplied brief path, facts/evidence, assumptions, open decisions and owner, active tracking/copy/asset revision paths, and exact publishing handoff. Do not invent budgets, schedules or campaign results. Link to source documents rather than duplicating a supplied brief.
- **Root campaign.json:** current complete link plan across all channels and platform ads; retain published and retired IDs. For Meta ads, set `"platform": "meta"`, `"platform_campaign": "<meta-campaign-slug>"`, `"adset": "<adset-slug>"`, and `"ad": "<ad-slug>"` on the link entry and align `creative_id` and `utm_content` with that ad's approved copy and asset revisions. Snapshots under `tracking/vNNN/` preserve earlier inputs and exports.
- **meta/campaigns/<meta-campaign-slug>/campaign.json:** Meta campaign goal (`objective`), `buying_type`, `special_ad_categories`, campaign budget mode and limits (`budget`: `mode`, `currency`, `daily_budget` / `lifetime_budget`, `spend_cap`, `bid_strategy`), `status`, and optional `remote_campaign_id` (see [meta-ads.md](meta-ads.md)).
- **meta/.../adsets/<adset-slug>/adset.json:** `optimization_goal`, `billing_event`, optional `conversion` (pixel/event), `schedule`, ad-set `budget` (when ABO), **user targeting** (`targeting`: geo locations, age range, gender, locales, interests/behaviors, custom/lookalike audiences, exclusions), `placements` (platforms, positions, and required creative aspect ratios), `status`, and optional `remote_adset_id`.
- **meta/.../ads/<ad-slug>/ad.json, copy/, and assets/:**
  - `ad.json` binds the ad (`ad_slug`, `name`, `status`, `format`, `call_to_action`) to its `link_id` in root `campaign.json`, clean `destination_url` (Meta Website URL), `utm` object, serialized `url_tags` (Meta URL parameters), and active revision paths (`approved_copy_revision`, `approved_assets_revision`).
  - `copy/drafts/` and `copy/approved/vNNN/`: keep working ad copy, voice/style explorations, localization drafts and editorial notes in `copy/drafts/`. When approved, save the clean ad copy and field mapping in a fresh `copy/approved/v001/` directory (then `v002/`, `v003/`, etc. for later approved revisions).
  - `assets/development/` and `assets/approved/vNNN/`: keep exploratory and in-progress creative work for the ad under `assets/development/storyboard/`, `assets/development/images/`, `assets/development/video/`, and `assets/development/audio/`. When creative deliverables are reviewed and approved, place them in a fresh `assets/approved/v001/` directory (and `v002/`, `v003/`, etc. for subsequent approved revisions) under `images/`, `video/` and/or `audio/`, alongside `MANIFEST.md` or `assets.json` mapping `creative_id`, placement ratios, file hashes and source development runs. When two ads in an ad set share the exact same approved creative deliverable, `ad.json` can reference the sibling ad's `assets/approved/vNNN` directory rather than duplicating paid renders.
- **MEASUREMENT.md:** primary conversion and its definition, analytics destination/property if known, attribution scope, relevant auto-tagging, validation status/evidence/date, and unresolved implementation work. Keep measurement unknowns explicit.
- **CHANGELOG.md:** dated decisions, campaign/adset/ad additions or changes, link replacements, approved copy/asset revision promotions (`copy/approved/vNNN`, `assets/approved/vNNN`), status transitions, reason and affected IDs. Distinguish planned, approved, actually published and retired items; generating an export or approving an asset does not publish it.

For a small URL-only tagging request these files can be brief, and `meta/` subdirectories can be omitted until ad-platform planning, copy or creative work exists. Non-ad channels (such as organic posts or newsletters) keep their link entries in root `campaign.json` and may use optional top-level `copy/` or `assets/` folders when no ad-platform hierarchy applies. Do not manufacture a research report or force a full marketing interview. If the user requests no filesystem changes, deliver the records in chat and respect that override.

## Revision and publication rules

Before changing the current plan, compare it with the latest snapshot. Existing published/retired link IDs retain their destination and UTM values. A changed tracking tuple or destination needs a new link ID; record its predecessor. When a new approved copy revision (`copy/approved/v002`) or approved asset revision (`assets/approved/v002`) on an ad materially changes the creative variant being measured, assign a new `creative_id` / `link_id` (and `utm_content` when distinct reporting is desired) while retaining the published link's history; if it is a pre-launch fix to an unpublished draft, update the draft entry in a new revision and document the promotion in `CHANGELOG.md`.

Tracking exports (`tracking/vNNN`), approved copy (`copy/approved/vNNN`) and approved assets (`assets/approved/vNNN`) always go into a new unused `vNNN` revision directory. Never overwrite previous revisions or repair an interrupted run by deleting it. Inspect retained files, then use the next unused revision. Preserve user-written campaign notes, development runs and unrelated local edits.

Keep campaign records in the product workspace, not in this plugin's source, global skill directories or temporary folders. Use relative links within the campaign directory where possible. Do not silently change `.gitignore`, initialize Git or stage files. Keep raw customer data, credentials and signed/private URLs out of all campaign directories; follow the workspace's Git policy for binary media in `assets/development/` and `assets/approved/` rather than staging or committing large binaries automatically.

## Validation evidence

Local helper checks establish syntax, required fields, unique IDs, encoded parameter round-trips, and (when `meta/campaigns/` exists) consistency between root `campaign.json` and every Meta campaign, ad set, and ad specification. Also compare taxonomy values, campaign goals/budgets, ad-set targeting/placements, destination, and `creative_id` mapping against the brief, active `copy/approved/vNNN` and `assets/approved/vNNN` revisions, and prior `tracking/vNNN` revisions.

When live verification is authorized and tools are available, test a representative URL per destination/redirect path, record the final destination and whether parameters/click IDs survive, and inspect receipt in the intended analytics tool under the applicable consent state. Check the intended signup/purchase event separately when in scope. Do not trigger real purchases or mutate tracking settings merely to test a URL. Avoid visiting links that themselves perform an action.

Record checks as passed, failed or pending with evidence and date. HTTP success alone does not prove analytics collection; a collected visit does not prove conversion attribution. Assign blockers to the publishing or engineering owner and do not describe pending links as attribution-verified.
