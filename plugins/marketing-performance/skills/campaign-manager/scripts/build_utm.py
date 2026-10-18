#!/usr/bin/env python3
"""Validate a static campaign link plan and save a new, immutable export revision."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

UTM_KEYS = ("utm_source", "utm_medium", "utm_campaign", "utm_id",
            "utm_content", "utm_term", "utm_source_platform")
REQUIRED = {"utm_source", "utm_medium", "utm_campaign"}
AD_PLATFORMS = {"meta-ads"}
SOCIAL_PLATFORMS = ("instagram", "linkedin", "twitter")
HIERARCHY_KEYS = ("platform", "platform_campaign", "adset", "ad", "post")
META_KEYS = (*HIERARCHY_KEYS, "placement", "creative_id", "status", "notes")
COLUMNS = ("campaign_id", "link_id", *META_KEYS, "destination_url", *UTM_KEYS, "url_tags", "url")
AD_STATUSES = {"planned", "paused", "active", "archived", "retired"}
POST_STATUSES = {"planned", "paused", "active", "published", "archived", "retired"}
POST_FORMATS = {"single_image", "carousel", "video", "reel", "story", "text", "thread", "document", "article"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value, label):
    require(isinstance(value, str) and bool(value.strip()), f"{label} must be a nonempty string")
    require(value == value.strip(), f"{label} must not have surrounding whitespace")
    require(not any(ord(c) < 32 or ord(c) == 127 for c in value), f"{label} contains control characters")
    return value


def identifier(value, label):
    value = text(value, label)
    require(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value), f"{label} must be a lowercase slug")
    return value


def object_fields(value, allowed, label):
    require(isinstance(value, dict), f"{label} must be an object")
    require(not set(value) - set(allowed), f"{label} contains unsupported fields")


def utm_values(value, label):
    object_fields(value, UTM_KEYS, label)
    for key, item in value.items():
        text(item, f"{label}.{key}")
        require(not any(c in unquote(item) for c in "{}"), f"{label}.{key}: static values only; macros are unsupported")
    return value


def serialize_url_tags(utm):
    return urlencode([(key, utm[key]) for key in UTM_KEYS if key in utm])


def tagged_url(destination, utm):
    text(destination, "destination_url")
    require(not any(c.isspace() for c in destination), "destination_url must encode whitespace")
    require(not re.search(r"%(?![0-9a-fA-F]{2})", destination), "destination_url contains invalid percent encoding")
    require(not any(c in unquote(destination) for c in "{}"), "destination_url contains an unresolved macro")
    require(not any(ord(c) < 32 or ord(c) == 127 for c in unquote(destination)),
            "destination_url contains encoded control characters")
    parts = urlsplit(destination)
    require(parts.scheme in {"http", "https"} and parts.hostname, "destination_url must be absolute HTTP(S)")
    require(parts.username is None and parts.password is None, "destination_url must not contain credentials")
    # Accessing port also rejects malformed or out-of-range ports.
    _ = parts.port
    require(not any(k.lower().startswith("utm_") for k, _ in parse_qsl(parts.query, keep_blank_values=True)),
            "destination_url already contains UTM parameters; resolve ownership before building")
    encoded = serialize_url_tags(utm)
    separator = "&" if parts.query and not parts.query.endswith("&") else ""
    result = urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query + separator + encoded, parts.fragment))
    round_trip = {k: v for k, v in parse_qsl(urlsplit(result).query, keep_blank_values=True) if k in UTM_KEYS}
    require(round_trip == utm, "UTM serialization did not round-trip")
    return result


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON object key")
        result[key] = value
    return result


def read_json_file(path):
    return json.loads(Path(path).read_bytes().decode("utf-8"), object_pairs_hook=unique_keys)


def build_plan(plan):
    object_fields(plan, {"schema_version", "campaign_id", "defaults", "links"}, "plan")
    require(type(plan.get("schema_version")) is int and plan["schema_version"] == 1,
            "schema_version must be 1")
    campaign_id = identifier(plan.get("campaign_id"), "campaign_id")
    defaults = utm_values(plan.get("defaults"), "defaults")
    require("utm_campaign" in defaults, "defaults.utm_campaign is required")
    links = plan.get("links")
    require(isinstance(links, list) and links, "links must be a nonempty list")
    rows, warnings, ids, urls = [], [], set(), {}
    for index, link in enumerate(links):
        label = f"links[{index}]"
        object_fields(link, {"link_id", "destination_url", "utm", *META_KEYS}, label)
        link_id = identifier(link.get("link_id"), f"{label}.link_id")
        require(link_id not in ids, f"Duplicate link_id: {link_id}")
        ids.add(link_id)
        values = {**defaults, **utm_values(link.get("utm"), f"{label}.utm")}
        require(REQUIRED <= values.keys(), f"{label} needs source, medium and campaign")
        for key in ("utm_campaign", "utm_id"):
            require(values.get(key) == defaults.get(key), f"{label}.{key} must match campaign defaults")
        metadata = {key: link.get(key, "planned" if key == "status" else "") for key in META_KEYS}
        for key, value in metadata.items():
            require(isinstance(value, str), f"{label}.{key} must be a string")
            if value:
                if key in HIERARCHY_KEYS:
                    identifier(value, f"{label}.{key}")
                else:
                    text(value, f"{label}.{key}")
        platform = metadata["platform"]
        if platform in AD_PLATFORMS:
            require(all(metadata[key] for key in ("platform_campaign", "adset", "ad")) and not metadata["post"],
                    f"{label} must specify platform, platform_campaign, adset and ad together")
        elif platform in SOCIAL_PLATFORMS:
            require(bool(metadata["post"]) and not any(metadata[key] for key in ("platform_campaign", "adset", "ad")),
                    f"{label} with social platform '{platform}' must specify post (and not platform_campaign, adset or ad)")
        elif platform:
            raise ValueError(f"{label}.platform '{platform}' is unsupported")
        else:
            require(not any(metadata[key] for key in ("platform_campaign", "adset", "ad", "post")),
                    f"{label} must specify platform when platform_campaign, adset, ad or post is set")
        require(metadata["status"] in {"planned", "published", "retired"}, f"{label}: invalid status")
        destination = link.get("destination_url")
        url = tagged_url(destination, values)
        url_tags = serialize_url_tags(values)
        if url in urls:
            warnings.append(f"Links {urls[url]} and {link_id} resolve to the same URL; confirm variant mapping")
        urls[url] = link_id
        rows.append({"campaign_id": campaign_id, "link_id": link_id, **metadata,
                     "destination_url": destination, **{k: values.get(k, "") for k in UTM_KEYS},
                     "url_tags": url_tags, "url": url})
    return {"campaign_id": campaign_id, "links": rows, "warnings": warnings}


def validate_meta_tree(meta_root, plan_result):
    meta_root = Path(meta_root)
    campaigns_root = meta_root / "campaigns"
    require(campaigns_root.is_dir() and not campaigns_root.is_symlink(),
            "meta-ads/campaigns must be a real directory")
    campaign_dirs = sorted(p for p in campaigns_root.iterdir() if p.is_dir())
    require(bool(campaign_dirs), "meta-ads/campaigns must contain at least one campaign directory")
    links_by_id = {row["link_id"]: row for row in plan_result["links"]}
    matched_links = set()
    summary = []
    for campaign_dir in campaign_dirs:
        require(not campaign_dir.is_symlink(), f"Symlinked Meta campaign directory: {campaign_dir}")
        campaign_slug = identifier(campaign_dir.name, "meta-ads campaign directory")
        campaign_spec = read_json_file(campaign_dir / "campaign.json")
        object_fields(campaign_spec, {
            "schema_version", "platform", "campaign_slug", "name", "objective",
            "buying_type", "special_ad_categories", "budget", "status",
            "remote_campaign_id", "notes"
        }, f"meta-ads/{campaign_slug}/campaign.json")
        require(type(campaign_spec.get("schema_version")) is int and campaign_spec["schema_version"] == 1,
                f"meta-ads/{campaign_slug}/campaign.json: schema_version must be 1")
        require(campaign_spec.get("platform") == "meta-ads",
                f"meta-ads/{campaign_slug}/campaign.json: platform must be 'meta-ads'")
        require(campaign_spec.get("campaign_slug") == campaign_slug,
                f"meta-ads/{campaign_slug}/campaign.json: campaign_slug must match directory name")
        text(campaign_spec.get("name"), f"meta-ads/{campaign_slug}.name")
        text(campaign_spec.get("objective"), f"meta-ads/{campaign_slug}.objective")
        budget = campaign_spec.get("budget")
        require(isinstance(budget, dict) and budget.get("mode") in {"cbo", "abo"},
                f"meta-ads/{campaign_slug}.budget must define mode 'cbo' or 'abo'")
        require(campaign_spec.get("status") in AD_STATUSES, f"meta-ads/{campaign_slug}: invalid status")
        adsets_root = campaign_dir / "adsets"
        require(adsets_root.is_dir() and not adsets_root.is_symlink(),
                f"meta-ads/{campaign_slug}/adsets must be a real directory")
        adset_dirs = sorted(p for p in adsets_root.iterdir() if p.is_dir())
        require(bool(adset_dirs), f"meta-ads/{campaign_slug}/adsets must contain at least one adset directory")
        for adset_dir in adset_dirs:
            require(not adset_dir.is_symlink(), f"Symlinked Meta adset directory: {adset_dir}")
            adset_slug = identifier(adset_dir.name, "meta-ads adset directory")
            adset_label = f"meta-ads/{campaign_slug}/adsets/{adset_slug}"
            adset_spec = read_json_file(adset_dir / "adset.json")
            object_fields(adset_spec, {
                "schema_version", "adset_slug", "name", "optimization_goal",
                "billing_event", "conversion", "budget", "schedule",
                "targeting", "placements", "status", "remote_adset_id", "notes"
            }, f"{adset_label}/adset.json")
            require(type(adset_spec.get("schema_version")) is int and adset_spec["schema_version"] == 1,
                    f"{adset_label}/adset.json: schema_version must be 1")
            require(adset_spec.get("adset_slug") == adset_slug,
                    f"{adset_label}/adset.json: adset_slug must match directory name")
            text(adset_spec.get("name"), f"{adset_label}.name")
            text(adset_spec.get("optimization_goal"), f"{adset_label}.optimization_goal")
            targeting = adset_spec.get("targeting")
            require(isinstance(targeting, dict) and bool(targeting),
                    f"{adset_label}.targeting must be a nonempty object")
            placements = adset_spec.get("placements")
            require(isinstance(placements, (dict, list)) and bool(placements),
                    f"{adset_label}.placements must be a nonempty object or list")
            require(adset_spec.get("status") in AD_STATUSES, f"{adset_label}: invalid status")
            ads_root = adset_dir / "ads"
            require(ads_root.is_dir() and not ads_root.is_symlink(),
                    f"{adset_label}/ads must be a real directory")
            ad_dirs = sorted(p for p in ads_root.iterdir() if p.is_dir())
            require(bool(ad_dirs), f"{adset_label}/ads must contain at least one ad directory")
            for ad_dir in ad_dirs:
                require(not ad_dir.is_symlink(), f"Symlinked Meta ad directory: {ad_dir}")
                ad_slug = identifier(ad_dir.name, "meta-ads ad directory")
                ad_label = f"{adset_label}/ads/{ad_slug}"
                ad_spec = read_json_file(ad_dir / "ad.json")
                object_fields(ad_spec, {
                    "schema_version", "ad_slug", "name", "status", "format",
                    "call_to_action", "link_id", "destination_url", "utm",
                    "url_tags", "approved_copy_revision", "approved_assets_revision",
                    "remote_ad_id", "remote_creative_id", "video_id", "image_hash", "notes"
                }, f"{ad_label}/ad.json")
                require(type(ad_spec.get("schema_version")) is int and ad_spec["schema_version"] == 1,
                        f"{ad_label}/ad.json: schema_version must be 1")
                require(ad_spec.get("ad_slug") == ad_slug,
                        f"{ad_label}/ad.json: ad_slug must match directory name")
                text(ad_spec.get("name"), f"{ad_label}.name")
                require(ad_spec.get("status") in AD_STATUSES, f"{ad_label}: invalid status")
                require(ad_spec.get("format") in {"video", "single_image", "carousel"},
                        f"{ad_label}: invalid format")
                text(ad_spec.get("call_to_action"), f"{ad_label}.call_to_action")
                link_id = identifier(ad_spec.get("link_id"), f"{ad_label}.link_id")
                require(link_id in links_by_id, f"{ad_label}.link_id '{link_id}' not found in campaign.json")
                require(link_id not in matched_links, f"Duplicate Meta ad binding for link_id '{link_id}'")
                matched_links.add(link_id)
                link_row = links_by_id[link_id]
                require((link_row["platform"], link_row["platform_campaign"],
                         link_row["adset"], link_row["ad"]) == ("meta-ads", campaign_slug, adset_slug, ad_slug),
                        f"{ad_label} hierarchy does not match campaign.json link '{link_id}'")
                require(ad_spec.get("destination_url") == link_row["destination_url"],
                        f"{ad_label}.destination_url does not match campaign.json link '{link_id}'")
                ad_utm = utm_values(ad_spec.get("utm"), f"{ad_label}.utm")
                expected_utm = {k: link_row[k] for k in UTM_KEYS if link_row[k]}
                require(ad_utm == expected_utm,
                        f"{ad_label}.utm does not match resolved UTM values for '{link_id}'")
                if "url_tags" in ad_spec:
                    require(ad_spec["url_tags"] == link_row["url_tags"],
                            f"{ad_label}.url_tags does not match serialized url_tags for '{link_id}'")
                for rev_key in ("approved_copy_revision", "approved_assets_revision"):
                    if rev_key in ad_spec and ad_spec[rev_key]:
                        text(ad_spec[rev_key], f"{ad_label}.{rev_key}")
                summary.append({
                    "platform": "meta-ads",
                    "platform_campaign": campaign_slug,
                    "adset": adset_slug,
                    "ad": ad_slug,
                    "link_id": link_id,
                    "objective": campaign_spec["objective"],
                    "optimization_goal": adset_spec["optimization_goal"],
                    "format": ad_spec["format"]
                })
    for row in plan_result["links"]:
        if row["platform"] == "meta-ads":
            require(row["link_id"] in matched_links,
                    f"Meta link '{row['link_id']}' is missing its meta-ads/campaigns/{row['platform_campaign']}/adsets/{row['adset']}/ads/{row['ad']}/ad.json spec")
    return summary


def validate_social_platform_tree(platform, platform_root, plan_result):
    platform_root = Path(platform_root)
    posts_root = platform_root / "posts"
    require(posts_root.is_dir() and not posts_root.is_symlink(),
            f"{platform}/posts must be a real directory")
    post_dirs = sorted(p for p in posts_root.iterdir() if p.is_dir())
    require(bool(post_dirs), f"{platform}/posts must contain at least one post directory")
    links_by_id = {row["link_id"]: row for row in plan_result["links"]}
    matched_links = set()
    summary = []
    for post_dir in post_dirs:
        require(not post_dir.is_symlink(), f"Symlinked {platform} post directory: {post_dir}")
        post_slug = identifier(post_dir.name, f"{platform} post directory")
        post_label = f"{platform}/posts/{post_slug}"
        post_spec = read_json_file(post_dir / "post.json")
        object_fields(post_spec, {
            "schema_version", "platform", "post_slug", "name", "status", "format",
            "link_id", "destination_url", "utm", "url", "approved_copy_revision",
            "approved_assets_revision", "schedule", "account_handle", "remote_post_id", "notes"
        }, f"{post_label}/post.json")
        require(type(post_spec.get("schema_version")) is int and post_spec["schema_version"] == 1,
                f"{post_label}/post.json: schema_version must be 1")
        require(post_spec.get("platform") == platform,
                f"{post_label}/post.json: platform must be '{platform}'")
        require(post_spec.get("post_slug") == post_slug,
                f"{post_label}/post.json: post_slug must match directory name")
        text(post_spec.get("name"), f"{post_label}.name")
        require(post_spec.get("status") in POST_STATUSES, f"{post_label}: invalid status")
        require(post_spec.get("format") in POST_FORMATS, f"{post_label}: invalid format")
        link_id = post_spec.get("link_id")
        if link_id is not None:
            link_id = identifier(link_id, f"{post_label}.link_id")
            require(link_id in links_by_id, f"{post_label}.link_id '{link_id}' not found in campaign.json")
            require(link_id not in matched_links, f"Duplicate social post binding for link_id '{link_id}'")
            matched_links.add(link_id)
            link_row = links_by_id[link_id]
            require((link_row["platform"], link_row["post"]) == (platform, post_slug),
                    f"{post_label} hierarchy does not match campaign.json link '{link_id}'")
            require(post_spec.get("destination_url") == link_row["destination_url"],
                    f"{post_label}.destination_url does not match campaign.json link '{link_id}'")
            post_utm = utm_values(post_spec.get("utm"), f"{post_label}.utm")
            expected_utm = {k: link_row[k] for k in UTM_KEYS if link_row[k]}
            require(post_utm == expected_utm,
                    f"{post_label}.utm does not match resolved UTM values for '{link_id}'")
            if "url" in post_spec:
                require(post_spec["url"] == link_row["url"],
                        f"{post_label}.url does not match resolved url for '{link_id}'")
        else:
            require(not any(k in post_spec for k in ("destination_url", "utm", "url")),
                    f"{post_label}/post.json must specify link_id when destination_url, utm or url is set")
        for rev_key in ("approved_copy_revision", "approved_assets_revision"):
            if rev_key in post_spec and post_spec[rev_key]:
                text(post_spec[rev_key], f"{post_label}.{rev_key}")
        summary.append({
            "platform": platform,
            "post": post_slug,
            "link_id": link_id or "",
            "format": post_spec["format"],
            "status": post_spec["status"],
        })
    for row in plan_result["links"]:
        if row["platform"] == platform:
            require(row["link_id"] in matched_links,
                    f"Social link '{row['link_id']}' is missing its {platform}/posts/{row['post']}/post.json spec")
    return summary


def save_revision(output, source, result):
    output = Path(output).absolute()
    require(not any(p.is_symlink() for p in (output, *output.parents)), "Symlinked output paths are unsupported")
    # Never overwrite even an empty or incomplete prior revision.
    require(not output.exists(), "Output already exists; choose the next unused revision directory")
    csv_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(csv_buffer, fieldnames=COLUMNS)
    writer.writeheader()
    writer.writerows(result["links"])
    lines = [f"# UTM plan: {result['campaign_id']}", "",
             f"Input SHA-256: `{hashlib.sha256(source).hexdigest()}`", "",
             "Local URL validation passed. Publication, redirects and analytics receipt are not verified.", ""]
    for row in result["links"]:
        # JSON strings keep arbitrary copy out of Markdown links/HTML.
        lines.extend([f"## {row['link_id']}", "", f"Status: {row['status']}", "", "```json",
                      json.dumps({key: row[key] for key in COLUMNS if row[key]}, indent=2, ensure_ascii=False), "```", ""])
    if result["warnings"]:
        lines.extend(["## Warnings", "", *[f"- {warning}" for warning in result["warnings"]], ""])
    output.mkdir(parents=True, exist_ok=False)
    for name, data in (("campaign.json", source), ("utm-links.csv", csv_buffer.getvalue().encode("utf-8")),
                       ("UTM_PLAN.md", "\n".join(lines).encode("utf-8"))):
        with (output / name).open("xb") as target:
            target.write(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--out", type=Path, help="New export revision directory")
    parser.add_argument("--meta-ads-dir", "--meta-dir", dest="meta_ads_dir", type=Path,
                        help="Optional meta-ads/ directory to validate against campaign.json")
    parser.add_argument("--dry-run", action="store_true", help="Preview validated links without writes or network")
    args = parser.parse_args()
    if not args.dry_run and args.out is None:
        parser.error("--out is required unless --dry-run is used")
    try:
        source = args.plan.read_bytes()
        result = build_plan(json.loads(source.decode("utf-8"), object_pairs_hook=unique_keys))
        meta_dir = args.meta_ads_dir if args.meta_ads_dir is not None else (args.plan.parent / "meta-ads")
        if args.meta_ads_dir is not None or (meta_dir / "campaigns").exists():
            result["meta_ads"] = validate_meta_tree(meta_dir, result)
        social_posts = []
        for social_platform in SOCIAL_PLATFORMS:
            social_root = args.plan.parent / social_platform
            if (social_root / "posts").exists():
                social_posts.extend(validate_social_platform_tree(social_platform, social_root, result))
        if social_posts:
            result["social_posts"] = social_posts
        if args.dry_run:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            save_revision(args.out, source, result)
            print(f"Saved {len(result['links'])} links in {args.out}")
            for warning in result["warnings"]:
                print(f"Warning: {warning}")
    except (ValueError, OSError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    main()
