---
name: campaign-manager
description: Define campaign workspace structure, UTM conventions, and tagged product campaign links; organize storyboard and media development, versioned approved assets, copy drafts and approved revisions, and tracking records in YYYY-MM-DD-campaign-name directories. Use for new campaign setup, creative/copy revision tracking, or revisions to existing UTMs.
---

# Campaign Manager

Own both marketing operations (shared workspace layout, taxonomy and traceability) and campaign management (campaign decisions, copy/asset revision tracking and usable links). Save the work in the user's current workspace so it can be reviewed and committed. Managing campaign records or generating UTMs does not authorize campaign publication, ad-account changes or analytics implementation.

## Find or initialize the campaign directory

Read workspace guidance, existing campaign directories, briefs and tagging conventions first. Reuse the user's campaign root; otherwise use `marketing/campaigns/` under the current workspace. Never save campaign work inside the installed plugin. Use [workspace-records.md](references/workspace-records.md) to create or resume the campaign directory and `INDEX.md` without overwriting unrelated material.

For a new campaign, create its directory in `<YYYY-MM-DD>-<campaign-name>` format (for example `2026-10-18-taskapp-activation`), using the campaign creation or planned start date in ISO `YYYY-MM-DD` format followed by a lowercase hyphenated campaign slug, and use that same slug as the local `campaign_id`. When resuming an existing campaign in a later session or on a later date, reuse its existing directory and `campaign_id`—do not duplicate or rename an active campaign directory just because the calendar date changed.

Start from the supplied product, campaign, brief, copy or assets. For a URL-only request, establish just the destination, distribution sources/media, campaign identity and variants, and create only the directories needed for that task. Ask only about missing facts that change the links or structure; draft unresolved decisions without inventing destinations, platform IDs, offers or a launch date. Use [marketing-brief](../marketing-brief/SKILL.md) when broader strategy is requested or materially missing, and save `MARKETING_BRIEF.md` in this campaign's directory. Do not restart intake for an existing brief.

## Organize copy and creative asset lifecycles

Keep exploratory drafts and work-in-progress production separate from approved deliverables inside `<YYYY-MM-DD>-<campaign-name>/` (see [workspace-records.md](references/workspace-records.md)):

- **Copywriting (`copy/`):** Keep working drafts, voice/style explorations, localization work-in-progress and review notes in `copy/drafts/`. Save user-approved copy in versioned immutable directories under `copy/approved/v001/`, `copy/approved/v002/`, and so on.
- **Storyboard and asset development (`assets/development/`):** Keep work-in-progress creative material organized by role under `assets/development/storyboard/` (concepts, scripts, visual direction, beat sheets, `storyboard.json`, resolved timing), `assets/development/images/` (references, contact-sheet boards, cropped tile previews, candidate renders), `assets/development/video/` (video projects, custom scene generators, Veo/Omni generation runs, draft renders/QA snapshots), and `assets/development/audio/` (voice configs, raw/normalized narration takes, alignment files, pause rules, music/SFX).
- **Approved assets (`assets/approved/`):** Place reviewed, approved deliverables into versioned directories under `assets/approved/v001/`, `assets/approved/v002/`, and so on, organized by modality (`images/`, `video/`, `audio/`) with a manifest or summary (`MANIFEST.md` or `assets.json`) recording stable `creative_id` values, ratios, file hashes and source development paths. Multiple revisions of approved assets and approved copy are normal; always create the next unused `vNNN` directory rather than overwriting prior approved revisions.

Create only the subdirectories that the current workflow actually uses or that the user asks to scaffold.

## Define and apply the UTM convention

Read [utm-conventions.md](references/utm-conventions.md). Reuse the workspace taxonomy and exact existing values. When there is none, propose and document a compact convention, then apply it consistently. Separate stable campaign/link/creative IDs from display names; record who owns unresolved decisions.

Use one campaign identity across its links, source/medium for distribution, and `utm_content` to distinguish relevant creative, copy or placement variants. Align `creative_id` and `utm_content` with the stable variant IDs in `copy/approved/vNNN/` and `assets/approved/vNNN/`. Add optional IDs, platform or terms only with a defined meaning. Keep personal information and credentials out of URLs and records. Preserve auto-tagging and click identifiers; do not add UTMs to internal navigation. Dynamic provider macros require current official verification; the bundled helper supports static values only.

## Generate and retain the URLs

Create or update `campaign.json` using the [link plan contract](references/link-plan.md) and [fictional example](assets/campaign.example.json). Keep the full link inventory, including published/retired entries. Run the local helper with Python 3.10+ (standard library only):

```sh
python3 <skill-dir>/scripts/build_utm.py <campaign-dir>/campaign.json --dry-run
python3 <skill-dir>/scripts/build_utm.py <campaign-dir>/campaign.json --out <campaign-dir>/tracking/v001
```

Replace the placeholders with resolved paths; choose the next unused revision. Dry-run validates and previews URLs without writing or contacting a service. A real run saves the input snapshot, `utm-links.csv` and `UTM_PLAN.md` in a fresh directory. Existing UTMs cause an error rather than silent replacement; resolve their ownership before rebuilding. The helper preserves other query bytes and fragments.

Compare revisions before delivery. Never change a published link's meaning under the same ID: preserve it and add a new ID for a changed destination, tracking tuple or materially different creative/copy revision when separate measurement is needed. Record replacements, retirement and the reason. Update campaign notes and the shared index with the current tracking, approved copy and approved asset revision paths.

## Verify and hand off

Check the generated values against the taxonomy, campaign brief, and current approved copy/asset revisions (`copy/approved/vNNN/`, `assets/approved/vNNN/`), including creative IDs and destination ownership. Record local checks separately from live checks. Follow [workspace-records.md](references/workspace-records.md) for redirect, consent/analytics and conversion checks when available within scope; unperformed checks stay pending. A valid URL does not prove attribution or performance.

Return the campaign directory path, active approved copy/asset revisions, current tracking revision, usable links, naming decisions and remaining checks. Include the exact destination URLs, approved copy/asset paths and field mapping for the ad-publishing owner. Keep text records suitable for Git; follow workspace commit rules, but do not stage, commit or push merely because this skill ran.
