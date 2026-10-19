# Connecting to Google Analytics 4 (GA4) & Service Account Setup

Google Analytics 4 (GA4) and Firebase Analytics share the same underlying event storage and reporting engine. Every Firebase project with Google Analytics enabled is linked to a numeric **GA4 Property ID** (`properties/<PROPERTY_ID>`) that can be queried programmatically via the **Google Analytics Data API v1beta** (`https://analyticsdata.googleapis.com/v1beta/properties/<PROPERTY_ID>:runReport`).

---

## 1. Discovering the GA4 Property ID and Streams from Firebase / GCP

Often a repository or deployment config only records the GCP/Firebase `projectId` (for example `gochi-production`) or the public Web `measurementId` (`G-XXXXXXXXXX`). You can discover the numeric GA4 Property ID, GA4 Account ID, and all linked Web, iOS, and Android data streams using the **Firebase Management API**:

```sh
ACCESS_TOKEN="$(gcloud auth print-access-token)"
curl -sS -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  "https://firebase.googleapis.com/v1beta1/projects/${GCP_PROJECT_ID}/analyticsDetails"
```

Or use the bundled helper:

```sh
python3 <skill-dir>/scripts/ga4_report.py discover --project "$GCP_PROJECT_ID"
```

Example response structure:

```json
{
  "analyticsProperty": {
    "id": "521389584",
    "displayName": "gochi-production",
    "accountId": "381804175"
  },
  "streamMappings": [
    {
      "firebaseAppId": "1:681923778851:web:1bf491d06d0779c83cf40c",
      "streamId": "16046022847",
      "measurementId": "G-77YKW9SCC6"
    },
    {
      "firebaseAppId": "1:681923778851:ios:cb93f60908b904443cf40c",
      "streamId": "13360456319"
    }
  ]
}
```

Record these four identifiers in the campaign's `docs/MEASUREMENT.md`:
- **GCP / Firebase Project ID:** e.g. `gochi-production`
- **GA4 Account ID:** `analyticsProperty.accountId` (e.g. `381804175`)
- **GA4 Property ID:** `analyticsProperty.id` (e.g. `521389584`)
- **Stream IDs & Measurement ID:** Web `measurementId` (`G-...`) and iOS/Android `streamId`s

---

## 2. Why Service Account Authentication Is Required (and Why `gcloud` OAuth Fails)

When you run:

```sh
gcloud auth application-default login \
  --scopes="https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/analytics.readonly"
```

Google's browser consent screen rejects the login with:

> **This app is blocked** — This app tried to access sensitive info in your Google Account. To keep your account safe, Google blocked this access.

### Why this happens
`gcloud` uses a shared, public OAuth client ID built into the Google Cloud SDK. Because `https://www.googleapis.com/auth/analytics.readonly` is classified as a sensitive Google Analytics scope outside standard Cloud Platform IAM, Google blocks the shared public `gcloud` OAuth client from requesting it interactively unless you supply a custom OAuth client (`--client-id-file`).

### The reliable solution: Service Account JWT Authentication
A **GCP Service Account JSON key** bypasses interactive browser OAuth completely:
1. The helper signs a short-lived RS256 JWT assertion using the service account's `private_key` and `client_email` with `scope: "https://www.googleapis.com/auth/analytics.readonly"`.
2. It exchanges that JWT directly at `https://oauth2.googleapis.com/token` (`grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer`) for a 1-hour Bearer access token.
3. It calls `https://analyticsdata.googleapis.com/v1beta/properties/<PROPERTY_ID>:runReport` directly—no browser prompt, no OAuth consent block, and deterministic automation for CLI and agent workflows.

---

## 3. Step-by-Step Setup Checklist

### Step 1: Enable the Google Analytics Data API on the GCP Project

Enable `analyticsdata.googleapis.com` (and optionally `analyticsadmin.googleapis.com`) on the Google Cloud project that owns the service account:

```sh
gcloud services enable analyticsdata.googleapis.com analyticsadmin.googleapis.com \
  --project="$GCP_PROJECT_ID"
```

*(Note: After enabling the API for the first time, wait 30–60 seconds for Google's service activation cache to propagate.)*

### Step 2: Create or Reuse a GCP Service Account

Identify an existing service account or create a dedicated read-only service account:

```sh
gcloud iam service-accounts list --project="$GCP_PROJECT_ID"

# Or create a dedicated analytics reader service account:
gcloud iam service-accounts create ga4-analytics-reader \
  --display-name="GA4 Analytics Reader" \
  --project="$GCP_PROJECT_ID"
```

### Step 3: Grant the Service Account "Viewer" Access in GA4 Property Access Management

> **Critical Gotcha:** Granting `roles/viewer` or `roles/firebase.analyticsViewer` in **Google Cloud IAM** is **not sufficient** when the GA4 Property permissions are governed by a Google Analytics account. Otherwise, the GA4 Data API returns `403 PERMISSION_DENIED: User does not have sufficient permissions for this property`.

Grant property access directly in Google Analytics:
1. Open **GA4 Property Access Management** using the Account ID and Property ID from `discover`:
   `https://analytics.google.com/analytics/web/#/a<ACCOUNT_ID>p<PROPERTY_ID>/admin/property/users`
   *(Or in the Firebase Console: **Project settings → Integrations → Google Analytics → Manage → Admin → Property access management**).*
2. Click the blue **`+`** button in the top-right corner → **Add users**.
3. Paste the service account email address (for example `ga4-analytics-reader@<project-id>.iam.gserviceaccount.com` or `<service>@<project-id>.iam.gserviceaccount.com`).
4. Uncheck *"Notify new users by email"*.
5. Select the **Viewer** role (read-only access to reports, configurations, and Data API queries).
6. Click **Add**. Access takes effect within 10–30 seconds.

### Step 4: Provide the Service Account Key to the Agent / Helper

Support two clean operating modes depending on where the key resides:

#### Option A: Local key file via `~/.config/marketing-creative/.env`
Store the service account JSON outside the repository (for example `~/.config/gcloud/sa-ga4-reader.json` with `chmod 600`) and reference its path in `~/.config/marketing-creative/.env`:

```sh
mkdir -p "$HOME/.config/marketing-creative"
chmod 700 "$HOME/.config/marketing-creative"
chmod 600 "$HOME/.config/marketing-creative/.env"
```

In `~/.config/marketing-creative/.env`:

```sh
GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcloud/sa-ga4-reader.json"
GA4_PROPERTY_ID="521389584"
```

Load it in the shell that runs `ga4_report.py`:

```sh
set -a
. "$HOME/.config/marketing-creative/.env"
set +a
python3 <skill-dir>/scripts/ga4_report.py preset --property "$GA4_PROPERTY_ID" --preset campaigns
```

#### Option B: Remote execution via SSH when the Service Account lives on a backend server
If the production service account JSON is stored on a remote application server (for example `/opt/app/shared/config/service-account.json`) and should not be copied to a laptop, pipe or run `ga4_report.py` directly over SSH:

```sh
ssh user@production-host "python3 - preset --property 521389584 --preset campaigns --service-account /opt/app/shared/config/service-account.json" \
  < <skill-dir>/scripts/ga4_report.py
```

### Security Rules
- Never print `private_key`, raw JWT assertions, or OAuth `access_token` values in terminal output, reports, or commits.
- Never store service account JSON files inside a Git repository or campaign workspace.
- Always use read-only scopes (`https://www.googleapis.com/auth/analytics.readonly` and `https://www.googleapis.com/auth/firebase.readonly`).

---

## 4. Troubleshooting Common Errors

| HTTP Status / Error Code | Root Cause | Fix |
| --- | --- | --- |
| `This app is blocked` in browser during `gcloud auth` | `gcloud`'s shared OAuth client is blocked from requesting `analytics.readonly` interactively | Stop using `gcloud auth application-default login` for GA4. Use a Service Account JSON key (`--service-account` / `GOOGLE_APPLICATION_CREDENTIALS`). |
| `403 SERVICE_DISABLED` (`Google Analytics Data API has not been used in project ...`) | `analyticsdata.googleapis.com` is disabled on the GCP project that owns the service account | Run `gcloud services enable analyticsdata.googleapis.com --project=<PROJECT_ID>` and wait 30–60s. |
| `403 PERMISSION_DENIED` (`User does not have sufficient permissions for this property`) | Service account exists in GCP IAM, but has not been added to the GA4 Property | Add `<service-account>@<project>.iam.gserviceaccount.com` as **Viewer** in GA4 Admin → **Property access management**. |
| `400 INVALID_ARGUMENT` (`Field ... is not a valid dimension / metric`) | Custom dimension not registered in GA4, or incompatible dimension/metric scope | Run `ga4_report.py metadata --property <ID>` to inspect valid API names and scopes. |
| `(not set)` on `unifiedScreenName` for Web traffic | Web `gtag.js` sends `screen_name` instead of `firebase_screen` on `screen_view` events | Pass both `firebase_screen` and `screen_name` (and `firebase_screen_class` + `screen_class`) in the web analytics emitter, and use `pagePath` for historical Web sessions. |
