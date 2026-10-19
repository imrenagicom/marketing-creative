# Campaign Performance Reporting & Analysis (`reports/<datetime>.md`)

Each campaign directory `<YYYY-MM-DD>-<campaign-name>/` includes a top-level **`reports/`** directory that stores point-in-time, multi-source performance analysis reports in chronological markdown files named **`<datetime>.md`**.

---

## 1. Directory Layout & Filename Convention

```text
marketing/campaigns/<YYYY-MM-DD>-<campaign-name>/
  README.md
  campaign.json
  docs/
    MARKETING_BRIEF.md
    MEASUREMENT.md
    CHANGELOG.md
    plans/
    reviews/
  reports/
    2026-10-19-2200.md                 # or 2026-10-19T22-00-00+07-00.md
    2026-10-22-0930.md                 # subsequent checkpoint report
```

### Naming and Immutability Rules
1. **Filename format (`<datetime>.md`):**
   - Use an ISO-ordered, filesystem-safe timestamp in the campaign's primary timezone: either **`YYYY-MM-DD-HHMM.md`** (for example `2026-10-19-2200.md`) or **`YYYY-MM-DDTHH-MM-SS+HH-MM.md`** (replacing colons `:` with hyphens `-` so filenames are portable across macOS, Linux, and Windows).
   - Never overwrite an earlier report when running a new checkpoint analysis; create a new `<datetime>.md` file so the campaign retains a complete longitudinal audit trail.
2. **Cross-reference in `README.md` and `docs/CHANGELOG.md`:**
   - Link the latest report in the campaign root `README.md` under a `## Performance Reports` section.
   - When a report leads to concrete mutations (such as pausing an ad variant, shifting budgets, updating `MEASUREMENT.md`, or shipping tracking fixes), log those changes in `docs/CHANGELOG.md` and update affected `ad.json` / `campaign.json` status fields.

---

## 2. Multi-Skill Reporting Workflow

When asked to evaluate a campaign or create a campaign performance report, `campaign-manager` orchestrates three evidence layers:

1. **Paid Ad Platform Delivery & Creative Retention (`$adsctl-meta-analyst` & `$adsctl`):**
   - Inspect live campaign, ad set, and ad statuses, budgets, targeting, and creative `url_tags`.
   - Pull campaign-level, ad-level, daily (`--time-increment 1`), and placement (`publisher_platform,platform_position`) insights: spend, impressions, reach, frequency, CPM, 3s video views (Thumbstop rate), ThruPlays (Hold rate), video quartiles (`p25`–`p100`), all clicks/CTR, **outbound clicks / outbound CTR / cost per outbound click**, and platform-reported conversions (`landing_page_view`, `initiate_checkout`, `purchase`).
2. **Post-Click Web/App Reception & Product Funnel ([google-analytics-analyst](../../google-analytics-analyst/SKILL.md) / `$google-analytics-analyst`):**
   - Query the GA4 Data API (`ga4_report.py`) for the campaign's `utm_campaign` (`sessionCampaignName`) and each ad/post variant's `utm_content` (`sessionManualAdContent`), plus property-wide channel benchmarks (`sessionSourceMedium`).
   - Reconcile **Outbound Clicks → GA4 Sessions / New Users** (Click-to-Session Connect Rate), and measure `engagedSessions`, `engagementRate`, `averageSessionDuration`, `pagePath` / `unifiedScreenName` views, and event-level funnel progression from landing (`page_view` / `screen_view`) through product activation (`content_load_result`, `learning_session_started`), value-gate reach (`access_gate_viewed`, `access_gate_action`), authentication (`login_attempt`, `login`), package inspection (`website_packages_viewed`), and checkout (`website_checkout_started`, `purchase`).
3. **First-Party Backend / Database Verification (when accessible in scope):**
   - Cross-check marketing consent logs (`meta_measurement_consents`), user registrations (`users`), and payment/subscription records (`paid_access_grants`, `ai_credit_purchases`) for the same window.
   - Reconcile why numbers agree or diverge across Ad Platform ↔ GA4 ↔ Backend DB (for example, consent gating on Meta Pixel vs. un-gated GA4 sessions, or unpaid e-wallet/QRIS invoices in the database).

---

## 3. Canonical Marketing Performance Report Structure

Every `reports/<datetime>.md` file must include the following ten sections so stakeholders can immediately see what happened, why it happened, what actions were already executed, and what to do next.

```markdown
# Campaign Performance Report — `<campaign_id>` (`<YYYY-MM-DD HH:MM TZ>`)

- **Campaign:** `<campaign_id>` (`<Campaign Display Name>`)
- **Report Timestamp:** `<YYYY-MM-DD HH:MM TZ>`
- **Analysis Window:** `<start_date>` to `<end_date>` (note whether final day is partial)
- **Campaign Maturity Stage:** `Launch / Calibration (<48h)` | `Learning Phase (<7d / <50 conversions)` | `Established (>=7d)`
- **Active Channels Evaluated:** `meta-ads`, `instagram`, `linkedin`, `web` (GA4 + First-Party DB)
- **Tracking Revision:** `tracking/vNNN`

---

## 1. Executive Verdict

2–4 concise sentences stating:
1. Campaign maturity and spend/delivery health.
2. Top-to-bottom funnel headline (Thumbstop → Outbound CTR → GA4 Connect Rate → Product Activation → Checkout/Purchase).
3. Primary bottleneck identified across the funnel.
4. Summary of immediate actions taken and the primary strategic recommendation.

---

## 2. Multi-Source Funnel Scorecard

### A. End-to-End Funnel Reconciliation (Meta Ads → GA4 → First-Party Backend)
| Funnel Stage | Metric | Source | Campaign Total | Variant A (`<ad-slug-1>`) | Variant B (`<ad-slug-2>`) | Conversion / Step Rate | Benchmark / Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **1. Delivery** | Spend / Impressions / Reach / CPM | Meta Ads | ... | ... | ... | Frequency `X.XX` | ... |
| **2. Creative Hook** | 3s Video Views (Thumbstop) / ThruPlays (Hold) | Meta Ads | ... | ... | ... | Hook `XX.X%` / Hold `XX.X%` | ... |
| **3. Click Intent** | Outbound Clicks (`Unique`) / Cost per Outbound | Meta Ads | ... | ... | ... | Outbound CTR `X.XX%` | ... |
| **4. Post-Click Connect** | GA4 Sessions / New Users | GA4 (`<property_id>`) | ... | ... | ... | Connect Rate `XX.X%` | ... |
| **5. Landing Quality** | Engaged Sessions / Avg Session Duration | GA4 (`<property_id>`) | ... | ... | ... | Engagement Rate `XX.X%` | ... |
| **6. Product Activation** | Core Activation Event (`<event_name>`) | GA4 (`<property_id>`) | ... | ... | ... | `XX.X%` of Landing Users | ... |
| **7. Value Gate / Auth** | Gate Viewed → Login Attempt → Login | GA4 / Backend DB | ... | ... | ... | `XX.X%` Gate Reach | ... |
| **8. Monetization** | Checkouts Started → Paid Purchases | GA4 / Backend DB | ... | ... | ... | `X` initiated / `X` paid | ... |

### B. Daily Pacing & Trajectory
Table separating completed account-local days from partial current-day delivery across Meta Ads and GA4.

---

## 3. Creative Variant, Placement & Cross-Channel Breakdown

- **Ad Variant & Landing Page Comparison (`utm_content` / `sessionManualAdContent`):** Compare creative hooks, CBO spend share, CPM, Outbound CTR, GA4 engagement rate, session duration, and downstream funnel depth per variant.
- **Placement Breakdown (`publisher_platform` × `platform_position`):** Compare Instagram Reels, Instagram Stories, Instagram Feed, Explore, and Facebook placements on spend share, Outbound CTR, and Cost per Outbound Click.
- **Cross-Channel Context (Paid vs. Organic / Referral / Direct in GA4):** Compare paid campaign engagement against organic social (`linkedin / organic_social`, `instagram / organic_social`), referral, and direct cohorts on the same property.

---

## 4. What Went Well

Bullet list of validated strengths backed by concrete metrics:
- Creative hook, hold rate, or placement efficiency that beat benchmarks.
- Technical/tracking links that achieved high click-to-session connect rates.
- Landing routes or product interactions showing strong engagement depth (e.g. session duration, repeat sessions per activated user, consent opt-in rate).

---

## 5. What Went Wrong

Bullet list of diagnosed failures, drop-offs, and blindspots backed by exact evidence:
- Underperforming ad variants or landing pages (e.g. cold traffic bouncing from a static pricing page).
- Funnel drop-off stages (e.g. gap between free preview activation and value-gate reach, WebView OAuth login drop-off, or unpaid QRIS/e-wallet checkouts).
- Measurement, consent, or attribution discrepancies (e.g. missing frontend analytics events, `(not set)` screen names, or lost UTM headers on checkout API calls).

---

## 6. What Can Be Improved & Recommendations

Prioritized (`P0` Critical / `P1` High-Leverage / `P2` Iterative) recommendations grouped by domain:
- **Media Buying & Budget Allocation:** Which variants/placements to pause, hold, consolidate, or scale, with explicit sample-size gates.
- **Landing Experience & Product Funnel:** Changes to landing routes, onboarding, value-gate timing, authentication inside mobile WebViews, and payment UX.
- **Creative & Copy Iteration:** Next hook, offer framing, or CTA tests informed by video retention curves (`p25` → `p100`) and click behavior.
- **Measurement & Attribution:** Instrumentation, CAPI, consent, or schema improvements.

---

## 7. Actions Taken

Chronological log of concrete actions executed during or as part of this review session (or `None — diagnostic review only` if no mutations were made):
- **Live Ad Account Mutations:** Exact `adsctl` commands/operations, affected ad/adset/campaign IDs, status or budget changes, and timestamp.
- **Code, Tracking & Infrastructure Changes:** Commits, pull requests, database migrations, and production release tags deployed and verified.
- **Workspace & Campaign Record Updates:** Updated `ad.json`, `MEASUREMENT.md`, `CHANGELOG.md`, or `tracking/vNNN` files.

---

## 8. Lessons Learned

Durable, reusable insights for future campaigns and product iterations:
- **Audience & Funnel Psychology:** What this cohort taught us about cold traffic behavior (e.g. interactive product-first landing vs. cold pricing wall).
- **Creative & Placement Mechanics:** How format/duration interacted with Reels vs. Stories vs. Feed.
- **Technical & Attribution Patterns:** Engineering or analytics patterns to standardize across future launches.

---

## 9. Action Items & Next Checkpoints

| Priority | Action Item | Owner | Success Metric / Checkpoint Threshold | Target Date / Trigger | Status |
| --- | --- | --- | --- | --- | --- |
| `P0` | ... | ... | ... | ... | `Done` / `Open` |
| `P1` | ... | ... | ... | ... | `Open` |

---

## 10. Scope & Provenance Footer

- **Meta Ads:** Profile, Ad Account ID, Campaign ID, Currency, Timezone, API Version, Date Window, `meta.complete: true`.
- **Google Analytics 4:** GCP Project ID, GA4 Account ID, GA4 Property ID, Stream IDs, Service Account, Date Window.
- **First-Party Backend:** Environment/Host, Tables Queried, Timezone, Release Version verified.
```
