#!/usr/bin/env python3
"""Lint a Video Studio shot list and time it to the narration's word timestamps (stdlib only)."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "studio-producer/scripts"))
from craft import vague_words  # noqa: E402
from studio import (ContractError, load, require, validate_bible, validate_lock,  # noqa: E402
                    validate_project, validate_script, validate_shots, validate_words, write)

LEAD = 0.15          # cut slightly before the first word so the picture is there when it is said
END_HOLD = 0.8       # default hold after the last word for an end card to land
MAX_STATIC = 7.0     # longer than this without a visible change feels stalled
MIN_READ = 0.8       # shorter than this is hard to read
CAMERA_FIELDS = ("framing", "movement", "action", "light_source", "sound")
DIRECTIONS = {"left", "right", "in", "out", "up", "down", "toward", "towards", "away", "orbit", "push", "pull",
              "pan", "tilt", "track", "tracking", "dolly", "crane", "follow", "arc", "static", "locked-off",
              "kiri", "kanan", "maju", "mundur", "naik", "turun", "diam"}
MAX_TAKE_SECONDS = 15.0   # replace per project with the chosen model's limit (models_explore)
OPPOSITE = {("left-to-right", "right-to-left"), ("right-to-left", "left-to-right"),
            ("toward-camera", "away-from-camera"), ("away-from-camera", "toward-camera")}
MODE_FIELDS = {"title": ("title",), "stat": ("value", "label"), "end-card": ("title",), "image": ("asset",),
               "ui-card": ("title", "rows")}


def inputs(root):
    project, lock = load(root, "project"), load(root, "lock")
    validate_project(project)
    validate_lock(lock)
    script = load(root, "script", required=project["recipe"] == "explainer")
    if script is not None:
        validate_script(script, project, lock)
    words = load(root, "words", required=False)
    if words is not None:
        validate_words(words, script)
    bible = load(root, "bible", required=False)
    if bible is not None:
        validate_bible(bible, lock)
    shots = load(root, "shots")
    validate_shots(shots, script, lock, words, bible)
    return project, script, words, shots, bible


def shot_length(shot):
    return shot["end"] - shot["start"] if "start" in shot else shot.get("duration", 0)


def changes(shot):
    """How many visible changes a shot schedules (new keyword, list item, card)."""
    visual = shot.get("visual") or {}
    # Each line brings its own kinetic keywords unless keywords are switched off.
    spoken = 0 if visual.get("keywords") is False else len(shot.get("lines", []))
    return max(1, len(visual.get("items", [])), spoken)


def lint(root):
    project, script, words, shots, bible = inputs(root)
    errors, warnings = [], []
    footage = project["recipe"] != "explainer"
    if script is not None:
        order = [line["id"] for line in script["lines"]]
        assigned = [line for shot in shots["shots"] for line in shot["lines"]]
        missing = [line for line in order if line not in assigned]
        if missing:
            errors.append(f"Lines with no picture: {missing}")
        if assigned != sorted(assigned, key=order.index):
            errors.append("Shots play lines out of script order")
    previous_mode, run, previous_camera = None, 0, None
    for index, shot in enumerate(shots["shots"]):
        label = shot["id"]
        if not shot.get("lines") and index != len(shots["shots"]) - 1 and (words is not None or not footage):
            errors.append(f"{label} has no lines; only the final shot may be a silent hold")
        if footage and words is None and not shot.get("duration"):
            errors.append(f"{label} needs a duration (seconds); without narration, durations time the cut")
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
            if not shot.get("refs"):
                warnings.append(f"{label} names no bible references; list the characters, environment and props it shows")
            if bible is not None:
                roles = {ref["id"]: ref["role"] for ref in bible["references"]}
                if not any(roles.get(ref) == "environment" for ref in shot.get("refs", [])):
                    warnings.append(f"{label} has no environment reference; the model will invent the location and its light")
            if previous_camera and previous_camera.get("beat") == shot["beat"] and \
                    (previous_camera.get("screen_direction"), shot.get("screen_direction")) in OPPOSITE:
                warnings.append(f"Screen direction flips between {previous_camera['id']} and {label}; "
                                "bridge with a neutral shot or motivate the reversal")
            previous_camera = shot
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
    limit = float(shots.get("max_take_seconds", MAX_TAKE_SECONDS))
    totals = {}
    for shot in shots["shots"]:
        if shot.get("take"):
            totals[shot["take"]] = totals.get(shot["take"], 0) + shot_length(shot)
    for take, total in totals.items():
        if total > limit + 1e-6:
            errors.append(f"Take {take} runs {total:.1f}s, over the model limit of {limit:g}s; split it or choose another model")
    if words is None and not footage:
        warnings.append("No narration timings yet; run voice-director, then `shots.py time`")
    elif "start" not in shots["shots"][0]:
        warnings.append("Shots are not timed; run `shots.py time`")
    return {"errors": errors, "warnings": warnings}


def time(root, end_hold=END_HOLD):
    project, script, words, shots, bible = inputs(root)
    items = shots["shots"]
    if words is None:
        require(project["recipe"] != "explainer", "Time shots after voice/words.json exists")
        require(all(shot.get("duration") for shot in items), "Without narration every shot needs a duration")
        clock = 0.0
        for shot in items:
            shot["start"], clock = round(clock, 3), round(clock + float(shot["duration"]), 3)
            shot["end"] = clock
        shots["timed_against"] = {"take": None, "duration": None, "source": "shot durations"}
        validate_shots(shots, script, load(root, "lock"), None, bible)
        write(root, "shots", shots)
        return {"shots": [{"id": s["id"], "start": s["start"], "end": s["end"]} for s in items], "duration": clock}
    first_word = {}
    for word in words["words"]:
        first_word.setdefault(word["line"], word["start"])
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
    validate_shots(shots, script, load(root, "lock"), words, bible)
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
