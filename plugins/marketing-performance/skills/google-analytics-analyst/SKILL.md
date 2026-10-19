---
name: google-analytics-analyst
description: Query and analyze Google Analytics 4 (GA4) and Firebase Analytics campaign performance, traffic acquisition, user engagement, and post-click product and conversion funnels using the GA4 Data API. Configure project connection and service-account access, reconcile UTM-tagged sessions against ad-platform clicks (such as Meta Ads via adsctl) and backend conversion tables, diagnose funnel drop-offs, and produce actionable recommendations. Use when evaluating campaign performance in Google Analytics or Firebase Analytics, auditing post-click funnels, or setting up GA4 service-account reporting.
---

# Google Analytics Analyst

Evaluate post-click campaign performance, channel acquisition, user engagement, and product-to-purchase funnels in Google Analytics 4 (GA4) and Firebase Analytics using read-only GA4 Data API (`v1beta`) queries. Treat GA4 as the bridge between top-of-funnel ad-platform delivery (such as `$adsctl-meta-analyst`) and bottom-of-funnel first-party backend records.

## 1. Connect to the Analytics project and verify Service Account access

Read [setup-and-auth.md](references/setup-and-auth.md) before configuring credentials or troubleshooting authentication errors.

1. **Discover the GA4 Property ID and Streams from Firebase / GCP:**
   - Every Firebase Analytics project is backed by a GA4 Property (`properties/<PROPERTY_ID>`).
   - If only the GCP/Firebase Project ID is known (for example `my-app-production`), resolve the numeric GA4 Property ID, account ID, and web/iOS/Android measurement streams via the Firebase Management API (`GET https://firebase.googleapis.com/v1beta1/projects/<PROJECT_ID>/analyticsDetails`) or using the bundled helper:

```sh
python3 <skill-dir>/scripts/ga4_report.py discover --project "$GCP_PROJECT_ID"
```

2. **Why Service Account authentication is required (and why `gcloud` interactive OAuth fails):**
   - `gcloud auth login` and `gcloud auth application-default login` use Google's shared public SDK OAuth client (`764086051850-...`). When you request the sensitive `https://www.googleapis.com/auth/analytics.readonly` scope in a browser with that client, Google blocks the consent screen with **`This app is blocked`**.
   - Instead, authenticate using a **GCP Service Account JSON key** (`grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer` with `scope=https://www.googleapis.com/auth/analytics.readonly`), which exchanges a locally signed RS256 JWT directly at `https://oauth2.googleapis.com/token` with zero browser prompts.
3. **Three prerequisites on the target project:**
   - **Enable the GA4 Data API** on the GCP project that owns the service account:
     ```sh
     gcloud services enable analyticsdata.googleapis.com --project="$GCP_PROJECT_ID"
     ```
   - **Grant GA4 Property Viewer access to the Service Account:** Project-level IAM (`roles/viewer` or `roles/firebase.analyticsViewer`) does **not** automatically grant GA4 Data API read access when the GA4 account is managed under Google Analytics. Add the service account email (`<name>@<project-id>.iam.gserviceaccount.com`) as **Viewer** in **Google Analytics → Admin → Property → Property access management** (`https://analytics.google.com/analytics/web/#/a<ACCOUNT_ID>p<PROPERTY_ID>/admin/property/users`).
   - **Supply the Service Account key securely:** Export `GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json` (or `GA4_SERVICE_ACCOUNT_FILE` in `~/.config/marketing-creative/.env`), or run the helper over SSH on a trusted host where the service account file already resides. Never print, log, or commit private keys or tokens.

## 2. Pull multi-layer GA4 diagnostic evidence

Use [ga4_report.py](scripts/ga4_report.py) (Python 3.10+, standard library + `openssl`) to inspect metadata and run structured GA4 Data API reports. Preview requests with `--dry-run` when validating query structure without network calls.

### Inspect custom dimensions, metrics, and active streams

```sh
python3 <skill-dir>/scripts/ga4_report.py metadata \
  --property "$GA4_PROPERTY_ID" \
  --service-account "$GOOGLE_APPLICATION_CREDENTIALS"
```

### Run standard campaign & funnel diagnostic presets

```sh
# 1. Channel & UTM Campaign Acquisition (sessions, engagedSessions, engagementRate, avgDuration, users, newUsers)
python3 <skill-dir>/scripts/ga4_report.py preset \
  --property "$GA4_PROPERTY_ID" \
  --preset campaigns \
  --start-date 2026-10-16 --end-date today \
  --service-account "$GOOGLE_APPLICATION_CREDENTIALS"

# 2. Creative / Ad Content & Landing Variant Breakdown (utm_campaign x utm_content / sessionManualAdContent)
python3 <skill-dir>/scripts/ga4_report.py preset \
  --property "$GA4_PROPERTY_ID" \
  --preset ad-content \
  --campaign "$UTM_CAMPAIGN" \
  --start-date 2026-10-16 --end-date today \
  --service-account "$GOOGLE_APPLICATION_CREDENTIALS"

# 3. Post-Click Event Funnel by Ad Content (page_view -> activation -> access_gate -> login -> checkout -> purchase)
python3 <skill-dir>/scripts/ga4_report.py preset \
  --property "$GA4_PROPERTY_ID" \
  --preset funnel \
  --campaign "$UTM_CAMPAIGN" \
  --start-date 2026-10-16 --end-date today \
  --service-account "$GOOGLE_APPLICATION_CREDENTIALS"

# 4. Screen / Page Path Engagement Breakdown (unifiedScreenName & pagePath)
python3 <skill-dir>/scripts/ga4_report.py preset \
  --property "$GA4_PROPERTY_ID" \
  --preset screens \
  --campaign "$UTM_CAMPAIGN" \
  --start-date 2026-10-16 --end-date today \
  --service-account "$GOOGLE_APPLICATION_CREDENTIALS"

# 5. Daily Trajectory (date x sessionCampaignName x sessionManualAdContent)
python3 <skill-dir>/scripts/ga4_report.py preset \
  --property "$GA4_PROPERTY_ID" \
  --preset daily \
  --campaign "$UTM_CAMPAIGN" \
  --start-date 2026-10-16 --end-date today \
  --service-account "$GOOGLE_APPLICATION_CREDENTIALS"
```

For custom dimension/metric combinations or filters, use `query`:

```sh
python3 <skill-dir>/scripts/ga4_report.py query \
  --property "$GA4_PROPERTY_ID" \
  --dimensions sessionSourceMedium,sessionCampaignName,sessionManualAdContent,eventName \
  --metrics eventCount,totalUsers,sessions \
  --start-date 2026-10-16 --end-date today \
  --service-account "$GOOGLE_APPLICATION_CREDENTIALS"
```

## 3. Evaluate the 5-stage post-click funnel

Read [metrics-and-dimensions.md](references/metrics-and-dimensions.md) for exact GA4 dimension/metric definitions, formulas, and Web vs. iOS instrumentation differences. Evaluate every campaign through five sequential stages:

1. **Click-to-Session Connect Rate (Ad Platform → GA4):**
   - Compare ad-platform **Outbound Clicks** (for example from `$adsctl-meta-analyst`) against GA4 `sessions` and `newUsers` for the matching `sessionCampaignName` (`utm_campaign`) and `sessionManualAdContent` (`utm_content`).
   - Compute **Click-to-Session Connect Rate** (`GA4 Sessions / Outbound Clicks`) and **New-User Connect Rate** (`GA4 New Users / Unique Outbound Clicks`).
   - Investigate any connect rate below `70%` for redirect stripping, slow TLS/bundle load, broken `url_tags`, or consent-mode blocking before GA4 initializes.
2. **Landing Page Reception & Session Quality:**
   - Evaluate `engagedSessions`, **Engagement Rate** (`engagedSessions / sessions` — sessions lasting `>= 10s`, having `>= 2` screen/page views, or triggering a key event), and `averageSessionDuration` (`userEngagementDuration / sessions`) by landing destination (`pagePath`, `unifiedScreenName`) and ad variant (`sessionManualAdContent`).
   - Compare cold paid social traffic against organic social and referral benchmarks on the same property.
3. **Product Activation & Interactive Depth:**
   - Measure the share of landing users who progress from passive arrival (`page_view` / initial `screen_view`) to **meaningful first-use activation** (`content_load_result`, `learning_session_started`, `answer_revealed`, `audio_playback_result`, or product-equivalent core actions).
   - Compare activation rate across landing URLs (for example interactive `/app` vs. cold pricing `/app/packages` or static `/` homepages).
4. **Value Gate, Registration & Paywall Reach:**
   - Measure how many activated users hit a registration prompt, free-limit boundary, or value gate (`access_gate_viewed`, `access_gate_action`), attempt authentication (`login_attempt`), and complete registration/sign-in (`login`, `sign_up`).
   - Identify whether low registration comes from **insufficient gate reach** (users never hit the boundary where sign-in is required) or **gate friction** (users see `access_gate_viewed` / `login_attempt` but fail to complete `login`).
5. **Monetization, Checkout & Attribution Continuity:**
   - Track package/pricing inspection (`website_packages_viewed`, `credit_catalog_viewed`, `screen_view` on `Packages`), package selection (`website_package_selected`), checkout view/start (`website_checkout_viewed`, `website_checkout_started`, `begin_checkout`), payment handoff (`website_payment_opened`), and completed purchase (`purchase`, `website_checkout_result`).
   - Reconcile GA4 checkout/purchase events against first-party backend database records (`users`, `paid_access_grants`, `ai_credit_purchases`, `meta_measurement_consents`) and ad-platform conversion reporting (`landing_page_view`, `initiate_checkout`, `purchase`).

## 4. Diagnose bottlenecks and formulate evidence-backed recommendations

Read [diagnostic-playbook.md](references/diagnostic-playbook.md) to map multi-source funnel symptoms to root causes and prioritized fixes:

- **Never confuse an attribution/consent blindspot with a traffic failure:** If Meta Ads reports `landing_page_view: 1` on `98` outbound clicks while GA4 records `111` sessions and `98` new users on that exact `utm_campaign`, the traffic arrived cleanly (`100%` connect rate) and the gap is pixel/consent gating—not a broken landing page.
- **Compare cohorts by `utm_content` (`sessionManualAdContent`):** Isolate creative hooks and landing-page experiments at the `sessionManualAdContent` level. When one landing path drives `3x–6x` higher session duration and activation at identical CPC, recommend consolidating spend into the winning path and pausing the high-bounce variant.
- **Verify Web vs. Mobile screen-name parity:** On Web (`gtag.js`), GA4 only populates `unifiedScreenName` when `screen_view` includes `firebase_screen` (whereas iOS/Android Firebase SDKs map `screen_name` automatically). Flag `(not set)` screen names and missing checkout events as P0/P1 instrumentation fixes.
- **Pair with [campaign-manager](../campaign-manager/SKILL.md) for persistent campaign reporting:** When analyzing a tracked campaign in the workspace, hand off or record the unified Meta Ads + GA4 + Backend findings in `<campaign-dir>/reports/<datetime>.md` using [campaign-manager](../campaign-manager/SKILL.md)'s reporting structure.
