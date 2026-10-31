# Meta custom audiences (account level)

A Meta custom audience belongs to the **ad account**, not to one campaign. The same "website visitors 180d" audience serves as a retargeting include in one campaign and a prospecting exclusion in the next. Keep one record per audience in a shared registry beside `INDEX.md` and `UTM_CONVENTIONS.md`, and let ad sets reference it by slug:

```text
marketing/campaigns/
  INDEX.md
  UTM_CONVENTIONS.md
  audiences/
    README.md                      # registry: slug, Meta name, kind, window, status, remote ID, size, used by
    meta-ads/
      <audience-slug>.json         # one record per audience (record fields + native adsctl payload)
  <YYYY-MM-DD>-<campaign-name>/
    meta-ads/campaigns/<meta-campaign-slug>/adsets/<adset-slug>/adset.json   # references audience_slug
```

`audiences/` is not a campaign directory (it has no date prefix) and never holds creatives, links or reports. Campaign-specific reasoning (why an audience is included, size gates, fallbacks) stays in that campaign's `docs/plans/` and `adset.json` `notes`.

## Naming

Meta shows the audience `name` in Ads Manager and in every ad set picker, so make it scannable and self-describing. Use:

```text
<Brand> | <Source> | <Rule> | <Window>d
```

- `<Brand>`: the brand as it appears in other Meta object names (for example `TaskApp`).
- `<Source>`: one of `Web` (pixel/CAPI), `IG` (Instagram professional account), `FB` (Facebook Page), `Video` (video engagement), `LAL` (lookalike).
- `<Rule>`: the behavior in plain words, naming the handle, event or video where it matters: `All visitors`, `Purchase`, `CompleteRegistration`, `@taskapp engagers`, `Demo video 50% or 15s`, `1% ID of Purchasers 180d`.
- `<Window>`: the retention window in days. Always include it; a Meta audience has a fixed window and two windows are two audiences.
- Add `(exclude)` at the end only when an audience exists solely as an exclusion.

Examples: `TaskApp | Web | All visitors | 180d`, `TaskApp | Web | Purchase | 180d (exclude)`, `TaskApp | IG | @taskapp engagers | 90d`, `TaskApp | Video | Demo video 50% or 15s | 365d`.

The `|` separator matches campaign, ad set and ad naming. Escape it as `\|` inside markdown tables.

The file slug mirrors the name without the brand: `<source>-<rule>-<window>d`, lowercase hyphenated, for example `web-all-visitors-180d`, `web-purchase-180d`, `ig-engagers-90d`, `video-demo-50pct-365d`. Never rename a created audience's slug; if the rule or window changes materially, create a new record and retire the old one.

## Record (`audiences/meta-ads/<audience-slug>.json`)

```json
{
  "schema_version": 1,
  "platform": "meta-ads",
  "audience_slug": "web-all-visitors-180d",
  "name": "TaskApp | Web | All visitors | 180d",
  "ad_account_id": "act_1234567890",
  "kind": "website",
  "roles": ["retargeting", "exclusion"],
  "retention_days": 180,
  "status": "planned",
  "remote_audience_id": null,
  "payload": {
    "name": "TaskApp | Web | All visitors | 180d",
    "description": "All site visitors seen by the pixel, 180 days.",
    "prefill": true,
    "retention_days": 180,
    "rule": {
      "inclusions": {
        "operator": "or",
        "rules": [
          {
            "event_sources": [{"id": "1855259662305866", "type": "pixel"}],
            "retention_seconds": 15552000
          }
        ]
      }
    }
  },
  "size_checks": [],
  "notes": ""
}
```

- `kind`: `website`, `ig_engagement`, `page_engagement`, `video_engagement`, or `lookalike`.
- `roles`: how campaigns may use it (`retargeting`, `exclusion`, `seed`).
- `status`: `planned` → `created` (requires `remote_audience_id`) → `retired`. Ad sets cannot reference a retired audience.
- `payload`: the exact native body for `adsctl meta audiences create --file -`; `payload.name` must equal `name`. Customer-file fields (`customer_file_source`, `schema`, `data`) are not allowed: this registry never holds personal data.
- `size_checks`: append `{"checked_at": "<ISO datetime>", "lower_bound": N, "upper_bound": N}` after each read. Meta returns `-1` or omits counts while an audience populates or when it is too small; record that as unavailable, never as zero.

Payload rule shapes (verify against current Meta docs and record the date when they change):

- Website: `event_sources: [{"id": PIXEL_ID, "type": "pixel"}]`, `retention_seconds`, optional `filter`, for example `{"operator": "and", "filters": [{"field": "event", "operator": "eq", "value": "Purchase"}]}` or a `url` `i_contains` filter.
- Instagram engagers: `event_sources: [{"id": IG_USER_ID, "type": "ig_business"}]` with event `ig_business_profile_all` (or a narrower `ig_business_profile_engaged`, `ig_user_messaged_business`, ...).
- Video viewers: `"subtype": "ENGAGEMENT"` and the list rule `[{"object_id": VIDEO_ID, "event_name": "video_view_50_percent"}]`; use the video IDs from the ads' creatives.

## Referencing from ad sets

In `adset.json`, list audiences under `targeting.custom_audiences` and `targeting.excluded_custom_audiences` by slug. Mirror the Meta `id` and `name` once created so the ad set reads on its own:

```json
"excluded_custom_audiences": [
  {"audience_slug": "web-purchase-180d", "id": "120200000000000001", "name": "TaskApp | Web | Purchase | 180d (exclude)"}
]
```

`build_utm.py` resolves each `audience_slug` against `<campaigns root>/audiences/meta-ads/` (override with `--audiences-dir`), validates the record, and fails if the mirrored `id` or `name` drifts from it or the audience is retired. Its dry-run output lists the audiences each ad uses.

## Creating and checking with adsctl

Creating an audience changes the live ad account. It needs explicit user approval, like any other write; a planned record does not authorize it.

```sh
jq .payload audiences/meta-ads/web-all-visitors-180d.json \
  | adsctl meta audiences validate --operation create --file - --profile "$READ_PROFILE" --account "$ACCOUNT"
jq .payload audiences/meta-ads/web-all-visitors-180d.json \
  | adsctl meta audiences create --file - --profile "$WRITE_PROFILE" --account "$ACCOUNT" --dry-run
# after approval, rerun create without --dry-run, then:
adsctl meta audiences get <ID> --profile "$READ_PROFILE" --account "$ACCOUNT"
```

After a verified create, set `status: "created"` and `remote_audience_id`, append a size check, update `audiences/README.md`, mirror the ID into each referencing `adset.json`, and log it in each affected campaign's `docs/CHANGELOG.md`. If the receipt is `applied_unverified` or `unknown`, list audiences by name and reconcile before creating again. Meta requires the custom-audience terms to be accepted in Business Manager; a terms error is the user's step, not something to retry.

Audiences take hours to populate. Re-read size before relying on an audience for a size-gated decision (for example folding a small retargeting ad set into prospecting).
