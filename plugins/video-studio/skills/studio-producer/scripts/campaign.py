#!/usr/bin/env python3
"""Tie a Video Studio project to its marketing campaign workspace and hand approved deliveries to it (stdlib only).

The campaign workspace is campaign-manager's `<YYYY-MM-DD>-<campaign-name>/` directory
(marketing-performance plugin). A video serves one or more of its ads or posts;
the approved files go into that ad's or post's `assets/approved/vNNN/video/`,
never over an earlier revision. Publishing, ad.json/post.json pointers and alt
text stay with campaign-manager and marketing-copywriter.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

from studio import ContractError, load, now, require, validate_project, write


def campaign_root(root, project):
    campaign = project.get("campaign")
    require(campaign, "This project is not linked to a campaign; run `campaign.py link` first")
    folder = (Path(root) / campaign["dir"]).resolve()
    require(folder.is_dir(), f"Campaign directory {campaign['dir']} is missing")
    return folder, campaign


def link(root, campaign_dir, deliverables=()):
    """Record the campaign directory (relative to the project), its campaign_id and the ads/posts this video serves."""
    project = load(root, "project")
    folder = Path(campaign_dir).resolve()
    plan = folder / "campaign.json"
    require(plan.is_file(), f"{folder} has no campaign.json; set the campaign up with campaign-manager first")
    campaign_id = json.loads(plan.read_text(encoding="utf-8")).get("campaign_id")
    require(campaign_id, f"{plan} has no campaign_id")
    for deliverable in deliverables:
        require(not Path(deliverable).is_absolute() and ".." not in Path(deliverable).parts,
                f"{deliverable} must be relative to the campaign directory")
        require((folder / deliverable).is_dir(), f"No ad or post directory {deliverable} in the campaign; "
                                                 "create it with campaign-manager")
    existing = (project.get("campaign") or {}).get("deliverables", []) if (project.get("campaign") or {}).get("id") == campaign_id else []
    project["campaign"] = {"dir": os.path.relpath(folder, Path(root).resolve()), "id": campaign_id,
                           "deliverables": list(dict.fromkeys([*existing, *deliverables]))}
    validate_project(project)
    write(root, "project", project)
    return project["campaign"]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def handoff(root, deliverable, note, version=None):
    """Copy a QC-passed render's deliveries into <deliverable>/assets/approved/vNNN/video/ with assets.json."""
    root = Path(root)
    project = load(root, "project")
    folder, campaign = campaign_root(root, project)
    require(deliverable in campaign.get("deliverables", []), f"{deliverable} is not one of this video's campaign "
                                                              "deliverables; add it with `campaign.py link`")
    require(note and note.strip(), "Record how the user approved this delivery (--note)")
    report_path = root / "qc/report.json"
    require(report_path.is_file(), "No final QC report; run qc.py final on the render first")
    report = json.loads(report_path.read_text())
    version = version or report["version"]
    require(report["version"] == version, f"qc/report.json covers v{report['version']}, not v{version}; re-run QC")
    require(report["failed"] == 0, f"Final QC for v{version} has {report['failed']} failed checks")
    manifest = json.loads((root / f"renders/v{version}/manifest.json").read_text())
    delivered = manifest.get("delivery") or []
    require(delivered, f"renders/v{version} has no finished deliveries; run edit.py finish")
    approved = folder / deliverable / "assets/approved"
    revision = 1
    while (approved / f"v{revision:03d}").exists():
        revision += 1
    target = approved / f"v{revision:03d}"
    (target / "video").mkdir(parents=True)
    formats = {f["id"]: f for f in project["formats"]}
    assets = []
    for item in delivered:
        source = root / f"renders/v{version}" / item["file"]
        require(source.is_file(), f"Missing delivery {source}")
        name = f"{project['id']}-{item['canvas']}{source.suffix}"
        shutil.copy2(source, target / "video" / name)
        assets.append({"file": f"video/{name}", "canvas": item["canvas"], "width": formats[item["canvas"]]["width"],
                       "height": formats[item["canvas"]]["height"], "sha256": sha256(target / "video" / name)})
    record = {"campaign_id": campaign["id"], "creative": project["id"], "source": "video-studio",
              "project": os.path.relpath(root.resolve(), folder), "render": f"v{version}",
              "qc_report_sha256": sha256(report_path), "manual_checks_remaining": report.get("manual_checks_remaining", []),
              "approval_note": note.strip(), "recorded_at": now(), "assets": assets}
    (target / "assets.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    return {"approved": str((target).relative_to(folder)), "assets": [a["file"] for a in assets],
            "next": ["Write alt text for each video with marketing-copywriter (copy/drafts → copy/approved)",
                     "Point the ad.json/post.json approved_assets_revision at this revision with campaign-manager",
                     "Copy, do not regenerate, when another ad or post reuses this video"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    tie = sub.add_parser("link", help="Link the project to a campaign-manager campaign directory")
    tie.add_argument("root")
    tie.add_argument("--campaign", required=True, help="The <YYYY-MM-DD>-<campaign-name> directory")
    tie.add_argument("--deliverable", action="append", default=[],
                     help="Ad or post this video serves, relative to the campaign (repeatable), "
                          "e.g. meta-ads/campaigns/launch/adsets/broad/ads/demo-video")
    give = sub.add_parser("handoff", help="Copy a QC-passed, user-approved render into the deliverable's approved assets")
    give.add_argument("root")
    give.add_argument("--deliverable", required=True)
    give.add_argument("--note", required=True, help="How the user approved this delivery")
    give.add_argument("--render", type=int, help="Render version (default: the one in qc/report.json)")
    args = parser.parse_args(argv)
    try:
        if args.command == "link":
            print(json.dumps(link(args.root, args.campaign, args.deliverable), indent=2))
        else:
            print(json.dumps(handoff(args.root, args.deliverable, args.note, args.render), indent=2))
    except (ContractError, FileNotFoundError) as error:
        print(f"campaign: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
