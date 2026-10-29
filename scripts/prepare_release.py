#!/usr/bin/env python3
"""Synchronize release metadata and build the allowlisted plugin archive."""
import argparse
import json
from pathlib import Path
import re

from build_plugin import build

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILES = (
    "package.json",
    "package-lock.json",
    "plugins/marketing-creative/.codex-plugin/plugin.json",
    "plugins/marketing-creative/.claude-plugin/plugin.json",
    "plugins/marketing-creative/plugin.json",
    "plugins/marketing-images/.codex-plugin/plugin.json",
    "plugins/marketing-images/.claude-plugin/plugin.json",
    "plugins/marketing-images/plugin.json",
    "plugins/marketing-performance/.codex-plugin/plugin.json",
    "plugins/marketing-performance/.claude-plugin/plugin.json",
    "plugins/marketing-performance/plugin.json",
    "plugins/video-studio/.codex-plugin/plugin.json",
    "plugins/video-studio/.claude-plugin/plugin.json",
    "plugins/video-studio/plugin.json",
)


def update_versions(root, version):
    if not re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version):
        raise ValueError("Expected a stable semantic version without a v prefix")
    # Read and check every file before writing any release metadata.
    documents = {name: json.loads((root / name).read_text(encoding="utf-8"))
                 for name in VERSION_FILES}
    lock = documents["package-lock.json"]
    if "" not in lock.get("packages", {}):
        raise ValueError("Expected an npm lockfile with root package metadata")
    for name, document in documents.items():
        document["version"] = version
        if name == "package-lock.json":
            document["packages"][""]["version"] = version
    for name, document in documents.items():
        (root / name).write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if Path(args.output).resolve().is_relative_to(ROOT):
        parser.error("Release archives must be outside the repository")
    if Path(args.output).name in {"marketing-images-plugin.zip", "marketing-performance-plugin.zip", "video-studio-plugin.zip"}:
        parser.error("The creative, images, performance and video studio archive paths must differ")
    update_versions(ROOT, args.version)
    build(args.output)
    build(Path(args.output).with_name("marketing-images-plugin.zip"), "marketing-images")
    build(Path(args.output).with_name("marketing-performance-plugin.zip"), "marketing-performance")
    build(Path(args.output).with_name("video-studio-plugin.zip"), "video-studio")
