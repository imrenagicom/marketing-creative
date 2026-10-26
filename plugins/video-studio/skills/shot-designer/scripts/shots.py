#!/usr/bin/env python3
"""Lint a Video Studio shot list and time it to the narration's word timestamps (stdlib only)."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "studio-producer/scripts"))
from craft import vague_words  # noqa: E402
from studio import (ContractError, load, require, validate_lock, validate_project,  # noqa: E402
                    validate_script, validate_shots, validate_words, write)

LEAD = 0.15          # cut slightly before the first word so the picture is there when it is said
END_HOLD = 0.8       # default hold after the last word for an end card to land
MAX_STATIC = 7.0     # longer than this without a visible change feels stalled
MIN_READ = 0.8       # shorter than this is hard to read
CAMERA_FIELDS = ("framing", "movement", "action", "light_source", "sound")
DIRECTIONS = {"left", "right", "in", "out", "up", "down", "toward", "towards", "away", "orbit", "push", "pull",
              "pan", "tilt", "track", "tracking", "dolly", "crane", "follow", "arc", "static", "locked-off",
              "kiri", "kanan", "maju", "mundur", "naik", "turun", "diam"}
MODE_FIELDS = {"title": ("title",), "stat": ("value", "label"), "end-card": ("title",), "image": ("asset",),
               "ui-card": ("title", "rows")}


def inputs(root):
    project, lock, script = load(root, "project"), load(root, "lock"), load(root, "script")
    validate_project(project)
    validate_lock(lock)
    validate_script(script, project, lock)
    words = load(root, "words", required=False)
    if words is not None:
        validate_words(words, script)
    shots = load(root, "shots")
    validate_shots(shots, script, lock, words)
    return script, words, shots


def changes(shot):
    """How many visible changes a shot schedules (new keyword, list item, card)."""
    visual = shot.get("visual") or {}
    # Each line brings its own kinetic keywords unless keywords are switched off.
    spoken = 0 if visual.get("keywords") is False else len(shot.get("lines", []))
    return max(1, len(visual.get("items", [])), spoken)


def lint(root):
    script, words, shots = inputs(root)
    errors, warnings = [], []
    order = [line["id"] for line in script["lines"]]
    assigned = [line for shot in shots["shots"] for line in shot["lines"]]
    missing = [line for line in order if line not in assigned]
    if missing:
        errors.append(f"Lines with no picture: {missing}")
    if assigned != sorted(assigned, key=order.index):
        errors.append("Shots play lines out of script order")
    language = script["language"]
    previous_mode, run = None, 0
    for index, shot in enumerate(shots["shots"]):
        label = shot["id"]
        if not shot.get("lines") and index != len(shots["shots"]) - 1:
            errors.append(f"{label} has no lines; only the final shot may be a silent hold")
        if not (shot.get("motivation") or "").strip():
            errors.append(f"{label} needs a motivation: what the narration needs shown at this moment")
        prose = " ".join(str(shot.get(key, "")) for key in ("motivation", *CAMERA_FIELDS))
        prose += " " + json.dumps(shot.get("visual", {}), ensure_ascii=False)
        found = vague_words(prose)
        if found:
            warnings.append(f"{label} uses vague words {found}; describe framing, movement or motion concretely")
        if shot["kind"] == "camera":
            for field in CAMERA_FIELDS:
                if not (shot.get(field) or "").strip():
                    errors.append(f"{label} camera shot needs {field}")
            movement = (shot.get("movement") or "").casefold().replace(",", " ").split()
            if movement and not DIRECTIONS.intersection(movement):
                warnings.append(f"{label} movement has no direction; say which way the camera moves or that it is static")
        else:
            visual = shot.get("visual") or {}
            for field in MODE_FIELDS.get(visual.get("mode"), ()):
                if not visual.get(field):
                    errors.append(f"{label} {visual.get('mode')} visual needs {field}")
            if visual.get("mode") == "steps":
                items = visual.get("items") or []
                if not items:
                    errors.append(f"{label} steps visual needs items")
                for item in items:
                    if item.get("line") not in shot["lines"]:
                        errors.append(f"{label} step {item.get('text')!r} must reveal on one of the shot's own lines")
            if visual.get("mode") == "image" and visual.get("asset") and not (Path(root) / visual["asset"]).is_file():
                errors.append(f"{label} image asset {visual['asset']} does not exist in the project")
            mode = visual.get("mode")
            run = run + 1 if mode == previous_mode else 1
            previous_mode = mode
            if run == 4:
                warnings.append(f"Four {mode} shots in a row ending at {label}; vary the layout")
        if "start" in shot:
            length = shot["end"] - shot["start"]
            if length < MIN_READ:
                warnings.append(f"{label} lasts {length:.2f}s; too short to read")
            if length / changes(shot) > MAX_STATIC:
                warnings.append(f"{label} holds {length:.1f}s with {changes(shot)} visible change(s); add a change every 2-5 s")
    if words is None:
        warnings.append("No narration timings yet; run voice-director, then `shots.py time`")
    elif "start" not in shots["shots"][0]:
        warnings.append("Shots are not timed; run `shots.py time`")
    return {"errors": errors, "warnings": warnings}


def time(root, end_hold=END_HOLD):
    script, words, shots = inputs(root)
    require(words is not None, "Time shots after voice/words.json exists")
    first_word = {}
    for word in words["words"]:
        first_word.setdefault(word["line"], word["start"])
    items = shots["shots"]
    starts = []
    for index, shot in enumerate(items):
        if index == 0:
            starts.append(0.0)
        elif shot["lines"]:
            starts.append(max(starts[-1] + 0.1, round(first_word[shot["lines"][0]] - LEAD, 3)))
        else:
            starts.append(round(words["duration"], 3))
    # The last shot holds past the final word so an end card or payoff can land.
    total = round(words["duration"] + float(items[-1].get("hold", end_hold)), 3)
    for index, shot in enumerate(items):
        shot["start"] = starts[index]
        shot["end"] = starts[index + 1] if index + 1 < len(items) else total
    shots["timed_against"] = {"take": words.get("take"), "duration": words["duration"]}
    validate_shots(shots, script, load(root, "lock"), words)
    write(root, "shots", shots)
    return {"shots": [{"id": s["id"], "start": s["start"], "end": s["end"]} for s in items], "duration": total}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("lint", "time"):
        command = sub.add_parser(name)
        command.add_argument("root")
    args = parser.parse_args(argv)
    try:
        if args.command == "lint":
            report = lint(args.root)
            print(json.dumps(report, indent=2, ensure_ascii=False))
            return 1 if report["errors"] else 0
        print(json.dumps(time(args.root), indent=2))
    except ContractError as error:
        print(f"shots: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
