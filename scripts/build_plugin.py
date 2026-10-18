#!/usr/bin/env python3
"""Build a deterministic skill/tool/resource ZIP for Codex, Claude Code, and Antigravity."""
import argparse
from pathlib import Path
import zipfile

from validate_package import ROOT, PLUGINS, validate


def build(output, plugin_name="marketing-creative"):
    files = validate(plugin_name)
    plugin = ROOT / "plugins" / plugin_name
    output = Path(output).resolve()
    if output.is_relative_to(ROOT):
        raise ValueError("Write the release outside the repository")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            entry = zipfile.ZipInfo(path.relative_to(plugin).as_posix(), (2020, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, path.read_bytes())
    print(f"Built {output} with {len(files)} explicitly allowed plugin files")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="Destination ZIP (for example /tmp/plugin.zip)")
    parser.add_argument("--plugin", choices=PLUGINS, default="marketing-creative")
    args = parser.parse_args()
    build(args.output, args.plugin)
