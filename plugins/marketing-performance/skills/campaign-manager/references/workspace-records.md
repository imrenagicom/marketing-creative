# Workspace campaign records

Honor an existing campaign root and source of truth. The following layout under `marketing/campaigns/` is the default for new campaigns:

```text
marketing/campaigns/
  INDEX.md
  UTM_CONVENTIONS.md
  audiences/                           # account-level Meta custom audiences shared across campaigns (see meta-audiences.md)
    README.md                          # registry: slug, Meta name, kind, window, status, remote ID, size, used by
    meta-ads/
      <audience-slug>.json             # record + native adsctl payload
  <YYYY-MM-DD>-<campaign-name>/
    README.md                          # single campaign entrypoint & index linking to docs/, tracking/, and channels
    campaign.json                      # canonical campaign-wide link plan & platform mapping
    docs/                              # campaign-level markdowns, briefs, plans, and reviews
      MARKETING_BRIEF.md               # strategic brief, product facts, audience, and channel requirements
      MEASUREMENT.md                   # conversion definitions, attribution scope, and validation status
      CHANGELOG.md                     # dated revision log across copy, assets, links, and launches
      plans/                           # campaign-wide or cross-channel plans (CREATIVE_IDEAS.md, CROSS_PLATFORM.md, carousel/content plans, shooting plans)
      reviews/                         # feature evidence registers, QA/review reports, delivery/repository handoffs, audit summaries
    reports/                           # chronological multi-source campaign performance reports (<datetime>.md)
      2026-10-19-2200.md               # point-in-time Meta Ads + GA4 + Backend funnel analysis, actions taken, and lessons learned
    tracking/
      v001/
        campaign.json                  # immutable generation snapshot
        utm-links.csv
        UTM_PLAN.md
    meta-ads/                          # paid Meta Ads platform tree (Campaign -> Ad Set -> Ad)
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
                    drafts/            # working primary text, headline, description, alt text, and style explorations
                    approved/
                      v001/            # approved ad copy and accessibility alt text revision
                      v002/            # subsequent approved ad copy revision
                  assets/
                    development/       # storyboard and work-in-progress creative production for this ad
                      storyboard/      # concepts, scripts, visual direction, beat sheets, storyboard.json
                      images/          # reference images, contact-sheet boards, cropped tiles, candidate renders
                      video/           # Video Studio projects, scene generators and Gemini/Higgsfield runs, draft renders/QA
                      audio/           # voice configs, raw/normalized narration takes, alignment, music/SFX
                    approved/
                      v001/            # approved deliverable revision ready for publishing
                        MANIFEST.md    # or assets.json: creative_id, ratios, hashes, Meta media IDs, source runs
                        images/        # approved final image and carousel deliverables
                        video/         # approved final encoded video deliverables (16:9, 9:16, 4:5, 1:1)
                        audio/         # approved standalone audio/voiceover deliverables when needed
                      v002/            # subsequent approved asset revision
    instagram/                         # social media campaign tree (same structure for linkedin/ and twitter/)
      README.md                        # optional channel notes, handle, or cadence
      posts/
        <post-slug>/
          post.json                    # format, status, schedule, optional link/UTM mapping, and active revisions
          copy/
            drafts/                    # working captions, hooks, hashtags, story/reel text, alt text
            approved/
              v001/                    # approved caption/copy and accessibility alt text revision
              v002/
          assets/
            development/
              storyboard/
              images/
              video/
              audio/
            approved/
              v001/
                MANIFEST.md
                images/
                video/
                audio/
    linkedin/
      posts/
        <post-slug>/                   # post.json, copy/{drafts,approved/vNNN}, assets/{development,approved/vNNN}
    twitter/
      posts/
        <post-slug>/                   # post.json, copy/{drafts,approved/vNNN}, assets/{development,approved/vNNN}
```

Name each new campaign directory `<YYYY-MM-DD>-<campaign-name>` (for example `2026-10-18-taskapp-activation`), using the campaign creation or planned start date in ISO `YYYY-MM-DD` format followed by a lowercase, nonpersonal hyphenated campaign slug. Use that same `<YYYY-MM-DD>-<campaign-name>` slug as the local `campaign_id` in root `campaign.json` and `INDEX.md`.

Reuse an existing campaign record for follow-up work; do not create a duplicate directory or rename an active campaign just because the chat or calendar date changed, and do not force a migration of legacy non-dated campaign directories unless requested. Check `INDEX.md` and existing directories before assigning a new campaign folder. Create only the subdirectories needed for the current task (or requested scaffold). If the workspace has no writable local directory, explain the limitation and provide the proposed files; do not claim they were saved.

## What to record

- **INDEX.md:** campaign ID (`<YYYY-MM-DD>-<campaign-name>`), product, objective, active platforms (such as `meta-ads`, `instagram`, `linkedin`, `twitter`), lifecycle status, record path, and current tracking revision (`tracking/vNNN`). Update only the affected rows. A campaign's lifecycle status is separate from its links', ads', or posts' publication status.
- **UTM_CONVENTIONS.md:** exact source/medium vocabulary, campaign/creative/placement naming, optional field meanings, existing aliases, analytics/channel assumptions, owner and dated changes. Preserve established casing; suggest normalization for new values without rewriting historical tags.
- **Campaign README.md:** single root entrypoint summarizing product and objective, audience/market/language when known, destination/CTA, active platforms and hierarchy (`meta-ads/campaigns/<meta-campaign-slug>/adsets/<adset-slug>/ads/<ad-slug>/` and/or `{instagram,linkedin,twitter}/posts/<post-slug>/`), links to `docs/` (`docs/MARKETING_BRIEF.md`, `docs/MEASUREMENT.md`, `docs/CHANGELOG.md`, `docs/plans/`, `docs/reviews/`) and `reports/` (`reports/<datetime>.md`), assumptions, open decisions and owner, active tracking/copy/asset revision paths, and exact publishing handoff. Do not invent budgets, schedules or campaign results. Link to source documents in `docs/` and `reports/` rather than cluttering the campaign root with loose markdown files.
- **docs/ (Campaign documents, markdowns, and document plans):**
  - Keep campaign-level markdown documents organized inside `docs/` rather than scattering loose `.md` files in the campaign root:
    - **`docs/MARKETING_BRIEF.md`:** strategic brief, target audience, positioning, verified product facts, offer, and placement requirements.
    - **`docs/MEASUREMENT.md`:** primary conversion and its definition, analytics destination/property if known, attribution scope, relevant auto-tagging, validation status/evidence/date, and unresolved implementation work. Keep measurement unknowns explicit.
    - **`docs/CHANGELOG.md`:** dated decisions, campaign/adset/ad/post additions or changes, link replacements, approved copy/asset revision promotions (`copy/approved/vNNN`, `assets/approved/vNNN`), status transitions, reason and affected IDs. Distinguish planned, approved, actually published and retired items; generating an export or approving an asset does not publish it.
    - **`docs/plans/`:** campaign-wide or cross-channel execution plans, creative concept explorations (`CREATIVE_IDEAS.md`), cross-platform distribution plans (`CROSS_PLATFORM.md`), carousel/content plans, and filming/shooting plans.
    - **`docs/reviews/`:** product feature evidence registers (`FEATURE_EVIDENCE.md`), visual/technical QA reviews (`REVIEW.md`), and delivery and repository handoffs (`DELIVERY.md`, `REPOSITORY.md`).
  - When a script (`SCRIPT.md`), beat sheet, visual direction (`VISUAL_DIRECTION.md`), shooting plan (`SHOOTING_PLAN.md`), or visual review (`REVIEW.md`) belongs specifically to a single ad's or post's creative development, store it in that ad's or post's `assets/development/storyboard/` (or `<ad-or-post>/docs/`).
- **reports/<datetime>.md (Chronological campaign performance & funnel reports):**
  - Store point-in-time campaign performance analyses inside top-level `reports/` using an ISO-ordered timestamp filename (`reports/YYYY-MM-DD-HHMM.md` or `reports/YYYY-MM-DDTHH-MM-SS+HH-MM.md`; see [reporting.md](reporting.md)).
  - Combine paid ad delivery metrics (`$adsctl`, `$adsctl-meta-analyst`), post-click web/app funnel analytics ([google-analytics-analyst](../../google-analytics-analyst/SKILL.md)), and first-party backend conversion records into a single structured report covering: Executive Verdict, Multi-Source Funnel Scorecard, Creative Variant & Placement Breakdown, What Went Well, What Went Wrong, What Can Be Improved & Recommendations, Actions Taken, Lessons Learned, and Action Items & Next Checkpoints.
  - Never overwrite an existing `reports/<datetime>.md` file when running a later checkpoint; always write a new timestamped report file.
- **Root campaign.json:** current complete link plan across all channels, paid ads, and social posts; retain published and retired IDs. For Meta ads, set `"platform": "meta-ads"`, `"platform_campaign": "<meta-campaign-slug>"`, `"adset": "<adset-slug>"`, and `"ad": "<ad-slug>"` on the link entry. For social media posts that include a tracked link, set `"platform": "instagram" | "linkedin" | "twitter"` and `"post": "<post-slug>"`. Align `creative_id` and `utm_content` with that ad's or post's approved copy and asset revisions. Snapshots under `tracking/vNNN/` preserve earlier inputs and exports.
- **meta-ads/campaigns/<meta-campaign-slug>/campaign.json:** Meta campaign goal (`objective`), `buying_type`, `special_ad_categories`, campaign budget mode and limits (`budget`: `mode: "advantage_plus" | "cbo" | "abo"` — defaulting to `"advantage_plus"` for Advantage+ campaign budget — `currency`, `daily_budget` / `lifetime_budget`, optional `spend_cap`, `bid_strategy`, and `is_adset_budget_sharing_enabled: false`), `status`, and optional `remote_campaign_id` (see [meta-ads.md](meta-ads.md)).
- **meta-ads/.../adsets/<adset-slug>/adset.json:** `optimization_goal`, `billing_event`, optional `conversion` (pixel/event), `schedule`, `budget` (`{"mode": "advantage_plus", "inherited_from_campaign": true}` when the campaign uses Advantage+ campaign budget, or ad-set budget when ABO), **user targeting** (`targeting`: geo locations, age range, gender, locales, interests/behaviors, custom/lookalike audiences, exclusions), `placements` (defaulting to `"mode": "advantage_plus"` for Advantage+ placements with `required_ratios` and no platform/position restrictions, or `"mode": "manual"` with explicit `publisher_platforms` and `*_positions`), `status`, and optional `remote_adset_id`.
- **meta-ads/.../ads/<ad-slug>/ad.json, copy/, and assets/:**
  - `ad.json` binds the ad (`ad_slug`, `name`, `status`, `format`, `call_to_action`) to its `link_id` in root `campaign.json`, clean `destination_url` (Meta Website URL), `utm` object, serialized `url_tags` (Meta URL parameters), and active revision paths (`approved_copy_revision`, `approved_assets_revision`).
  - `copy/drafts/` and `copy/approved/vNNN/`: keep working ad copy, voice/style explorations, localization drafts, accessibility alt text (written by [marketing-copywriter](../../marketing-copywriter/SKILL.md) whenever images, carousel slides, or videos are created), and editorial notes in `copy/drafts/`. When approved, save the clean ad copy, accessibility alt text, and field mapping in a fresh `copy/approved/v001/` directory (then `v002/`, `v003/`, etc. for later approved revisions).
  - `assets/development/` and `assets/approved/vNNN/`: keep exploratory and in-progress creative work for the ad under `assets/development/storyboard/`, `assets/development/images/`, `assets/development/video/`, and `assets/development/audio/`. When creative deliverables are reviewed and approved, place them in a fresh `assets/approved/v001/` directory (and `v002/`, `v003/`, etc. for subsequent approved revisions) under `images/`, `video/` and/or `audio/`, alongside `MANIFEST.md` or `assets.json` mapping `creative_id`, placement ratios, file hashes and source development runs.
- **{instagram,linkedin,twitter}/posts/<post-slug>/post.json, copy/, and assets/:**
  - `post.json` records `platform` (`"instagram"`, `"linkedin"`, or `"twitter"`), `post_slug`, `name`, `status`, `format`, optional `schedule`, optional tracked link mapping (`link_id`, `destination_url`, `utm`, `url`), and active revision paths (`approved_copy_revision`, `approved_assets_revision`; see [social-media.md](social-media.md)).
  - `copy/drafts/` and `copy/approved/vNNN/`: keep working social captions, opening hooks, thread posts, hashtags, first-comment copy, and accessibility alt text (written by [marketing-copywriter](../../marketing-copywriter/SKILL.md) whenever images, carousel slides, or videos/reels are created) in `copy/drafts/`; promote user-approved captions/threads and accessibility alt text into `copy/approved/v001/`, `v002/`, etc.
  - `assets/development/` and `assets/approved/vNNN/`: keep storyboard/media development under `assets/development/{storyboard,images,video,audio}/` when new creative is produced for this post, and place approved social media images, carousels, videos/reels, or audio under `assets/approved/v001/`, `v002/`, etc.
- **Cross-channel asset reuse (copying between `meta-ads/` and social media without regeneration):**
  - Do **not** regenerate images, videos, or audio for social media (`instagram/`, `linkedin/`, `twitter/`) if a suitable approved asset already exists in `meta-ads/` (or another social directory), and vice versa (`meta-ads/` reusing an asset already created for social media).
  - Instead, copy the approved deliverable from the source `assets/approved/vNNN/` directory into the target ad's or post's `assets/approved/v001/` directory so each directory keeps a complete local record, and record `copied_from` and the file hash in the target's `MANIFEST.md` or `assets.json`.
  - When an ad or social post copies an approved asset from another directory rather than generating new media, **it is okay to omit `assets/development/`** altogether, and ask [marketing-copywriter](../../marketing-copywriter/SKILL.md) to carry over or adapt the accessibility alt text in the target's `copy/drafts/` and `copy/approved/vNNN/`.

For a small URL-only tagging request these files can be brief, and `docs/plans/`, `docs/reviews/`, `reports/`, `meta-ads/`, `instagram/`, `linkedin/`, and `twitter/` subdirectories can be omitted until platform planning, copy, creative work, or performance reporting exists. Do not manufacture a research report or force a full marketing interview. If the user requests no filesystem changes, deliver the records in chat and respect that override.

## Revision and publication rules

Before changing the current plan, compare it with the latest snapshot. Existing published/retired link IDs retain their destination and UTM values. A changed tracking tuple or destination needs a new link ID; record its predecessor. When a new approved copy revision (`copy/approved/v002`) or approved asset revision (`assets/approved/v002`) on an ad or social post materially changes the creative variant being measured, assign a new `creative_id` / `link_id` (and `utm_content` when distinct reporting is desired) while retaining the published link's history; if it is a pre-launch fix to an unpublished draft, update the draft entry in a new revision and document the promotion in `CHANGELOG.md`.

Tracking exports (`tracking/vNNN`), approved copy (`copy/approved/vNNN`), approved assets (`assets/approved/vNNN`), and performance reports (`reports/<datetime>.md`) always go into a new unused `vNNN` revision directory or timestamped file. Never overwrite previous revisions or repair an interrupted run by deleting it. Inspect retained files, then use the next unused revision. Preserve user-written campaign notes, development runs and unrelated local edits.

Keep campaign records in the product workspace, not in this plugin's source, global skill directories or temporary folders. Use relative links within the campaign directory where possible. Do not silently change `.gitignore`, initialize Git or stage files. Keep raw customer data, credentials and signed/private URLs out of all campaign directories; follow the workspace's Git policy for binary media in `assets/development/` and `assets/approved/` rather than staging or committing large binaries automatically.

## Validation evidence

Local helper checks establish syntax, required fields, unique IDs, encoded parameter round-trips, and (when `meta-ads/campaigns/` or `{instagram,linkedin,twitter}/posts/` exists) consistency between root `campaign.json` and every Meta campaign/adset/ad and social post specification. Also compare taxonomy values, campaign goals/budgets, ad-set targeting/placements, destination, and `creative_id` mapping against the brief, active `copy/approved/vNNN` and `assets/approved/vNNN` revisions, and prior `tracking/vNNN` revisions.

When live verification is authorized and tools are available, test a representative URL per destination/redirect path, record the final destination and whether parameters/click IDs survive, and inspect receipt in the intended analytics tool under the applicable consent state. Check the intended signup/purchase event separately when in scope. Do not trigger real purchases or mutate tracking settings merely to test a URL. Avoid visiting links that themselves perform an action.

Record checks as passed, failed or pending with evidence and date. HTTP success alone does not prove analytics collection; a collected visit does not prove conversion attribution. Assign blockers to the publishing or engineering owner and do not describe pending links as attribution-verified.
