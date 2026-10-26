#!/usr/bin/env python3
"""Video Studio project contracts: create, inspect and validate a project (stdlib only).

Other Video Studio helpers import this module for loading, validation and
versioned writes, so every skill reads the same contract.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
import re
import shutil
import sys

LANGUAGES = {"en", "id"}
REGISTERS = {"id": {"casual", "friendly", "formal"}, "en": {"casual", "conversational", "formal"}}
RECIPES = {"explainer"}
FORMATS = {
    "16x9": (1920, 1080),
    "9x16": (1080, 1920),
    "4x5": (1080, 1350),
    "1x1": (1080, 1080),
}
VISUAL_MODES = {"title", "kinetic", "steps", "ui-card", "stat", "image", "end-card"}
SHOT_KINDS = {"graphic", "camera"}
TRANSITIONS = {"cut", "wipe", "fade", "push"}
FILES = {
    "project": "project.json",
    "lock": "direction/lock.json",
    "script": "script/script.json",
    "voice_config": "voice/voice-config.json",
    "words": "voice/words.json",
    "shots": "shots/shots.json",
    "style": "style.json",
    "ledger": "ledger.json",
}
STAGES = (
    ("direction", "lock", "director"),
    ("script", "script", "scriptwriter"),
    ("voice", "words", "voice-director"),
    ("shots", "shots", "shot-designer"),
)
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


class ContractError(ValueError):
    """A project file breaks the Video Studio contract."""


def require(condition, message):
    if not condition:
        raise ContractError(message)


def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def path_of(root, key):
    return Path(root) / FILES[key]


def load(root, key, required=True):
    path = path_of(root, key)
    if not path.is_file():
        require(not required, f"Missing {FILES[key]}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ContractError(f"{FILES[key]} is not valid JSON: {error}") from error


def write(root, key, document):
    """Write a contract atomically, keeping the previous version in .history/."""
    path = path_of(root, key)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        history = Path(root) / ".history"
        history.mkdir(exist_ok=True)
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        shutil.copy2(path, history / f"{FILES[key].replace('/', '__')}.{stamp}")
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(path)
    return path


def text(value):
    return isinstance(value, str) and value.strip() != ""


def schema(document, name):
    require(isinstance(document, dict), f"{name} must be a JSON object")
    require(document.get("schema") == f"video-studio/{name}@1", f"{name} must declare schema video-studio/{name}@1")


def unique_ids(items, label):
    ids = [item.get("id") for item in items]
    for item_id in ids:
        require(isinstance(item_id, str) and ID.match(item_id), f"Invalid {label} id: {item_id!r}")
    require(len(ids) == len(set(ids)), f"Duplicate {label} ids")
    return ids


def validate_project(project):
    schema(project, "project")
    require(isinstance(project.get("id"), str) and ID.match(project["id"]), "project.id must be a slug")
    require(text(project.get("title")), "project.title is required")
    require(project.get("recipe") in RECIPES, f"project.recipe must be one of {sorted(RECIPES)}")
    language = project.get("language")
    require(language is None or language in LANGUAGES, "project.language must be en, id or null (not yet chosen)")
    formats = project.get("formats")
    require(isinstance(formats, list) and formats, "project.formats needs at least one canvas")
    seen = set()
    for item in formats:
        require(item.get("id") in FORMATS, f"Unknown format {item.get('id')!r}")
        require(item["id"] not in seen, f"Duplicate format {item['id']}")
        seen.add(item["id"])
        require(isinstance(item.get("width"), int) and isinstance(item.get("height"), int)
                and item["width"] > 0 and item["height"] > 0, f"Format {item['id']} needs integer width/height")
    require(project.get("fps") in {24, 25, 30, 60}, "project.fps must be 24, 25, 30 or 60")


def validate_lock(lock):
    schema(lock, "direction-lock")
    require(isinstance(lock.get("version"), int) and lock["version"] >= 1, "direction lock needs a version")
    require(text(lock.get("logline")), "direction lock needs a logline")
    hook = lock.get("hook") or {}
    require(text(hook.get("pattern")) and text(hook.get("opening")), "direction lock needs hook.pattern and hook.opening")
    beats = lock.get("beats")
    require(isinstance(beats, list) and beats, "direction lock needs beats")
    unique_ids(beats, "beat")
    for beat in beats:
        require(text(beat.get("purpose")) and text(beat.get("summary")), f"Beat {beat['id']} needs purpose and summary")
    characters = lock.get("characters")
    require(isinstance(characters, list) and characters, "direction lock needs at least one character or narrator")
    unique_ids(characters, "character")
    for character in characters:
        require(text(character.get("acting_baseline")), f"Character {character['id']} needs an acting_baseline")
    approved = lock.get("approved") or {}
    require(approved.get("by") == "user" and text(approved.get("at")),
            "direction lock is not approved by the user (approved.by/at)")


def validate_script(script, project, lock):
    schema(script, "script")
    language = script.get("language")
    require(language in LANGUAGES, "script.language must be en or id")
    require(project.get("language") == language, "script.language differs from project.language")
    register = script.get("register")
    require(register in REGISTERS[language], f"script.register must be one of {sorted(REGISTERS[language])}")
    lines = script.get("lines")
    require(isinstance(lines, list) and lines, "script needs lines")
    unique_ids(lines, "line")
    beats = {beat["id"] for beat in lock["beats"]}
    speakers = {character["id"] for character in lock["characters"]}
    for line in lines:
        require(line.get("beat") in beats, f"Line {line['id']} references unknown beat {line.get('beat')!r}")
        require(line.get("speaker") in speakers, f"Line {line['id']} references unknown speaker {line.get('speaker')!r}")
        require(text(line.get("text")), f"Line {line['id']} needs text")
        for keyword in line.get("keywords", []):
            require(keyword.casefold() in line["text"].casefold(), f"Line {line['id']} keyword {keyword!r} is not in its text")


def validate_words(words, script):
    schema(words, "words")
    require(text(words.get("audio")), "words.audio is required")
    duration = words.get("duration")
    require(isinstance(duration, (int, float)) and duration > 0, "words.duration must be positive")
    require(words.get("language") == script["language"], "words.language differs from script.language")
    items = words.get("words")
    require(isinstance(items, list) and items, "words needs word timings")
    lines = {line["id"] for line in script["lines"]}
    previous = 0.0
    for index, word in enumerate(items):
        start, end = word.get("start"), word.get("end")
        require(text(word.get("text")), f"Word {index} needs text")
        require(isinstance(start, (int, float)) and isinstance(end, (int, float)) and 0 <= start <= end <= duration + 0.05,
                f"Word {index} has invalid timing")
        require(start >= previous - 0.02, f"Word {index} starts before the previous word")
        require(word.get("line") in lines, f"Word {index} references unknown line {word.get('line')!r}")
        previous = start


def validate_shots(shots, script, lock, words=None):
    schema(shots, "shots")
    items = shots.get("shots")
    require(isinstance(items, list) and items, "shots needs at least one shot")
    unique_ids(items, "shot")
    beats = {beat["id"] for beat in lock["beats"]}
    lines = {line["id"] for line in script["lines"]}
    covered = []
    for shot in items:
        require(shot.get("kind") in SHOT_KINDS, f"Shot {shot['id']} kind must be graphic or camera")
        require(shot.get("beat") in beats, f"Shot {shot['id']} references unknown beat")
        require(isinstance(shot.get("lines"), list), f"Shot {shot['id']} needs a lines list")
        for line in shot["lines"]:
            require(line in lines, f"Shot {shot['id']} references unknown line {line!r}")
        covered.extend(shot["lines"])
        require(shot.get("transition", "cut") in TRANSITIONS, f"Shot {shot['id']} has unknown transition")
        if shot["kind"] == "graphic":
            require((shot.get("visual") or {}).get("mode") in VISUAL_MODES,
                    f"Shot {shot['id']} visual.mode must be one of {sorted(VISUAL_MODES)}")
        if "start" in shot or "end" in shot:
            require(isinstance(shot.get("start"), (int, float)) and isinstance(shot.get("end"), (int, float))
                    and shot["start"] < shot["end"], f"Shot {shot['id']} has invalid start/end")
    require(len(covered) == len(set(covered)), "A script line is assigned to more than one shot")
    timed = [shot for shot in items if "start" in shot]
    if timed:
        require(len(timed) == len(items), "Either every shot is timed or none are")
        for before, after in zip(items, items[1:]):
            require(abs(before["end"] - after["start"]) < 1e-6, f"Gap or overlap between {before['id']} and {after['id']}")
        if words:
            require(items[-1]["end"] >= words["duration"] - 0.05, "Shots end before the narration does")


def validate(root):
    """Validate every contract present; return a status report."""
    root = Path(root)
    report = {"project": str(root), "valid": [], "missing": [], "next": None}
    project = load(root, "project")
    validate_project(project)
    report["valid"].append(FILES["project"])
    lock = load(root, "lock", required=False)
    script = load(root, "script", required=False)
    words = load(root, "words", required=False)
    shots = load(root, "shots", required=False)
    if lock is not None:
        validate_lock(lock)
        report["valid"].append(FILES["lock"])
    if script is not None:
        require(lock is not None, "script exists without an approved direction lock")
        validate_script(script, project, lock)
        report["valid"].append(FILES["script"])
    if words is not None:
        require(script is not None, "voice/words.json exists without a script")
        validate_words(words, script)
        report["valid"].append(FILES["words"])
    if shots is not None:
        require(script is not None and lock is not None, "shots exist without script and direction lock")
        validate_shots(shots, script, lock, words)
        report["valid"].append(FILES["shots"])
    present = {"lock": lock, "script": script, "words": words, "shots": shots}
    for stage, key, skill in STAGES:
        if present[key] is None:
            report["missing"].append(FILES[key])
            if report["next"] is None:
                report["next"] = {"stage": stage, "skill": skill}
    if project.get("language") is None and report["next"] and report["next"]["stage"] in {"script", "voice"}:
        report["next"]["blocked"] = "Choose the video language (en or id) before scripting"
    if report["next"] is None:
        report["next"] = {"stage": "compose", "skill": "motion-designer"}
    return report


def init(root, title, recipe, language, formats, fps):
    root = Path(root)
    require(not (root / FILES["project"]).exists(), f"{root / FILES['project']} already exists; use a new versioned directory")
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:48] or "video"
    project = {
        "schema": "video-studio/project@1",
        "id": slug,
        "title": title,
        "recipe": recipe,
        "language": language,
        "formats": [{"id": f, "width": FORMATS[f][0], "height": FORMATS[f][1]} for f in formats],
        "fps": fps,
        "created": now(),
    }
    validate_project(project)
    root.mkdir(parents=True, exist_ok=True)
    write(root, "project", project)
    write(root, "ledger", {"schema": "video-studio/ledger@1", "caps": {}, "entries": []})
    return project


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    make = sub.add_parser("init", help="Create a project directory")
    make.add_argument("root")
    make.add_argument("--title", required=True)
    make.add_argument("--recipe", default="explainer", choices=sorted(RECIPES))
    make.add_argument("--language", choices=sorted(LANGUAGES), help="Leave unset until the user chooses")
    make.add_argument("--formats", default="9x16", help="Comma-separated: " + ",".join(FORMATS))
    make.add_argument("--fps", type=int, default=30)
    for name in ("status", "validate"):
        command = sub.add_parser(name)
        command.add_argument("root")
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            formats = [item.strip() for item in args.formats.split(",") if item.strip()]
            project = init(args.root, args.title, args.recipe, args.language, formats, args.fps)
            print(json.dumps({"created": str(Path(args.root) / FILES["project"]), "id": project["id"]}))
        else:
            report = validate(args.root)
            print(json.dumps(report, indent=2))
    except ContractError as error:
        print(f"studio: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
