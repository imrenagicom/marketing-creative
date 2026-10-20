---
name: campaign-manager
description: Define campaign workspace structure, paid ad hierarchies (meta-ads campaign, ad set, and ad folders), social media campaign trees (instagram, linkedin, twitter), campaign documents and plans (docs/), timestamped campaign performance reports (reports/), UTM conventions, and tagged product campaign links; organize storyboard and media development, versioned approved assets and copy/caption revisions, tracking records, and cross-channel performance reviews in YYYY-MM-DD-campaign-name directories. Use for new campaign setup, Meta Ads and social media campaign planning, creative/copy revision tracking, UTM revisions, or generating campaign performance reports using adsctl and google-analytics-analyst.
---

# Campaign Manager

Own both marketing operations (shared workspace layout, paid-ad and social-media platform hierarchies, campaign documentation/plans, timestamped performance reports, taxonomy and traceability) and campaign management (campaign goals/budgets, ad-set targeting, per-ad and per-post copy/caption and asset revision tracking, usable links, and cross-channel performance analysis). Save the work in the user's current workspace so it can be reviewed and committed. Managing campaign records or generating UTMs does not authorize campaign publication, ad-account changes or analytics implementation.

## Find or initialize the campaign directory

Read workspace guidance, existing campaign directories, briefs and tagging conventions first. Reuse the user's campaign root; otherwise use `marketing/campaigns/` under the current workspace. Never save campaign work inside the installed plugin. Use [workspace-records.md](references/workspace-records.md) to create or resume the campaign directory and `INDEX.md` without overwriting unrelated material.

For a new campaign, create its directory in `<YYYY-MM-DD>-<campaign-name>` format (for example `2026-10-18-taskapp-activation`), using the campaign creation or planned start date in ISO `YYYY-MM-DD` format followed by a lowercase hyphenated campaign slug, and use that same slug as the local `campaign_id`. When resuming an existing campaign in a later session or on a later date, reuse its existing directory and `campaign_id`—do not duplicate or rename an active campaign directory just because the calendar date changed.

Start from the supplied product, campaign, brief, copy or assets. Keep the campaign root clean with `README.md` (the single campaign entrypoint) and `campaign.json` (the canonical link plan), store campaign-level markdown documents, briefs, and plans under `docs/` (`docs/MARKETING_BRIEF.md`, `docs/MEASUREMENT.md`, `docs/CHANGELOG.md`, `docs/plans/`, and `docs/reviews/`), and store chronological campaign performance analyses under `reports/<datetime>.md`. For a URL-only request, establish just the destination, distribution sources/media, campaign identity and variants, and create only the directories needed for that task. Ask only about missing facts that change the links or structure; draft unresolved decisions without inventing destinations, platform IDs, offers, budgets or a launch date. Use [marketing-brief](../marketing-brief/SKILL.md) when broader strategy is requested or materially missing, and save `docs/MARKETING_BRIEF.md` in this campaign's directory. Do not restart intake for an existing brief.

## Structure campaign documents (`docs/`), reports (`reports/`), paid ad platforms (`meta-ads`), and social media channels (`instagram`, `linkedin`, `twitter`)

Under `<YYYY-MM-DD>-<campaign-name>/`, organize campaign documents/plans, performance reports, paid ads, and social media campaigns in sibling top-level directories (see [workspace-records.md](references/workspace-records.md), [reporting.md](references/reporting.md), [meta-ads.md](references/meta-ads.md), and [social-media.md](references/social-media.md)):

0. **Campaign Documents (`docs/`) & Performance Reports (`reports/`):**
   - Keep `README.md` and `campaign.json` at the root of `<YYYY-MM-DD>-<campaign-name>/` and place all campaign-level strategy markdowns and plans inside `docs/`:
     - `docs/MARKETING_BRIEF.md`, `docs/MEASUREMENT.md`, and `docs/CHANGELOG.md` for core campaign strategy, attribution/measurement, and dated revision history.
     - `docs/plans/` for campaign-wide or cross-channel plans, creative ideation docs (`CREATIVE_IDEAS.md`), cross-platform distribution plans (`CROSS_PLATFORM.md`), carousel/content plans, and shooting plans.
     - `docs/reviews/` for product feature evidence registers, QA/review reports, and delivery/repository handoffs.
   - Place chronological campaign performance and funnel analysis reports inside top-level **`reports/<datetime>.md`** (for example `reports/2026-10-19-2200.md` or `reports/2026-10-19T22-00-00+07-00.md`; see [reporting.md](references/reporting.md)).
   - Ad-specific or post-specific scripts, beat sheets, visual direction, and creative QA reviews live inside that ad's or post's `assets/development/storyboard/` (or `<ad-or-post>/docs/`).
1. **Meta Ads (`meta-ads/campaigns/<meta-campaign-slug>/adsets/<adset-slug>/ads/<ad-slug>/`):**
   - **Meta Campaign (`meta-ads/campaigns/<meta-campaign-slug>/campaign.json`):** Default to **Advantage+ campaign budget** (`budget.mode: "advantage_plus"`, with `"cbo"` accepted as a legacy alias and `"abo"` only when explicit ad-set budgets are required). Record the campaign goal (`objective`, such as `OUTCOME_SALES` or `OUTCOME_TRAFFIC`), buying type (`"AUCTION"`), `budget` (`mode: "advantage_plus" | "cbo" | "abo"`, `currency`, `daily_budget` / `lifetime_budget`, optional `spend_cap`, `bid_strategy` such as `"LOWEST_COST_WITHOUT_CAP"`, and `is_adset_budget_sharing_enabled: false` for Advantage+ campaign budget), special ad categories, and status.
   - **Meta Ad Set (`.../adsets/<adset-slug>/adset.json`):** Inside each Meta campaign, create one or more ad sets under `adsets/<adset-slug>/`. Default to **Advantage+ placements** (`placements.mode: "advantage_plus"`) and inherited Advantage+ campaign budget (`budget: {"mode": "advantage_plus", "inherited_from_campaign": true}`). Record `optimization_goal`, `billing_event`, conversion pixel/event, schedule, `budget`, **user targeting** (`targeting`: geo locations, age range, gender, locales, detailed targeting interests/behaviors, custom/lookalike audiences, exclusions — omitting `publisher_platforms` and `*_positions` when `placements.mode` is `"advantage_plus"`), and `placements` (`mode: "advantage_plus" | "manual"`, optional `placement_soft_opt_out`, and `required_ratios`: `["16:9", "9:16", "4:5", "1:1"]`; only specify `publisher_platforms` and `*_positions` when `mode` is `"manual"`).
   - **Meta Ad (`.../ads/<ad-slug>/`):** Inside each ad set, create one or more ad directories under `ads/<ad-slug>/`. Each ad contains `ad.json` (format, `call_to_action`, `link_id`, clean `destination_url`, `utm`, serialized `url_tags`, and `approved_copy_revision` / `approved_assets_revision`), `copy/drafts/`, `copy/approved/v001/` (`v002/`, ...), `assets/development/{storyboard,images,video,audio}/`, and `assets/approved/v001/` (`v002/`, ...).
2. **Social Media Campaigns (`instagram/`, `linkedin/`, `twitter/`):**
   - Sit at the same directory level as `meta-ads/` under `<YYYY-MM-DD>-<campaign-name>/`.
   - Under `<platform>/posts/<post-slug>/` (where `<platform>` is `instagram`, `linkedin`, or `twitter`), each social post, reel, story, carousel, thread, or article self-contains:
     - **`post.json`:** Post `platform`, `post_slug`, `name`, `status`, `format` (`single_image`, `carousel`, `video`, `reel`, `story`, `text`, `thread`, `document`, `article`), optional `schedule`, optional tracked link mapping (`link_id`, `destination_url`, `utm`, `url`), and active revision pointers (`approved_copy_revision`, `approved_assets_revision`).
     - **`copy/drafts/` and `copy/approved/v001/` (`v002/`, ...):** Working and user-approved captions, hooks, thread tweets, slide copy, hashtags, first-comment links, and accessibility alt text.
     - **`assets/development/` and `assets/approved/v001/` (`v002/`, ...):** Storyboard/media development (`storyboard/`, `images/`, `video/`, `audio/`) and versioned approved deliverables (`images/`, `video/`, `audio/` plus `MANIFEST.md` or `assets.json`).
3. **Accessibility alt text via `marketing-copywriter` whenever images, videos, or visual assets are created:**
   - Whenever images, carousel slides, videos, or other visual assets are created, imported, or updated for an ad (`meta-ads/.../ads/<ad-slug>/`) or social post (`{instagram,linkedin,twitter}/posts/<post-slug>/`), ask [marketing-copywriter](../marketing-copywriter/SKILL.md) (`$marketing-copywriter`) to write clear accessibility alt text for each visual asset (including per-slide alt text for carousels and descriptive alt/thumbnail text for videos).
   - Keep working alt text in `copy/drafts/` alongside the ad or post copy, and promote the reviewed alt text into `copy/approved/v001/` (`v002/`, ...) so every visual deliverable has matching accessibility copy before handoff.
4. **Reuse and copy approved assets across ads and social media (avoid redundant generation):**
   - Do **not** regenerate images, videos, or audio for social media (`instagram/`, `linkedin/`, `twitter/`) when a suitable approved asset already exists in `meta-ads/` (or another social channel), and vice versa (`meta-ads/` reusing an asset already created for social media).
   - Instead of calling paid image/video generators again, copy the approved deliverable from the source `assets/approved/vNNN/` directory into the target ad's or post's `assets/approved/v001/` directory so each ad or social post keeps a complete, self-contained record, and note the source path and hash in its `MANIFEST.md` / `assets.json`.
   - When an ad or social post reuses/copies an approved asset from another directory, **it does not need an `assets/development/` directory**—omit `assets/development/` rather than creating empty or duplicate development folders, and ensure `copy/drafts/` and `copy/approved/vNNN/` still include accessibility alt text for the reused visual asset (reusing or adapting the alt text via [marketing-copywriter](../marketing-copywriter/SKILL.md)).

Create only the platform (`meta-ads/`, `instagram/`, `linkedin/`, `twitter/`), `reports/`, campaign/adset/ad/post, copy and asset directories that the current workflow actually uses or that the user asks to scaffold. Never overwrite prior `vNNN` directories in `copy/approved/`, `assets/approved/`, `tracking/`, or existing `reports/<datetime>.md` files.

## Define and apply the UTM convention

Read [utm-conventions.md](references/utm-conventions.md). Reuse the workspace taxonomy and exact existing values. When there is none, propose and document a compact convention, then apply it consistently. Separate stable campaign/link/creative IDs from display names; record who owns unresolved decisions.

Use one campaign identity across its links, source/medium for distribution, and `utm_content` to distinguish relevant ad, post, creative, copy or placement variants. For Meta ads, set `"platform": "meta-ads"`, `"platform_campaign": "<meta-campaign-slug>"`, `"adset": "<adset-slug>"`, and `"ad": "<ad-slug>"` on the corresponding link in root `campaign.json`. For social media posts with a tracked outbound link, set `"platform": "instagram" | "linkedin" | "twitter"` and `"post": "<post-slug>"`. Align `creative_id` and `utm_content` with the ad's or post's approved copy and asset revisions. Add optional IDs, platform or terms only with a defined meaning. Keep personal information and credentials out of URLs and records. Preserve auto-tagging and click identifiers; do not add UTMs to internal navigation. Dynamic provider macros require current official verification; the bundled helper supports static values only.

## Generate and retain the URLs

Create or update root `campaign.json` (and any `meta-ads/campaigns/<campaign-slug>/.../ad.json` or `{instagram,linkedin,twitter}/posts/<post-slug>/post.json` specs) using the [link plan contract](references/link-plan.md), [Meta Ads hierarchy contract](references/meta-ads.md), [social media structure](references/social-media.md) and [fictional example](assets/campaign.example.json). Keep the full link inventory, including published/retired entries. Run the local helper with Python 3.10+ (standard library only):

```sh
python3 <skill-dir>/scripts/build_utm.py <campaign-dir>/campaign.json --dry-run
python3 <skill-dir>/scripts/build_utm.py <campaign-dir>/campaign.json --out <campaign-dir>/tracking/v001
```

Replace the placeholders with resolved paths; choose the next unused revision. Dry-run validates and previews URLs, `url_tags`, every Meta campaign/adset/ad specification (when `<campaign-dir>/meta-ads/campaigns/` exists or `--meta-ads-dir` is supplied), and every social media post specification (when `<campaign-dir>/{instagram,linkedin,twitter}/posts/` exists) without writing or contacting a service. A real run saves the input snapshot, `utm-links.csv` (including platform/hierarchy columns and `url_tags`) and `UTM_PLAN.md` in a fresh directory. Existing UTMs in `destination_url` cause an error rather than silent replacement; resolve their ownership before rebuilding. The helper preserves other query bytes and fragments.

Compare revisions before delivery. Never change a published link's meaning under the same ID: preserve it and add a new ID for a changed destination, tracking tuple or materially different creative/copy revision when separate measurement is needed. Record replacements, retirement and the reason. Update campaign notes, `ad.json` / `post.json` and the shared index with the current tracking, approved copy and approved asset revision paths.

## Analyze campaign performance and write `reports/<datetime>.md`

When the user asks to evaluate how a campaign is performing, audit funnel drop-offs, or record a campaign performance report, follow [reporting.md](references/reporting.md):

1. **Gather multi-source evidence using companion skills:**
   - Use `$adsctl` and `$adsctl-meta-analyst` to pull Meta Ads delivery, creative hook/hold rates, outbound clicks, placement breakdowns, and ad-level status.
   - Use [google-analytics-analyst](../google-analytics-analyst/SKILL.md) (`$google-analytics-analyst`) and its `scripts/ga4_report.py` helper to pull GA4 / Firebase Analytics sessions, new users, click-to-session connect rates, engagement rates, session durations, and step-by-step product/checkout funnel events by `utm_campaign` (`sessionCampaignName`) and `utm_content` (`sessionManualAdContent`).
   - When first-party backend/database access is in scope, cross-check consent records, user registrations, and initiated/completed transactions.
2. **Write `<campaign-dir>/reports/<datetime>.md`:**
   - Create a new timestamped markdown file under `reports/` (such as `reports/2026-10-19-2200.md` or `reports/2026-10-19T22-00-00+07-00.md`; never overwrite previous reports).
   - Structure the report with all required sections from [reporting.md](references/reporting.md): **Executive Verdict**, **Multi-Source Funnel Scorecard**, **Creative Variant & Placement Breakdown**, **What Went Well**, **What Went Wrong**, **What Can Be Improved & Recommendations**, **Actions Taken** (recording any live ad pauses, budget changes, code/tracking deployments, or config updates executed), **Lessons Learned**, **Action Items & Next Checkpoints**, and **Scope & Provenance Footer**.
3. **Synchronize campaign metadata:**
   - If live actions were taken (for example pausing an underperforming ad variant or updating tracking parameters), update the corresponding `ad.json` / `post.json`, `docs/MEASUREMENT.md`, `docs/CHANGELOG.md`, and link the new report in root `README.md`.

## Verify and hand off

Check the generated values against the taxonomy, campaign brief, `meta-ads` campaign/adset/ad specs, social media `post.json` specs, and current approved copy/asset revisions (`copy/approved/vNNN/`, `assets/approved/vNNN/`), including creative IDs, accessibility alt text for created/approved images and videos, and destination ownership. Record local checks separately from live checks. Follow [workspace-records.md](references/workspace-records.md) and [reporting.md](references/reporting.md) for redirect, consent/analytics, conversion and performance-report checks when available within scope; unperformed checks stay pending. A valid URL does not prove attribution or performance.

Return the campaign directory path, active platform hierarchies (`meta-ads/campaigns/.../adsets/.../ads/...` and/or `{instagram,linkedin,twitter}/posts/...`), active approved copy/asset revisions, current tracking revision, any generated `reports/<datetime>.md` path, usable links, `url_tags` and field mapping for the publishing owner, and remaining checks. Keep text records suitable for Git; follow workspace commit rules, but do not stage, commit or push merely because this skill ran.
