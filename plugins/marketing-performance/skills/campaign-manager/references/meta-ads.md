# Meta Ads campaign, ad set, and ad hierarchy

Under `<YYYY-MM-DD>-<campaign-name>/meta-ads/`, organize campaigns, ad sets, and ads to mirror Meta Ads' three-tier hierarchy (`Campaign → Ad Set → Ad`). Each level owns the decisions that belong to that Meta object, and each ad directory owns its destination link/UTM mapping, copy revisions, and creative asset development/approved revisions:

```text
<YYYY-MM-DD>-<campaign-name>/
  campaign.json                          # canonical campaign-wide link plan
  tracking/
    v001/
      campaign.json
      utm-links.csv
      UTM_PLAN.md
  meta-ads/
    README.md                            # optional Meta account, pixel, and page notes
    campaigns/
      <meta-campaign-slug>/
        campaign.json                    # Meta campaign goal, buying type, and budget limit
        adsets/
          <adset-slug>/
            adset.json                   # optimization goal, schedule, placements, and user targeting
            ads/
              <ad-slug>/
                ad.json                  # ad format, CTA, destination_url, utm, url_tags, link_id, and active revisions
                copy/
                  drafts/                # working primary text, headline, description, alt text, and style explorations
                  approved/
                    v001/                # approved ad copy and accessibility alt text revision
                    v002/                # subsequent approved ad copy revision
                assets/
                  development/
                    storyboard/          # concepts, scripts, style direction, beat sheets, storyboard.json
                    images/              # references, contact-sheet boards, cropped tiles, candidate renders
                    video/               # Video Studio projects, scene generators and Gemini/Higgsfield runs, draft renders/QA
                    audio/               # voice configs, raw/normalized narration takes, alignment, music/SFX
                  approved/
                    v001/                # approved deliverable revision ready for publishing
                      MANIFEST.md        # or assets.json: creative_id, ratios, hashes, Meta media IDs
                      images/            # approved final image/carousel deliverables
                      video/             # approved final encoded video deliverables (16:9, 9:16, 4:5, 1:1)
                      audio/             # approved standalone audio/voiceover deliverables when needed
                    v002/                # subsequent approved asset revision
```

Social media campaign directories (`instagram/`, `linkedin/`, `twitter/`; see [social-media.md](social-media.md)) and future paid ad platforms sit alongside `meta-ads/` under `<YYYY-MM-DD>-<campaign-name>/` while sharing the root `campaign.json` and `tracking/vNNN/` registry.

## 1. Meta Campaign level (`meta-ads/campaigns/<meta-campaign-slug>/campaign.json`)

Captures the campaign goal (objective), **Advantage+ campaign budget** configuration (default), bid strategy, special ad categories, and lifecycle status:

```json
{
  "schema_version": 1,
  "platform": "meta-ads",
  "campaign_slug": "taskapp-activation-sales",
  "name": "TaskApp | ID Activation | Sales | 2026-10-18",
  "objective": "OUTCOME_SALES",
  "buying_type": "AUCTION",
  "special_ad_categories": ["NONE"],
  "budget": {
    "mode": "advantage_plus",
    "currency": "IDR",
    "daily_budget": 100000,
    "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
    "is_adset_budget_sharing_enabled": false
  },
  "status": "planned"
}
```

- `campaign_slug`: lowercase hyphenated slug matching the `<meta-campaign-slug>` folder name.
- `objective`: Meta campaign goal, such as `OUTCOME_SALES`, `OUTCOME_TRAFFIC`, `OUTCOME_LEADS`, `OUTCOME_ENGAGEMENT`, `OUTCOME_APP_PROMOTION`, or `OUTCOME_AWARENESS`.
- `budget`:
  - **Default — Advantage+ campaign budget (`"mode": "advantage_plus"`)**: Meta dynamically distributes the campaign budget across ad sets in real time (`"cbo"` is also accepted as a backward-compatible alias). Include `currency`, either `daily_budget` or `lifetime_budget` (not both), `bid_strategy` (defaults to `"LOWEST_COST_WITHOUT_CAP"`), optional `spend_cap`, and `"is_adset_budget_sharing_enabled": false`. In native Meta Graph API / `adsctl` payloads, Advantage+ campaign budget sets `daily_budget` or `lifetime_budget` and `bid_strategy` on the Campaign object (`adsctl meta campaigns create --advantage-budget --daily-budget-minor ...`) while omitting budget fields on child ad sets.
  - **Ad-set budget override (`"mode": "abo"`)**: Use only when explicit per-ad-set budgets are required. Omit `daily_budget` and `lifetime_budget` on the campaign (or set them to `null`), and optionally set `"is_adset_budget_sharing_enabled": true | false`.
  - Do not invent budgets or currency values when unsupplied.
- `status`: `"planned"`, `"paused"`, `"active"`, `"archived"`, or `"retired"`. Optional `remote_campaign_id` records the live Meta Campaign ID once created.

## 2. Meta Ad Set level (`.../adsets/<adset-slug>/adset.json`)

Captures user targeting, **Advantage+ placements** (default) and required aspect ratios for creative production, conversion event/pixel optimization, schedule, and inherited Advantage+ campaign budget (or ad-set budget when `budget.mode` is `"abo"`):

```json
{
  "schema_version": 1,
  "adset_slug": "id-18-45-design-teams",
  "name": "ID 18-45 | Design Teams | Advantage+ Placements",
  "optimization_goal": "OFFSITE_CONVERSIONS",
  "billing_event": "IMPRESSIONS",
  "conversion": {
    "destination_type": "WEBSITE",
    "pixel_id": "1855259662305866",
    "custom_event_type": "PURCHASE"
  },
  "budget": {
    "mode": "advantage_plus",
    "inherited_from_campaign": true
  },
  "targeting": {
    "geo_locations": {
      "countries": ["ID"]
    },
    "age_min": 18,
    "age_max": 45,
    "interests": ["Design", "Project management"],
    "advantage_audience": false
  },
  "placements": {
    "mode": "advantage_plus",
    "placement_soft_opt_out": false,
    "required_ratios": ["9:16", "4:5", "1:1"]
  },
  "status": "planned"
}
```

- `adset_slug`: lowercase hyphenated slug matching the `<adset-slug>` folder name.
- `budget`:
  - When the parent campaign uses **Advantage+ campaign budget** (`"mode": "advantage_plus"` or `"cbo"`), set `"budget": {"mode": "advantage_plus", "inherited_from_campaign": true}` (or omit `daily_budget` / `lifetime_budget`). Never set a positive `daily_budget` or `lifetime_budget` on the ad set when the campaign owns the budget; optional `daily_min_spend_target`, `daily_spend_cap`, `lifetime_min_spend_target`, or `lifetime_spend_cap` may be recorded if ad-set spend limits are used.
  - When the parent campaign uses `"mode": "abo"`, record `currency` and `daily_budget` or `lifetime_budget` on the ad set.
- `targeting`: nonempty object recording the audience hypothesis and targeting parameters (locations, age range, genders, locales, detailed targeting interests/behaviors, custom/lookalike audiences, `advantage_audience`, and exclusions). Do **not** embed `publisher_platforms` or `*_positions` inside `targeting` when `placements.mode` is `"advantage_plus"`.
- `placements`:
  - **Default — Advantage+ placements (`"mode": "advantage_plus"`)**: Allows Meta's delivery system to dynamically allocate impressions across all eligible placements (Instagram Reels/Stories/Feed/Explore, Facebook Reels/Feed/Stories/In-Stream/Search, WhatsApp Status, Messenger, Threads, and Audience Network) to find the lowest-cost conversions.
    - When `"mode": "advantage_plus"`, **omit `publisher_platforms`, `facebook_positions`, `instagram_positions`, `messenger_positions`, `audience_network_positions`, and `threads_positions`** (or leave them empty `[]`), and do not set them in `targeting`. `build_utm.py` rejects non-empty platform/position restriction lists when `"mode": "advantage_plus"` so local `adset.json` files never drift from live Advantage+ placement behavior.
    - Include `required_ratios` (`16:9`, `9:16`, `4:5`, `1:1`; or `aspect_ratios`) so downstream image and video skills produce the creative aspect ratios needed across vertical and feed placements, plus optional `placement_soft_opt_out` (`true` or `false`) and optional `device_platforms` (`["mobile", "desktop"]`).
    - In `adsctl`, create or update Advantage+ placement ad sets with `--advantage-placements` (`adsctl meta adsets create --file adset.json --advantage-placements`), `adsctl meta adsets placements set ID --advantage-plus`, or `advantage_placements: true` on the adset node in a `launch.yaml` manifest.
  - **Manual placements override (`"mode": "manual"`)**: Use only when the user explicitly requests restricted placements. Set `"mode": "manual"`, a non-empty `"publisher_platforms"` array (such as `["instagram", "facebook"]`), the corresponding `*_positions` arrays (`instagram_positions`, `facebook_positions`, etc.), and `required_ratios`.
- Optional `schedule` (`start_time`, `end_time`, `timezone`) and `remote_adset_id`.

## 3. Meta Ad level (`.../ads/<ad-slug>/ad.json`)

Binds a single ad's destination URL and UTM parameters (`link_id` in root `campaign.json`) to its approved copy revision (`copy/approved/vNNN`) and approved creative asset revision (`assets/approved/vNNN`):

```json
{
  "schema_version": 1,
  "ad_slug": "reels-demo-v1",
  "name": "Reels Demo v1 | Start Page",
  "status": "planned",
  "format": "video",
  "call_to_action": "LEARN_MORE",
  "link_id": "instagram-reels-demo-v1",
  "destination_url": "https://example.com/start?lang=id#demo",
  "utm": {
    "utm_source": "instagram",
    "utm_medium": "paid_social",
    "utm_campaign": "taskapp-activation-id-2026q4",
    "utm_id": "2026-10-18-example-taskapp-activation",
    "utm_content": "demo-v1-reels"
  },
  "url_tags": "utm_source=instagram&utm_medium=paid_social&utm_campaign=taskapp-activation-id-2026q4&utm_id=2026-10-18-example-taskapp-activation&utm_content=demo-v1-reels",
  "approved_copy_revision": "copy/approved/v001",
  "approved_assets_revision": "assets/approved/v001"
}
```

- `ad_slug`: lowercase hyphenated slug matching the `<ad-slug>` folder name.
- `link_id`: references the corresponding link entry in the campaign root's `campaign.json`. In root `campaign.json`, set `"platform": "meta-ads"`, `"platform_campaign": "<meta-campaign-slug>"`, `"adset": "<adset-slug>"`, and `"ad": "<ad-slug>"` on that link entry.
- `destination_url` and `url_tags`: Meta Ads separates the base **Website URL** (`destination_url`) from **URL parameters** (`url_tags`). Keep `destination_url` free of UTM query keys and put the serialized UTM query string in `url_tags` so parameters are not duplicated.
- `approved_copy_revision` and `approved_assets_revision`: point to the active `vNNN` directories inside this ad's `copy/approved/` and `assets/approved/` trees. Whenever images, carousel cards, or videos are created or imported for the ad, ask [marketing-copywriter](../../marketing-copywriter/SKILL.md) to write accessibility alt text for each visual asset and store it in `copy/drafts/` and `copy/approved/vNNN/`.
- **Reusing assets across ads and social media without regeneration:** Do not regenerate images, videos, or audio for an ad when a matching or compatible approved asset already exists in another ad or in `instagram/`, `linkedin/`, or `twitter/` (and vice versa). Copy the approved deliverable into this ad's `assets/approved/v001/` directory so the ad retains a self-contained record, and note the source path (`copied_from`) and file hash in `MANIFEST.md` or `assets.json`. When an ad copies its approved asset from another directory, **it does not need an `assets/development/` directory**, and its `copy/drafts/` and `copy/approved/vNNN/` should still include accessibility alt text (carried over or adapted by [marketing-copywriter](../../marketing-copywriter/SKILL.md)).
- Optional `remote_ad_id`, `remote_creative_id`, `video_id`, and `image_hash` record live Meta object identifiers after upload or creation.
