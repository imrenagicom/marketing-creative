#!/usr/bin/env python3
"""Check director drafts and turn the user's chosen option into the direction lock (stdlib only)."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "studio-producer/scripts"))
from craft import vague_words  # noqa: E402
from studio import ContractError, load, now, require, validate_lock, write  # noqa: E402

FIELDS = ("title", "logline", "hook", "structure", "beats", "characters", "visual_plan", "audio_policy")


def options_path(root):
    return Path(root) / "direction/options.json"


def check_options(document):
    """Return (errors, warnings) for a set of direction options."""
    errors, warnings = [], []
    if document.get("schema") != "video-studio/direction-options@1":
        return ["options.json must declare schema video-studio/direction-options@1"], warnings
    options = document.get("options") or []
    if not 2 <= len(options) <= 3:
        errors.append("Draft 2 or 3 options so the user has a real choice")
    ids = [option.get("id") for option in options]
    if len(ids) != len(set(ids)):
        errors.append("Option ids must be unique")
    for option in options:
        label = f"Option {option.get('id')}"
        for field in FIELDS:
            if not option.get(field):
                errors.append(f"{label} is missing {field}")
        for character in option.get("characters") or []:
            if not character.get("acting_baseline"):
                errors.append(f"{label} character {character.get('id')} needs an acting_baseline")
        if not (option.get("hook") or {}).get("opening"):
            errors.append(f"{label} hook needs an opening (what happens in the first 2 seconds)")
        prose = json.dumps({k: option.get(k) for k in ("logline", "hook", "visual_plan", "beats", "characters")},
                           ensure_ascii=False)
        vague = vague_words(prose)
        if vague:
            warnings.append(f"{label} leans on vague words {vague}; replace them with concrete instructions")
        if not option.get("risks"):
            warnings.append(f"{label} names no risks; say honestly where it could fail")
    patterns = [(option.get("hook") or {}).get("pattern") for option in options]
    structures = [option.get("structure") for option in options]
    if len(options) > 1 and len(set(patterns)) == 1 and len(set(structures)) == 1:
        errors.append("Options share the same hook pattern and structure; make them genuinely different")
    return errors, warnings


def lock(root, option_id):
    """Write direction/lock.json from an option the user approved (after their edits)."""
    document = json.loads(options_path(root).read_text(encoding="utf-8"))
    errors, _ = check_options(document)
    require(not errors, "; ".join(errors))
    option = next((item for item in document["options"] if item.get("id") == option_id), None)
    require(option is not None, f"No option {option_id!r} in direction/options.json")
    previous = load(root, "lock", required=False)
    result = {
        "schema": "video-studio/direction-lock@1",
        "version": (previous or {}).get("version", 0) + 1,
        "source_option": option_id,
        "logline": option["logline"],
        "hook": option["hook"],
        "structure": option["structure"],
        "beats": option["beats"],
        "characters": option["characters"],
        "visual_plan": option["visual_plan"],
        "audio_policy": option["audio_policy"],
        "approved": {"by": "user", "at": now()},
    }
    validate_lock(result)
    write(root, "lock", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="Check direction/options.json before showing it")
    check.add_argument("root")
    choose = sub.add_parser("lock", help="Record the option the user approved")
    choose.add_argument("root")
    choose.add_argument("--option", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            errors, warnings = check_options(json.loads(options_path(args.root).read_text(encoding="utf-8")))
            print(json.dumps({"errors": errors, "warnings": warnings}, indent=2, ensure_ascii=False))
            return 1 if errors else 0
        result = lock(args.root, args.option)
        print(json.dumps({"locked": args.option, "version": result["version"]}))
    except (ContractError, FileNotFoundError, json.JSONDecodeError) as error:
        print(f"direction: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
