---
name: campaign-manager
description: Define campaign workspace structure, multi-platform ad hierarchies (starting with Meta campaign, ad set, and ad folders), UTM conventions, and tagged product campaign links; organize per-ad storyboard and media development, versioned approved assets and copy revisions, and tracking records in YYYY-MM-DD-campaign-name directories. Use for new campaign setup, Meta campaign/adset/ad planning, creative/copy revision tracking, or revisions to existing UTMs.
---

# Campaign Manager

Own both marketing operations (shared workspace layout, multi-platform hierarchy, taxonomy and traceability) and campaign management (campaign goals/budgets, ad-set targeting, per-ad copy/asset revision tracking and usable links). Save the work in the user's current workspace so it can be reviewed and committed. Managing campaign records or generating UTMs does not authorize campaign publication, ad-account changes or analytics implementation.

## Find or initialize the campaign directory

Read workspace guidance, existing campaign directories, briefs and tagging conventions first. Reuse the user's campaign root; otherwise use `marketing/campaigns/` under the current workspace. Never save campaign work inside the installed plugin. Use [workspace-records.md](references/workspace-records.md) to create or resume the campaign directory and `INDEX.md` without overwriting unrelated material.

For a new campaign, create its directory in `<YYYY-MM-DD>-<campaign-name>` format (for example `2026-10-18-taskapp-activation`), using the campaign creation or planned start date in ISO `YYYY-MM-DD` format followed by a lowercase hyphenated campaign slug, and use that same slug as the local `campaign_id`. When resuming an existing campaign in a later session or on a later date, reuse its existing directory and `campaign_id`—do not duplicate or rename an active campaign directory just because the calendar date changed.

Start from the supplied product, campaign, brief, copy or assets. For a URL-only request, establish just the destination, distribution sources/media, campaign identity and variants, and create only the directories needed for that task. Ask only about missing facts that change the links or structure; draft unresolved decisions without inventing destinations, platform IDs, offers, budgets or a launch date. Use [marketing-brief](../marketing-brief/SKILL.md) when broader strategy is requested or materially missing, and save `MARKETING_BRIEF.md` in this campaign's directory. Do not restart intake for an existing brief.

## Structure ad platforms and creative lifecycles (starting with Meta)

Under `<YYYY-MM-DD>-<campaign-name>/`, organize paid media by ad platform—starting with `meta/`—using that platform's native hierarchy (see [meta-ads.md](references/meta-ads.md) and [workspace-records.md](references/workspace-records.md)):

1. **Meta Campaign (`meta/campaigns/<meta-campaign-slug>/campaign.json`):** Record the campaign goal (`objective`, such as `OUTCOME_SALES` or `OUTCOME_TRAFFIC`), buying type, budget mode and budget limits (`budget` with `mode: "cbo" | "abo"`, `currency`, `daily_budget` / `lifetime_budget`, `spend_cap`, `bid_strategy`), special ad categories, and status.
2. **Meta Ad Set (`.../adsets/<adset-slug>/adset.json`):** Inside each Meta campaign, create one or more ad sets under `adsets/<adset-slug>/`. Record `optimization_goal`, `billing_event`, conversion pixel/event, schedule, ad-set budget (when ABO), **user targeting** (`targeting`: geo locations, age range, gender, locales, detailed targeting interests/behaviors, custom/lookalike audiences, exclusions), and `placements` (platforms, positions, and required creative aspect ratios `16:9`, `9:16`, `4:5`, `1:1`).
3. **Meta Ad (`.../ads/<ad-slug>/`):** Inside each ad set, create one or more ad directories under `ads/<ad-slug>/`. Every ad self-contains its destination link/UTM spec (`ad.json`), copy lifecycle (`copy/`), and creative asset lifecycle (`assets/`):
   - **`ad.json`:** Ad format (`video`, `single_image`, `carousel`), `call_to_action`, `link_id` (referencing root `campaign.json`), clean `destination_url` (Meta Website URL), `utm` object, serialized `url_tags` (Meta URL parameters), and active revision pointers (`approved_copy_revision`, `approved_assets_revision`).
   - **`copy/drafts/` and `copy/approved/v001/` (`v002/`, ...):** Keep working primary text, headlines, descriptions, overlay text and voice/style explorations in `copy/drafts/`. Save user-approved ad copy in versioned immutable directories under `copy/approved/v001/`, `copy/approved/v002/`, and so on.
   - **`assets/development/` and `assets/approved/v001/` (`v002/`, ...):** Keep work-in-progress creative production for this ad under `assets/development/storyboard/` (concepts, scripts, visual direction, beat sheets, `storyboard.json`, resolved timing), `assets/development/images/` (references, contact-sheet boards, cropped tile previews, candidate renders), `assets/development/video/` (video projects, custom scene generators, Veo/Omni runs, draft renders/QA), and `assets/development/audio/` (`voice-config.json`, raw/normalized narration takes, alignment files, pause rules, music/SFX). Place reviewed, approved deliverables in versioned directories under `assets/approved/v001/`, `assets/approved/v002/`, and so on (`images/`, `video/`, `audio/` plus `MANIFEST.md` or `assets.json`). When multiple ads intentionally share the same approved creative deliverable, `ad.json` can reference the sibling ad's `assets/approved/vNNN` directory rather than duplicating paid renders.

Create only the platform, campaign, adset, ad, copy and asset directories that the current workflow actually uses or that the user asks to scaffold. Never overwrite prior `vNNN` directories in `copy/approved/`, `assets/approved/` or `tracking/`.

## Define and apply the UTM convention

Read [utm-conventions.md](references/utm-conventions.md). Reuse the workspace taxonomy and exact existing values. When there is none, propose and document a compact convention, then apply it consistently. Separate stable campaign/link/creative IDs from display names; record who owns unresolved decisions.

Use one campaign identity across its links, source/medium for distribution, and `utm_content` to distinguish relevant ad, creative, copy or placement variants. For Meta ads, set `"platform": "meta"`, `"platform_campaign": "<meta-campaign-slug>"`, `"adset": "<adset-slug>"`, and `"ad": "<ad-slug>"` on the corresponding link in root `campaign.json` and align `creative_id` and `utm_content` with the ad's approved copy and asset revisions. Add optional IDs, platform or terms only with a defined meaning. Keep personal information and credentials out of URLs and records. Preserve auto-tagging and click identifiers; do not add UTMs to internal navigation. Dynamic provider macros require current official verification; the bundled helper supports static values only.

## Generate and retain the URLs

Create or update root `campaign.json` (and any `meta/campaigns/<campaign-slug>/.../ad.json` specs) using the [link plan contract](references/link-plan.md), [Meta hierarchy contract](references/meta-ads.md) and [fictional example](assets/campaign.example.json). Keep the full link inventory, including published/retired entries. Run the local helper with Python 3.10+ (standard library only):

```sh
python3 <skill-dir>/scripts/build_utm.py <campaign-dir>/campaign.json --dry-run
python3 <skill-dir>/scripts/build_utm.py <campaign-dir>/campaign.json --out <campaign-dir>/tracking/v001
```

Replace the placeholders with resolved paths; choose the next unused revision. Dry-run validates and previews URLs, `url_tags`, and (when `<campaign-dir>/meta/campaigns/` exists or `--meta-dir` is supplied) every Meta campaign, ad set, and ad specification without writing or contacting a service. A real run saves the input snapshot, `utm-links.csv` (including platform/campaign/adset/ad columns and `url_tags`) and `UTM_PLAN.md` in a fresh directory. Existing UTMs in `destination_url` cause an error rather than silent replacement; resolve their ownership before rebuilding. The helper preserves other query bytes and fragments.

Compare revisions before delivery. Never change a published link's meaning under the same ID: preserve it and add a new ID for a changed destination, tracking tuple or materially different creative/copy revision when separate measurement is needed. Record replacements, retirement and the reason. Update campaign notes, `ad.json` and the shared index with the current tracking, approved copy and approved asset revision paths.

## Verify and hand off

Check the generated values against the taxonomy, campaign brief, Meta campaign/adset/ad specs, and current approved copy/asset revisions (`copy/approved/vNNN/`, `assets/approved/vNNN/`), including creative IDs and destination ownership. Record local checks separately from live checks. Follow [workspace-records.md](references/workspace-records.md) for redirect, consent/analytics and conversion checks when available within scope; unperformed checks stay pending. A valid URL does not prove attribution or performance.

Return the campaign directory path, platform hierarchy (`meta/campaigns/.../adsets/.../ads/...`), active approved copy/asset revisions, current tracking revision, usable links, `url_tags` and field mapping for the ad-publishing owner, and remaining checks. Keep text records suitable for Git; follow workspace commit rules, but do not stage, commit or push merely because this skill ran.
