# Static link plan and helper

`campaign.json` uses `schema_version: 1`, a stable local `campaign_id` (matching the `<YYYY-MM-DD>-<campaign-name>` directory slug for new campaigns), shared `defaults`, and a nonempty `links` list. See the [fictional example](../assets/campaign.example.json) and [Meta hierarchy contract](meta-ads.md). The helper does not create broader strategy or infer missing values.

- `defaults`: UTM values inherited by each link. Must contain `utm_campaign`; may contain any supported UTM key. `utm_id`, when used, has the same value across the campaign. The local `campaign_id` is not automatically sent as a platform ID.
- Link required fields: unique `link_id`, absolute public `destination_url`, and `utm` (an object, possibly empty when all fields are inherited).
- Link optional fields:
  - Platform hierarchy slugs: `platform` (for example `"meta"`), `platform_campaign` (`<meta-campaign-slug>`), `adset` (`<adset-slug>`), and `ad` (`<ad-slug>`). When any hierarchy field is set on a link, all four must be provided as lowercase slugs mapping to `<platform>/campaigns/<platform_campaign>/adsets/<adset>/ads/<ad>/`.
  - Other metadata: `placement`, `creative_id`, `notes` (strings), and `status` (`planned`, `published`, `retired`; defaults to `planned`). These metadata fields are not automatically added to the URL. Align `creative_id` with the approved copy/asset variant IDs in `copy/approved/vNNN/` and `assets/approved/vNNN/`, and put a documented variant value in `utm_content` when needed.
- Supported UTM keys: `utm_source`, `utm_medium`, `utm_campaign`, `utm_id`, `utm_content`, `utm_term`, `utm_source_platform`. Source, medium and campaign are required after merging defaults. Omit unused optional keys; supplied empty values are errors. Per-link overrides cannot change the shared campaign name or ID.

Local campaign/link/hierarchy IDs use lowercase letters, digits and hyphens and begin with a letter or digit. UTM values preserve supplied case, Unicode and spacing; no normalization occurs. Non-string values, control characters, unknown fields, duplicate JSON keys, unsupported schemes, embedded URL credentials, existing UTM query keys and unresolved macros fail validation before any output is written. Use public nonsensitive destinations: the helper cannot detect every signed URL or personal value.

Run:

```sh
python3 <skill-dir>/scripts/build_utm.py campaign.json --dry-run
python3 <skill-dir>/scripts/build_utm.py campaign.json --out tracking/v001
```

Dry-run returns a JSON preview (including serialized `url_tags` for platforms like Meta that separate Website URL from URL parameters, duplicate-URL warnings, and validated `meta_ads` hierarchy entries when `meta/campaigns/` exists or `--meta-dir` is passed), without writes or network calls. Real runs require an unused output directory, reject symlinked output ancestors, and save the exact source bytes as `campaign.json`, a CSV registry with individual fields, `url_tags`, and final `url`s, and a readable `UTM_PLAN.md`. Rows follow input order and URLs append supported parameters in stable order. Different link IDs resolving to the same URL produce a warning: confirm whether those variants should be distinguished.

When `meta/campaigns/` is present alongside `campaign.json` (or `--meta-dir` is specified), the helper also validates every `meta/campaigns/<meta-campaign-slug>/campaign.json` (goal/objective and budget mode), `adsets/<adset-slug>/adset.json` (optimization goal, targeting, and placements), and `ads/<ad-slug>/ad.json` (format, CTA, `link_id`, `destination_url`, `utm`, and `url_tags`), ensuring one-to-one agreement with the root `campaign.json` link plan before writing any export.

Prior exports are never overwritten. Retained partial output after a filesystem failure is not success; inspect it and choose a new revision directory. The helper validates one snapshot, not history: the agent must compare prior revisions to protect published IDs and keep the shared taxonomy/index/current-revision notes accurate. Existing UTM conflicts require a deliberate plan edit after ownership is resolved; there is no automatic replace flag.

Local round-trip checks establish correct serialization, not successful redirects, ad acceptance, consent handling or analytics receipt. CSV is a publishing handoff, not an ad-platform API payload. Follow the platform's actual destination/URL-parameter insertion contract when publishing is separately authorized.
