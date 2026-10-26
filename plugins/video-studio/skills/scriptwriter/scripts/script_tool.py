#!/usr/bin/env python3
"""Estimate script timing per beat and flag common script problems (stdlib only)."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "studio-producer/scripts"))
from craft import planned_seconds, spoken, vague_words, word_count  # noqa: E402
from studio import ContractError, load, validate_lock, validate_project, validate_script  # noqa: E402

HOOK_SECONDS = 3.5
LONG_LINE_WORDS = 22


def estimate(root):
    project, lock, script = load(root, "project"), load(root, "lock"), load(root, "script")
    validate_project(project)
    validate_lock(lock)
    validate_script(script, project, lock)
    language = script["language"]
    beats = {beat["id"]: {"target": beat.get("seconds"), "planned": 0.0, "lines": []} for beat in lock["beats"]}
    warnings = []
    for line in script["lines"]:
        seconds = planned_seconds(line["text"], language)
        beats[line["beat"]]["planned"] += seconds
        beats[line["beat"]]["lines"].append(line["id"])
        if word_count(line["text"]) > LONG_LINE_WORDS:
            warnings.append(f"{line['id']} is long ({word_count(line['text'])} words); split it so visuals can follow")
        if not line.get("keywords"):
            warnings.append(f"{line['id']} has no on-screen keyword")
        found = vague_words(spoken(line["text"]), (language,))
        if found:
            warnings.append(f"{line['id']} uses vague words {found}")
    order = [beat["id"] for beat in lock["beats"]]
    unused = [beat for beat in order if not beats[beat]["lines"]]
    if unused:
        warnings.append(f"Beats without lines: {unused}")
    used = [line["beat"] for line in script["lines"]]
    if used != sorted(used, key=order.index):
        warnings.append("Lines are not in beat order")
    first = script["lines"][0]
    if planned_seconds(first["text"], language) > HOOK_SECONDS:
        warnings.append(f"The hook line {first['id']} runs past {HOOK_SECONDS}s at planning pace; tighten it")
    for beat_id, beat in beats.items():
        beat["planned"] = round(beat["planned"], 1)
        if beat["target"] and abs(beat["planned"] - beat["target"]) > max(1.5, 0.35 * beat["target"]):
            warnings.append(f"Beat {beat_id} plans {beat['planned']}s against {beat['target']}s in the direction lock")
    total = round(sum(beat["planned"] for beat in beats.values()), 1)
    return {"language": language, "planned_seconds": total, "beats": beats, "warnings": warnings,
            "note": "Planning pace only; voice-director's word timestamps replace these numbers."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["estimate"])
    parser.add_argument("root")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(estimate(args.root), indent=2, ensure_ascii=False))
    except ContractError as error:
        print(f"script: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
