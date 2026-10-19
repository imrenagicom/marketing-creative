#!/usr/bin/env python3
"""Query Google Analytics 4 (GA4) Data API v1beta and Firebase Analytics discovery (stdlib only)."""
import argparse
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

ANALYTICS_READONLY_SCOPE = "https://www.googleapis.com/auth/analytics.readonly"
FIREBASE_READONLY_SCOPE = (
    "https://www.googleapis.com/auth/firebase.readonly "
    "https://www.googleapis.com/auth/cloud-platform.read-only"
)
DEFAULT_TOKEN_URI = "https://oauth2.googleapis.com/token"
GA4_BASE_URL = "https://analyticsdata.googleapis.com/v1beta"
FIREBASE_BASE_URL = "https://firebase.googleapis.com/v1beta1"

PRESETS = (
    "campaigns",
    "ad-content",
    "funnel",
    "screens",
    "daily",
    "realtime",
)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def resolve_service_account_path(explicit_path: str | None = None) -> Path:
    raw = (
        explicit_path
        or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        or os.environ.get("GA4_SERVICE_ACCOUNT_FILE")
    )
    if not raw:
        raise ValueError(
            "Missing service account path: pass --service-account or set "
            "GOOGLE_APPLICATION_CREDENTIALS / GA4_SERVICE_ACCOUNT_FILE"
        )
    path = Path(raw).expanduser().resolve()
    if not path.is_file():
        raise ValueError(f"Service account file not found: {path}")
    return path


def load_service_account(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Invalid service account JSON at {path}: {exc}") from exc
    if not isinstance(data, dict) or data.get("type") != "service_account":
        raise ValueError(f"Expected a GCP service_account JSON file at {path}")
    for field in ("client_email", "private_key"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise ValueError(f"Service account JSON missing required field '{field}'")
    return data


def sign_rs256_jwt(private_key_pem: str, signing_input: bytes) -> bytes:
    with tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False, encoding="utf-8") as handle:
        key_file = Path(handle.name)
        handle.write(private_key_pem)
    try:
        os.chmod(key_file, 0o600)
        proc = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", str(key_file)],
            input=signing_input,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            stderr = proc.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"openssl failed to sign JWT assertion: {stderr}")
        return proc.stdout
    finally:
        key_file.unlink(missing_ok=True)


def mint_service_account_token(
    sa_info: dict,
    scope: str = ANALYTICS_READONLY_SCOPE,
    now: int | None = None,
) -> str:
    issued_at = int(time.time()) if now is None else int(now)
    token_uri = sa_info.get("token_uri") or DEFAULT_TOKEN_URI
    header = {"alg": "RS256", "typ": "JWT"}
    if sa_info.get("private_key_id"):
        header["kid"] = sa_info["private_key_id"]
    claims = {
        "iss": sa_info["client_email"],
        "scope": scope,
        "aud": token_uri,
        "iat": issued_at,
        "exp": issued_at + 3600,
    }
    signing_input = (
        f"{_b64url(json.dumps(header, separators=(',', ':')).encode('utf-8'))}."
        f"{_b64url(json.dumps(claims, separators=(',', ':')).encode('utf-8'))}"
    ).encode("ascii")
    signature = sign_rs256_jwt(sa_info["private_key"], signing_input)
    assertion = f"{signing_input.decode('ascii')}.{_b64url(signature)}"

    form_body = urllib.parse.urlencode(
        {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        token_uri,
        data=form_body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OAuth token exchange failed (HTTP {exc.code}): {detail}") from exc
    token = payload.get("access_token")
    if not token:
        raise RuntimeError("OAuth token response did not include an access_token")
    return token


def gcloud_access_token() -> str:
    proc = subprocess.run(
        ["gcloud", "auth", "print-access-token"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        stderr = (proc.stderr or "").strip()
        raise RuntimeError(f"Unable to obtain access token via gcloud: {stderr}")
    return proc.stdout.strip()


def normalize_property_id(raw_property: str) -> str:
    value = str(raw_property or "").strip()
    if value.startswith("properties/"):
        value = value.split("/", 1)[1].strip()
    if not value or not value.isdigit():
        raise ValueError(
            f"Invalid GA4 property ID '{raw_property}': expected numeric ID (e.g. 521389584)"
        )
    return value


def build_filter_expression(
    campaign: str | None = None,
    ad_content: str | None = None,
    event_names: list[str] | None = None,
) -> dict | None:
    expressions = []
    if campaign:
        expressions.append(
            {
                "filter": {
                    "fieldName": "sessionCampaignName",
                    "stringFilter": {"matchType": "EXACT", "value": campaign},
                }
            }
        )
    if ad_content:
        expressions.append(
            {
                "filter": {
                    "fieldName": "sessionManualAdContent",
                    "stringFilter": {"matchType": "EXACT", "value": ad_content},
                }
            }
        )
    if event_names:
        cleaned = [e.strip() for e in event_names if e and e.strip()]
        if len(cleaned) == 1:
            expressions.append(
                {
                    "filter": {
                        "fieldName": "eventName",
                        "stringFilter": {"matchType": "EXACT", "value": cleaned[0]},
                    }
                }
            )
        elif len(cleaned) > 1:
            expressions.append(
                {
                    "filter": {
                        "fieldName": "eventName",
                        "inListFilter": {"values": cleaned, "caseSensitive": True},
                    }
                }
            )
    if not expressions:
        return None
    if len(expressions) == 1:
        return expressions[0]
    return {"andGroup": {"expressions": expressions}}


def build_report_request(
    *,
    dimensions: list[str],
    metrics: list[str],
    start_date: str = "7daysAgo",
    end_date: str = "today",
    campaign: str | None = None,
    ad_content: str | None = None,
    event_names: list[str] | None = None,
    order_by_metric: str | None = None,
    order_by_dimension: str | None = None,
    order_desc: bool = True,
    limit: int = 250,
    realtime: bool = False,
) -> dict:
    if not dimensions:
        raise ValueError("At least one dimension is required")
    if not metrics:
        raise ValueError("At least one metric is required")
    if limit <= 0 or limit > 100000:
        raise ValueError("limit must be between 1 and 100000")

    body: dict = {
        "dimensions": [{"name": d.strip()} for d in dimensions if d.strip()],
        "metrics": [{"name": m.strip()} for m in metrics if m.strip()],
        "limit": limit,
    }
    if not realtime:
        body["dateRanges"] = [{"startDate": start_date, "endDate": end_date}]
        body["keepEmptyRows"] = False

    dimension_filter = build_filter_expression(
        campaign=campaign,
        ad_content=ad_content,
        event_names=event_names,
    )
    if dimension_filter is not None:
        body["dimensionFilter"] = dimension_filter

    if order_by_metric:
        body["orderBys"] = [{"metric": {"metricName": order_by_metric}, "desc": order_desc}]
    elif order_by_dimension:
        body["orderBys"] = [
            {"dimension": {"dimensionName": order_by_dimension}, "desc": order_desc}
        ]
    return body


def build_preset_spec(
    preset: str,
    *,
    start_date: str = "7daysAgo",
    end_date: str = "today",
    campaign: str | None = None,
    ad_content: str | None = None,
    limit: int = 250,
) -> tuple[str, dict]:
    if preset not in PRESETS:
        raise ValueError(f"Unsupported preset '{preset}'. Choose from: {', '.join(PRESETS)}")

    if preset == "campaigns":
        return (
            "runReport",
            build_report_request(
                dimensions=[
                    "sessionSourceMedium",
                    "sessionCampaignName",
                    "sessionManualAdContent",
                ],
                metrics=[
                    "sessions",
                    "engagedSessions",
                    "engagementRate",
                    "averageSessionDuration",
                    "totalUsers",
                    "newUsers",
                    "eventCount",
                ],
                start_date=start_date,
                end_date=end_date,
                campaign=campaign,
                ad_content=ad_content,
                order_by_metric="sessions",
                limit=limit,
            ),
        )
    if preset == "ad-content":
        return (
            "runReport",
            build_report_request(
                dimensions=[
                    "sessionCampaignName",
                    "sessionManualAdContent",
                    "deviceCategory",
                ],
                metrics=[
                    "sessions",
                    "engagedSessions",
                    "engagementRate",
                    "averageSessionDuration",
                    "userEngagementDuration",
                    "totalUsers",
                    "newUsers",
                    "eventCount",
                ],
                start_date=start_date,
                end_date=end_date,
                campaign=campaign,
                ad_content=ad_content,
                order_by_metric="sessions",
                limit=limit,
            ),
        )
    if preset == "funnel":
        return (
            "runReport",
            build_report_request(
                dimensions=[
                    "sessionCampaignName",
                    "sessionManualAdContent",
                    "eventName",
                ],
                metrics=[
                    "eventCount",
                    "totalUsers",
                    "sessions",
                ],
                start_date=start_date,
                end_date=end_date,
                campaign=campaign,
                ad_content=ad_content,
                order_by_metric="totalUsers",
                limit=limit,
            ),
        )
    if preset == "screens":
        return (
            "runReport",
            build_report_request(
                dimensions=[
                    "sessionCampaignName",
                    "sessionManualAdContent",
                    "pagePath",
                    "unifiedScreenName",
                ],
                metrics=[
                    "screenPageViews",
                    "totalUsers",
                    "engagedSessions",
                    "userEngagementDuration",
                ],
                start_date=start_date,
                end_date=end_date,
                campaign=campaign,
                ad_content=ad_content,
                order_by_metric="screenPageViews",
                limit=limit,
            ),
        )
    if preset == "daily":
        return (
            "runReport",
            build_report_request(
                dimensions=[
                    "date",
                    "sessionSourceMedium",
                    "sessionCampaignName",
                    "sessionManualAdContent",
                ],
                metrics=[
                    "sessions",
                    "engagedSessions",
                    "engagementRate",
                    "averageSessionDuration",
                    "totalUsers",
                    "newUsers",
                    "eventCount",
                ],
                start_date=start_date,
                end_date=end_date,
                campaign=campaign,
                ad_content=ad_content,
                order_by_dimension="date",
                order_desc=False,
                limit=limit,
            ),
        )
    # realtime
    return (
        "runRealtimeReport",
        build_report_request(
            dimensions=["unifiedScreenName", "eventName"],
            metrics=["eventCount", "activeUsers"],
            limit=limit,
            realtime=True,
        ),
    )


def format_report_response(raw_response: dict, property_id: str, method: str) -> dict:
    dim_headers = [h.get("name", "") for h in raw_response.get("dimensionHeaders", [])]
    met_headers = [h.get("name", "") for h in raw_response.get("metricHeaders", [])]
    rows = []
    for row in raw_response.get("rows", []):
        entry = {}
        for idx, dim in enumerate(row.get("dimensionValues", [])):
            key = dim_headers[idx] if idx < len(dim_headers) else f"dimension_{idx}"
            entry[key] = dim.get("value", "")
        for idx, met in enumerate(row.get("metricValues", [])):
            key = met_headers[idx] if idx < len(met_headers) else f"metric_{idx}"
            val = met.get("value", "0")
            if "." in val:
                try:
                    entry[key] = round(float(val), 4)
                except ValueError:
                    entry[key] = val
            else:
                try:
                    entry[key] = int(val)
                except ValueError:
                    entry[key] = val
        rows.append(entry)
    return {
        "ok": True,
        "property_id": property_id,
        "method": method,
        "row_count": raw_response.get("rowCount", len(rows)),
        "dimensions": dim_headers,
        "metrics": met_headers,
        "metadata": raw_response.get("metadata", {}),
        "rows": rows,
    }


def http_json(url: str, token: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="GET" if payload is None else "POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GA4 API error (HTTP {exc.code}) on {url}: {detail}") from exc


def run_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Query GA4 Data API v1beta and Firebase Analytics details."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # discover
    discover_p = subparsers.add_parser(
        "discover",
        help="Discover GA4 Property ID, Account ID, and streams linked to a Firebase/GCP project",
    )
    discover_p.add_argument("--project", required=True, help="GCP / Firebase project ID")
    discover_p.add_argument("--service-account", help="Optional path to service account JSON")
    discover_p.add_argument("--dry-run", action="store_true", help="Print request without calling API")

    # metadata
    meta_p = subparsers.add_parser(
        "metadata",
        help="Fetch available standard and custom dimensions/metrics for a GA4 property",
    )
    meta_p.add_argument(
        "--property",
        default=os.environ.get("GA4_PROPERTY_ID"),
        required=not bool(os.environ.get("GA4_PROPERTY_ID")),
        help="Numeric GA4 Property ID (or set GA4_PROPERTY_ID)",
    )
    meta_p.add_argument("--service-account", help="Path to service account JSON")
    meta_p.add_argument("--custom-only", action="store_true", help="Return only custom dimensions/metrics")
    meta_p.add_argument("--dry-run", action="store_true", help="Print request without calling API")

    # preset
    preset_p = subparsers.add_parser(
        "preset",
        help="Run a standard campaign or funnel diagnostic preset",
    )
    preset_p.add_argument(
        "--property",
        default=os.environ.get("GA4_PROPERTY_ID"),
        required=not bool(os.environ.get("GA4_PROPERTY_ID")),
        help="Numeric GA4 Property ID (or set GA4_PROPERTY_ID)",
    )
    preset_p.add_argument("--preset", choices=PRESETS, required=True, help="Diagnostic preset name")
    preset_p.add_argument("--start-date", default="7daysAgo", help="YYYY-MM-DD or NdaysAgo")
    preset_p.add_argument("--end-date", default="today", help="YYYY-MM-DD, today, or yesterday")
    preset_p.add_argument("--campaign", help="Optional exact sessionCampaignName (utm_campaign) filter")
    preset_p.add_argument("--ad-content", help="Optional exact sessionManualAdContent (utm_content) filter")
    preset_p.add_argument("--limit", type=int, default=250, help="Max rows (default 250)")
    preset_p.add_argument("--service-account", help="Path to service account JSON")
    preset_p.add_argument("--dry-run", action="store_true", help="Preview request JSON without network call")

    # query
    query_p = subparsers.add_parser(
        "query",
        help="Run a custom GA4 Data API runReport query",
    )
    query_p.add_argument(
        "--property",
        default=os.environ.get("GA4_PROPERTY_ID"),
        required=not bool(os.environ.get("GA4_PROPERTY_ID")),
        help="Numeric GA4 Property ID (or set GA4_PROPERTY_ID)",
    )
    query_p.add_argument("--dimensions", required=True, help="Comma-separated GA4 dimension names")
    query_p.add_argument("--metrics", required=True, help="Comma-separated GA4 metric names")
    query_p.add_argument("--start-date", default="7daysAgo", help="YYYY-MM-DD or NdaysAgo")
    query_p.add_argument("--end-date", default="today", help="YYYY-MM-DD, today, or yesterday")
    query_p.add_argument("--campaign", help="Optional exact sessionCampaignName (utm_campaign) filter")
    query_p.add_argument("--ad-content", help="Optional exact sessionManualAdContent (utm_content) filter")
    query_p.add_argument("--event-names", help="Optional comma-separated eventName filter")
    query_p.add_argument("--order-by-metric", help="Metric name to sort descending")
    query_p.add_argument("--limit", type=int, default=250, help="Max rows (default 250)")
    query_p.add_argument("--service-account", help="Path to service account JSON")
    query_p.add_argument("--dry-run", action="store_true", help="Preview request JSON without network call")

    args = parser.parse_args(argv)

    try:
        if args.command == "discover":
            url = f"{FIREBASE_BASE_URL}/projects/{args.project.strip()}/analyticsDetails"
            if args.dry_run:
                print(json.dumps({"dry_run": True, "method": "GET", "url": url}, indent=2))
                return 0
            if args.service_account or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or os.environ.get("GA4_SERVICE_ACCOUNT_FILE"):
                sa_path = resolve_service_account_path(args.service_account)
                token = mint_service_account_token(load_service_account(sa_path), scope=FIREBASE_READONLY_SCOPE)
            else:
                token = gcloud_access_token()
            raw = http_json(url, token)
            print(json.dumps({"ok": True, "project": args.project, "analyticsDetails": raw}, indent=2))
            return 0

        prop_id = normalize_property_id(args.property)

        if args.command == "metadata":
            url = f"{GA4_BASE_URL}/properties/{prop_id}/metadata"
            if args.dry_run:
                print(json.dumps({"dry_run": True, "method": "GET", "url": url, "property_id": prop_id}, indent=2))
                return 0
            sa_path = resolve_service_account_path(args.service_account)
            token = mint_service_account_token(load_service_account(sa_path))
            raw = http_json(url, token)
            dims = raw.get("dimensions", [])
            mets = raw.get("metrics", [])
            if args.custom_only:
                dims = [d for d in dims if d.get("customDefinition")]
                mets = [m for m in mets if m.get("customDefinition")]
            print(
                json.dumps(
                    {
                        "ok": True,
                        "property_id": prop_id,
                        "dimension_count": len(dims),
                        "metric_count": len(mets),
                        "dimensions": dims,
                        "metrics": mets,
                    },
                    indent=2,
                )
            )
            return 0

        if args.command == "preset":
            api_method, body = build_preset_spec(
                args.preset,
                start_date=args.start_date,
                end_date=args.end_date,
                campaign=args.campaign,
                ad_content=args.ad_content,
                limit=args.limit,
            )
        else:
            dims = [d.strip() for d in args.dimensions.split(",") if d.strip()]
            mets = [m.strip() for m in args.metrics.split(",") if m.strip()]
            events = (
                [e.strip() for e in args.event_names.split(",") if e.strip()]
                if args.event_names
                else None
            )
            api_method = "runReport"
            body = build_report_request(
                dimensions=dims,
                metrics=mets,
                start_date=args.start_date,
                end_date=args.end_date,
                campaign=args.campaign,
                ad_content=args.ad_content,
                event_names=events,
                order_by_metric=args.order_by_metric or (mets[0] if mets else None),
                limit=args.limit,
            )

        url = f"{GA4_BASE_URL}/properties/{prop_id}:{api_method}"
        if args.dry_run:
            print(
                json.dumps(
                    {
                        "dry_run": True,
                        "property_id": prop_id,
                        "method": api_method,
                        "url": url,
                        "request": body,
                    },
                    indent=2,
                )
            )
            return 0

        sa_path = resolve_service_account_path(args.service_account)
        token = mint_service_account_token(load_service_account(sa_path))
        raw = http_json(url, token, body)
        formatted = format_report_response(raw, prop_id, api_method)
        print(json.dumps(formatted, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(run_cli())
