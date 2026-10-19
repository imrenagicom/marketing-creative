# GA4 Campaign & Funnel Diagnostic Playbook

Use this playbook to diagnose campaign performance bottlenecks across paid social (`meta-ads`), organic social (`instagram`, `linkedin`, `twitter`), referral, and direct traffic, and to translate raw GA4 Data API numbers into prioritized engineering, UX, and media-buying actions.

---

## 1. Cross-System Reconciliation Matrix (Ad Platform vs. GA4 vs. Backend DB)

Before judging campaign conversion rates, reconcile the three data sources side-by-side. Differences between systems are diagnostic signals, not noise:

| Symptom Across Systems | Root Cause Diagnosis | Verification Check & Action |
| --- | --- | --- |
| **Meta Outbound Clicks high (`~100`), Meta `landing_page_view` near `0`, but GA4 `sessions` / `newUsers` match Outbound Clicks (`~100`)** | **Pixel consent or CAPI gating—NOT a broken landing page.** Users are arriving on the site (`~100%` Click-to-Session Connect Rate), but `fbq('init')` / `PageView` is blocked until explicit consent or consent is never prompted on the ad's landing route. | 1. Inspect which routes mount the consent banner (e.g. `/` vs `/app`).<br>2. Check if the consent banner language matches the ad market.<br>3. Check if pixel ID in `config.yaml` matches the ad set's `promoted_object.pixel_id`. |
| **Meta Outbound Clicks high, AND GA4 `sessions` for `utm_campaign` is near `0`, while GA4 `(direct) / (none)` spikes on the same dates** | **UTM stripping or missing `url_tags`.** Either the ad was published without `url_tags` (`utm_source=...`), or an HTTP/HTTPS/trailing-slash redirect on the server strips query parameters before GA4 fires `page_view`. | 1. Inspect live ad creative `url_tags` via `$adsctl`.<br>2. Run `curl -IL "<destination_url>?<url_tags>"` to verify query params survive every redirect.<br>3. Verify SPA router does not strip `window.location.search` before `gtag` initializes. |
| **Meta Outbound Clicks high, AND both GA4 `sessions` and `(direct)` are low (`< 50%` total connect rate)** | **Slow page load / WebView abandonment.** Users tap the ad inside Instagram/Facebook's in-app WebView and close the sheet before the JS bundle boots. | 1. Check bundle size, TTFB, and CDN caching on the landing route.<br>2. Verify GA4 initializes early in page boot rather than behind heavy async data fetches. |
| **Backend DB shows initiated checkouts or sign-ups, but GA4 shows `0` checkout events** | **Missing frontend analytics instrumentation on checkout routes.** Backend flows (`startWebsiteCheckout`, `startCreditCheckout`) execute via API calls without emitting GA4 events (`website_checkout_started`, `begin_checkout`, `purchase`). | 1. Audit the frontend checkout component for analytics emitters.<br>2. Add structured events (`website_packages_viewed`, `website_package_selected`, `website_checkout_viewed`, `website_checkout_started`, `website_checkout_result`, `website_payment_opened`). |
| **Backend DB shows `paid_access_grants` rows, but all have empty UTM columns (`utm_source = ''`)** | **Session attribution lost between landing and checkout API call.** When a user lands on `/app?...` and later navigates to `/app/checkout`, `window.location.search` no longer contains the initial UTMs unless cached in `sessionStorage` and attached via a header (e.g. `X-Gochi-Campaign`). | 1. Persist landing UTMs in `sessionStorage` on initial load.<br>2. Attach the stored campaign JSON header on checkout initiation API requests and persist UTM columns on the transaction table. |

---

## 2. Landing Path & Variant Diagnostics (`sessionManualAdContent` / `utm_content`)

When a campaign splits traffic across multiple landing experiences (for example an interactive product experience `/app` vs. a static pricing catalog `/app/packages` vs. a marketing homepage `/`), compare them across four metrics in GA4:

1. **Engagement Rate (`engagedSessions / sessions`):**
   - `< 45%` on cold paid traffic indicates immediate message mismatch or "price shock" before value demonstration.
   - `>= 55%` on cold paid social (Instagram Reels/Stories) indicates strong visual/message continuity between the video hook and the landing screen.
2. **Average Session Duration (`averageSessionDuration`):**
   - Compare seconds spent per session across `sessionManualAdContent` variants:
     - **Example Pattern:** If an ad demonstrating an interactive product sends Variant A to `/app` (`231s` avg session duration, `59.6%` engagement rate, `30.2%` starting a session) and Variant B to `/app/packages` (`42s` avg session duration, `48.8%` engagement rate, `5.0%` starting a session, `0` sign-ins), **cold traffic is bouncing off the cold pricing wall** because they clicked to *try the product shown in the video*, not to read a price table before trying it.
   - **Decision Rule:** Pause the cold pricing-page ad variant (`LP packages`) and consolidate 100% of ad-set budget into the interactive product landing page (`LP app`).
3. **Interactive Depth (`eventCount / totalUsers` on core product events):**
   - Measure how many actions each activated user completes (e.g. `32` `learning_session_started` across `16` users = `2.0` sessions per activated user; `370` `audio_playback_result` across `12` users = `30.8` audio plays per user).
   - High depth per activated user proves **product-market engagement** once the user starts; if overall conversions are still low, the bottleneck is downstream of activation (value-gate reach, sign-in friction, or payment completion).

---

## 3. Funnel Stage Drop-Off Playbook

Walk down the post-click funnel from top (`page_view` / `screen_view`) to bottom (`purchase`) and apply the diagnostic rule for the steepest drop-off stage:

### Stage A: Landing → First Interactive Action (`< 20%` Activation Rate)
- **Symptoms:** Users land (`screen_view` / `page_view` = `100%`), stay `15–40s`, and leave without triggering `content_load_result` or `learning_session_started`.
- **Root Causes:**
  1. Landing screen requires account creation before showing any interactive preview.
  2. Landing screen shows a generic dashboard or menu instead of dropping the user directly into the specific feature demonstrated in the ad creative.
  3. Mobile WebView layout hides the primary interactive CTA below the fold.
- **Remediation:** Deep-link the ad directly into an interactive, zero-login starter experience that mirrors the first 5 seconds of the video creative.

### Stage B: Activated User → Value Gate / Registration Prompt (`< 35%` Gate Reach among Activated Users)
- **Symptoms:** Users actively use the free preview (`30%+` start a session, `200s+` average duration), but very few ever see `access_gate_viewed` (`< 15%` of total users) or attempt `login_attempt`.
- **Root Causes:**
  1. The unauthenticated guest allowance is so generous that cold visitors satisfy their curiosity in a single 3–4 minute session and leave before ever encountering a "Sign in to save your progress" or premium feature prompt.
  2. There is no natural inline prompt after completing the first free module/deck to save progress or unlock the next level.
- **Remediation:** Trigger a contextual, value-anchoring save-progress / registration prompt immediately upon completing the first free study round or interactive milestone.

### Stage C: Value Gate Viewed → Sign-In / Registration Completed (`< 40%` Gate-to-Login Conversion)
- **Symptoms:** Users see `access_gate_viewed` (`12` views across `7` users) and click `access_gate_action` / `login_attempt` (`4` users), but only `1` completes `login`.
- **Root Causes:**
  1. **In-App WebView OAuth friction:** Google Sign-In (`signInWithPopup` / `signInWithRedirect`) inside Instagram/Facebook's embedded iOS/Android browser frequently fails, loses state, or forces users to re-enter Google credentials they don't remember inside a WebView.
  2. Modal copy frames sign-in as a hard paywall rather than free progress saving.
- **Remediation:**
  1. Inspect `login_attempt` failure codes (`error_code` parameter in GA4) segmented by mobile in-app browser vs. Safari/Chrome.
  2. Support frictionless email/magic-link or one-tap authentication that works reliably inside Instagram/Facebook WebViews, or guide users when OAuth popups are blocked.

### Stage D: Registered / Pricing Viewer → Checkout Started (`< 15%` Package-to-Checkout Rate)
- **Symptoms:** Users view `Packages` / `Credits` (`website_packages_viewed`, `credit_catalog_viewed`), but rarely select a package (`website_package_selected`) or start checkout (`website_checkout_started`).
- **Root Causes:**
  1. Price point jump is too steep for cold social traffic (e.g. only offering a full monthly/quarterly subscription `Rp 129,000` with no low-friction starter pack or trial).
  2. Value proposition on the pricing cards lists abstract feature names instead of concrete outcomes.
- **Remediation:** Introduce a low-friction introductory tier / starter credit pack, highlight the recommended plan, and connect the paywall directly to the feature the user just tried.

### Stage E: Checkout Started → Payment Completed (`< 50%` Checkout Completion Rate)
- **Symptoms:** Backend database / GA4 records initiated checkouts (`website_checkout_started` / `paid_access_grants` with `status = pending | canceled`), but `0` or very few transition to `active` / `purchase`.
- **Root Causes:**
  1. **Single-device QRIS / E-Wallet friction on Mobile:** When a mobile user selects GoPay/QRIS inside an Instagram WebView and is shown a QR code on their own phone screen without an automatic deep-link (`deeplink_redirect`) into the GoPay/banking app, they cannot scan their own screen and abandon the invoice until it expires.
  2. Payment popup (`website_payment_opened`) is blocked by the mobile WebView when opened asynchronously after an API call.
  3. No recovery email or in-app "Resume pending payment" banner when the user returns.
- **Remediation:**
  1. Ensure mobile GoPay/QRIS checkouts trigger the native app deep-link on mobile devices and provide a 1-tap "Download QR / Open in Gojek" flow.
  2. Add a synchronous window/tab handoff or inline QR + deep-link button so WebView popup blockers never swallow the payment redirect.
  3. Cross-check backend payment gateway webhook logs (`expired` vs `canceled` vs `paid`).

---

## 4. Organic vs. Paid Benchmark Comparison

Always pull property-wide traffic (`preset --preset campaigns`) alongside the paid campaign cohort so you can compare paid social against organic channels on the exact same product version:
- **LinkedIn / Organic Social (`linkedin / organic_social`, `linkedin.com / referral`):** Often arrives on desktop or high-intent mobile (`65–68%` engagement rate, `160–330s` average session duration). Use this as the upper-bound engagement benchmark.
- **Instagram Paid Social (`instagram / paid_social`):** Typically arrives 95%+ on mobile inside the Instagram WebView. When an interactive landing route (`/app`) achieves `~60%` engagement rate and `230s+` average session duration on cold Instagram paid traffic, it is performing on par with high-intent organic traffic—proving the creative and landing product experience are strongly aligned.
