# GA4 Data API Metrics, Dimensions & Funnel Formulas

Verified against the [Google Analytics Data API v1beta Schema](https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema) on 2026-10-19.

---

## 1. Attribution & Traffic Dimensions (Session vs. First-User vs. Event Scope)

GA4 separates **first-user acquisition** (how the user originally discovered the product) from **session acquisition** (what brought the user in the current session). Always inspect **session-scoped** dimensions when evaluating active campaign links, and compare with **first-user** dimensions when measuring new-user growth or multi-session conversion lag.

| Dimension API Name | Scope | UTM / Tag Source | What It Measures & How to Use It |
| --- | --- | --- | --- |
| `sessionSourceMedium` | Session | `utm_source` / `utm_medium` | Combined source and medium for the session (e.g. `instagram / paid_social`, `linkedin / organic_social`, `(direct) / (none)`). Primary channel grouping key. |
| `sessionSource` | Session | `utm_source` | Session source (`instagram`, `facebook`, `linkedin`, `google`). |
| `sessionMedium` | Session | `utm_medium` | Session medium (`paid_social`, `organic_social`, `cpc`, `referral`, `email`). |
| `sessionCampaignName` | Session | `utm_campaign` | Marketing campaign name (`utm_campaign`, e.g. `gochi_web_subscriptions_20261018`). Use to filter a specific campaign launch. |
| `sessionManualAdContent` | Session | `utm_content` | **Ad / creative / landing-page variant identifier** (`utm_content`, e.g. `ipad_demo_exciting_v2_lp_app` vs `ipad_demo_exciting_v2_lp_packages`). Essential for A/B testing ads and landing paths! |
| `sessionManualTerm` | Session | `utm_term` | Keyword, audience segment, or targeting cohort (`utm_term`). |
| `firstUserSourceMedium` | User | First touch `utm_source` / `utm_medium` | The original source/medium that acquired the user on their first visit. |
| `firstUserCampaignName` | User | First touch `utm_campaign` | The original `utm_campaign` that acquired the user. Compare against `sessionCampaignName` to see if paid users return later via `(direct)`. |
| `firstUserManualAdContent` | User | First touch `utm_content` | The original ad variant (`utm_content`) that first acquired the user. |
| `platform` | Device/Stream | Automatic | `Web`, `iOS`, or `Android`. |
| `deviceCategory` | Device | Automatic | `mobile`, `desktop`, or `tablet`. Compare mobile vs. desktop when running Instagram/Facebook placements. |
| `country` / `city` | Geo | Automatic | Geographic distribution of sessions and users. Verify delivery matches ad-set geo targeting. |
| `date` | Time | Automatic | `YYYYMMDD` in the property's configured timezone. |

---

## 2. Content, Screen & Event Dimensions

| Dimension API Name | Scope | What It Measures & Critical Gotchas |
| --- | --- | --- |
| `eventName` | Event | Exact event triggered (`page_view`, `screen_view`, `session_start`, `first_visit`, `login`, `purchase`, or custom app/web events). |
| `unifiedScreenName` | Event | Screen name on mobile (`screen_name`) or Web (`firebase_screen`) or page `<title>`. **Web (`gtag.js`) Gotcha:** `gtag('event', 'screen_view', { screen_name: '...' })` alone leaves `unifiedScreenName` as `(not set)` unless `firebase_screen` is also passed in the event payload! |
| `pagePath` | Event | URL path after the hostname (e.g. `/`, `/app`, `/app/packages`, `/app/checkout`). Reliable on Web even if `<title>` is static or `firebase_screen` was omitted. |
| `landingPagePlusQueryString` | Session | The entry path and query parameters of the first page in the session. |

---

## 3. Core Traffic, Engagement & Conversion Metrics

| Metric API Name | Type | Formula / Definition | Analytical Meaning |
| --- | --- | --- | --- |
| `sessions` | Integer | Count of `session_start` events | Total sessions initiated in the date range. |
| `totalUsers` | Integer | Distinct users who logged at least one event | Total unique active/visiting users (identified by `user_id` or `app_instance_id` / `_ga` cookie). |
| `newUsers` | Integer | Count of `first_visit` / `first_open` events | Users visiting the property for the very first time. |
| `activeUsers` | Integer | Distinct users with an engaged session or `first_visit` | GA4's default "Users" metric in standard UI reports. Note: `activeUsers <= totalUsers` because unengaged returning bounces are excluded from `activeUsers`. Always pull `totalUsers` and `newUsers` alongside `sessions` for ad-click reconciliation! |
| `engagedSessions` | Integer | Sessions meeting `>= 1` engagement criterion | A session is **engaged** if it lasts **`>= 10 seconds`**, has **`>= 2` `screen_view` / `page_view` events**, or triggers **`>= 1` key/conversion event**. |
| `engagementRate` | Float (`0..1`) | `engagedSessions / sessions` | Percentage of sessions that were engaged (`1 - bounceRate`). Primary landing-page reception metric. |
| `bounceRate` | Float (`0..1`) | `1 - engagementRate` | Percentage of sessions that left in `< 10s` with only 1 page/screen view and no conversion event. |
| `userEngagementDuration` | Seconds | Total foreground time across sessions | Sum of active foreground engagement time in seconds. |
| `averageSessionDuration` | Seconds | `userEngagementDuration / sessions` | Average active foreground time per session in seconds. Strongest indicator of interactive depth on single-page web apps (SPAs) where URL paths may not change. |
| `eventCount` | Integer | Total times the event fired | Raw volume of interactions. Compare with `totalUsers` (`eventCount / totalUsers`) to measure repeat intensity per user. |
| `conversions` / `keyEvents` | Integer | Count of events marked as Key Events | Total key conversion events in GA4. |
| `totalRevenue` / `purchaseRevenue` | Currency | Sum of `value` on `purchase` events | Monetary revenue recorded by GA4 ecommerce events. |

---

## 4. Derived Cross-System & Funnel Metrics

When combining ad-platform data (`$adsctl-meta-analyst`), GA4 (`$google-analytics-analyst`), and backend database records, compute these derived ratios:

### A. Ad-to-GA4 Connect & Reception Metrics
1. **Click-to-Session Connect Rate:**
   $$\text{Click-to-Session Connect Rate} = \frac{\text{GA4 Sessions (matching } \texttt{utm\_campaign}\text{)}}{\text{Ad Platform Outbound Clicks}}$$
   - **Benchmark:**
     - `>= 85%`: Healthy redirect, fast page boot, and intact `url_tags` / UTM parameters. *(Can slightly exceed `100%` when users reopen the tagged tab later after 30 minutes of inactivity, starting a second session under the same URL).*
     - `70% – 84%`: Normal mobile in-app browser drop-off (Instagram/Facebook WebView abandonment during load).
     - `< 70%`: **Broken bridge.** Check for slow TLS/JS bundle load, redirect stripping query strings, missing `url_tags` on specific ads, or cookie/consent banners blocking GA4 initialization.
2. **New-User Connect Rate:**
   $$\text{New-User Connect Rate} = \frac{\text{GA4 } \texttt{newUsers}}{\text{Ad Platform Unique Outbound Clicks}}$$
3. **Consent / Pixel Survival Ratio (when Meta Pixel is consent-gated):**
   $$\text{Pixel Consent Opt-In Rate} = \frac{\text{Consents Granted}}{\text{Total Consent Decisions}}$$
   - Explains discrepancies between GA4 (if loaded as basic telemetry) and Meta Pixel (`PageView` / `landing_page_view` gated behind explicit marketing consent).

### B. Post-Click Product & Monetization Funnel Conversion Rates
Always compute funnel step rates using **unique users (`totalUsers`)** who triggered each stage within the campaign cohort (`sessionCampaignName` / `sessionManualAdContent`), plus **events per active user (`eventCount / totalUsers`)** to measure depth:

1. **Landing-to-Activation Rate:**
   $$\text{Activation Rate} = \frac{\text{Users triggering core product interaction (e.g. } \texttt{learning\_session\_started}\text{)}}{\text{Total Landing Users (} \texttt{totalUsers}\text{)}}$$
2. **Activation-to-Value-Gate Reach Rate:**
   $$\text{Gate Reach Rate} = \frac{\text{Users viewing paywall/auth gate (e.g. } \texttt{access\_gate\_viewed}\text{)}}{\text{Activated Users}}$$
3. **Gate-to-Login Attempt Rate:**
   $$\text{Gate Action Rate} = \frac{\text{Users triggering } \texttt{login\_attempt}}{\text{Users viewing } \texttt{access\_gate\_viewed}}$$
4. **Login Completion Rate:**
   $$\text{Login Completion Rate} = \frac{\text{Users completing } \texttt{login} \text{ or } \texttt{sign\_up}}{\text{Users triggering } \texttt{login\_attempt}}$$
5. **Pricing-to-Checkout Start Rate:**
   $$\text{Checkout Start Rate} = \frac{\text{Users triggering } \texttt{website\_checkout\_started} \text{ / } \texttt{begin\_checkout}}{\text{Users viewing } \texttt{website\_packages\_viewed} \text{ / } \texttt{credit\_catalog\_viewed}}$$
6. **Checkout-to-Paid Completion Rate:**
   $$\text{Payment Completion Rate} = \frac{\text{Completed Purchases (GA4 } \texttt{purchase} \text{ / DB paid grants)}}{\text{Initiated Checkouts}}$$
