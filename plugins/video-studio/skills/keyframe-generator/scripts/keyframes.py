#!/usr/bin/env python3
"""Plan, reserve and record start/end keyframes for camera shots under the Higgsfield image cap."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "studio-producer/scripts"))
import media  # noqa: E402
from prompting import ASPECT, environment, media_refs, refs_for, subject  # noqa: E402
from studio import (ContractError, load, require, validate_bible, validate_lock, validate_project,  # noqa: E402
                    validate_shots, write)

DEFAULT_MODEL = "nano_banana_pro"
FRAMES = ("start", "end")


def inputs(root):
    project, lock, bible, shots = load(root, "project"), load(root, "lock"), load(root, "bible"), load(root, "shots")
    validate_project(project)
    validate_lock(lock)
    validate_bible(bible, lock)
    validate_shots(shots, load(root, "script", required=False), lock, load(root, "words", required=False), bible)
    return project, lock, bible, shots


def prompt_for(shot, frame, bible, lock, model, canvas):
    refs = refs_for(shot, bible)
    env, lights = environment(refs)
    subjects = [subject(ref, model) for ref in refs if ref["role"] != "environment"]
    moment = "the opening moment" if frame == "start" else "the closing moment"
    parts = [f"{shot['framing'].capitalize()} of {', '.join(subjects) or 'the scene'}, at {moment} of this action: {shot['action']}."]
    if env:
        parts.append(f"Setting: {subject(env, model)} — {env['description']}")
    parts.append(f"Light: {shot['light_source']}" + (f"; scene sources: {', '.join(lights)}." if lights else "."))
    characters = {c["id"]: c for c in lock["characters"]}
    for ref in refs:
        if ref["role"] == "character" and ref.get("character") in characters:
            parts.append(f"Performance: {characters[ref['character']]['acting_baseline']}")
    parts.append(f"Look: {bible['capture']['look']}. Aspect ratio {ASPECT[canvas]}.")
    if bible.get("negatives"):
        parts.append("Avoid: " + "; ".join(bible["negatives"]) + ".")
    return " ".join(parts)


def plan(root, canvas, model=DEFAULT_MODEL, ends=False, only=None):
    project, lock, bible, shots = inputs(root)
    require(canvas in {f["id"] for f in project["formats"]}, f"{canvas} is not a project canvas")
    requests = []
    for shot in shots["shots"]:
        if shot["kind"] != "camera" or (only and shot["id"] not in only):
            continue
        for frame in FRAMES if ends else FRAMES[:1]:
            refs = refs_for(shot, bible)
            requests.append({"shot": shot["id"], "frame": frame, "canvas": canvas, "model": model,
                             "aspect_ratio": ASPECT[canvas], "prompt": prompt_for(shot, frame, bible, lock, model, canvas),
                             "medias": media_refs(refs, model)})
    folder = Path(root) / "keyframes"
    folder.mkdir(exist_ok=True)
    (folder / f"requests-{canvas}.json").write_text(json.dumps({"requests": requests}, indent=2, ensure_ascii=False) + "\n")
    return requests


def find_request(root, canvas, shot, frame):
    requests = json.loads((Path(root) / f"keyframes/requests-{canvas}.json").read_text(encoding="utf-8"))["requests"]
    request = next((r for r in requests if r["shot"] == shot and r["frame"] == frame), None)
    require(request is not None, f"No planned {frame} keyframe for {shot} on {canvas}; run `keyframes.py plan`")
    return request


def record(root, canvas, shot_id, frame, entry_id, source, job_id=None):
    _, _, _, shots = inputs(root)
    shot = next((s for s in shots["shots"] if s["id"] == shot_id), None)
    require(shot is not None, f"No shot {shot_id}")
    folder = Path(root) / "keyframes" / canvas
    name = media.next_name(folder, f"{shot_id}-{frame}", Path(source).suffix or ".png")
    destination = f"keyframes/{canvas}/{name}"
    media.complete(root, entry_id, source, destination, job_id)
    shot.setdefault("keyframes", {}).setdefault(canvas, {})[frame] = destination
    write(root, "shots", shots)
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    draft = sub.add_parser("plan", help="Write keyframe requests for camera shots")
    draft.add_argument("root")
    draft.add_argument("--canvas", required=True)
    draft.add_argument("--model", default=DEFAULT_MODEL)
    draft.add_argument("--ends", action="store_true", help="Also plan end frames (for start/end-frame video models)")
    draft.add_argument("--shot", action="append", help="Limit to shots (repeatable)")
    hold = sub.add_parser("reserve", help="Check the image cap and record one keyframe job before the MCP call")
    hold.add_argument("root")
    hold.add_argument("--canvas", required=True)
    hold.add_argument("--shot", required=True)
    hold.add_argument("--frame", choices=FRAMES, default="start")
    hold.add_argument("--estimate", required=True, type=float, help="Credits from get_cost")
    done = sub.add_parser("record", help="Store a returned keyframe")
    done.add_argument("root")
    done.add_argument("--canvas", required=True)
    done.add_argument("--shot", required=True)
    done.add_argument("--frame", choices=FRAMES, default="start")
    done.add_argument("--entry", required=True)
    done.add_argument("--file", required=True)
    done.add_argument("--job-id")
    lost = sub.add_parser("fail", help="Record a failed or uncertain keyframe job")
    lost.add_argument("root")
    lost.add_argument("--entry", required=True)
    lost.add_argument("--uncertain", action="store_true", help="Timeout or lost response: keep it counted, do not resubmit")
    lost.add_argument("--job-id")
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            requests = plan(args.root, args.canvas, args.model, args.ends, args.shot)
            print(json.dumps({"requests": len(requests), "file": f"keyframes/requests-{args.canvas}.json"}))
        elif args.command == "reserve":
            request = find_request(args.root, args.canvas, args.shot, args.frame)
            print(json.dumps(media.reserve(args.root, "generate_image:keyframe", request, args.estimate), indent=2))
        elif args.command == "record":
            print(json.dumps({"keyframe": record(args.root, args.canvas, args.shot, args.frame, args.entry, args.file, args.job_id)}))
        else:
            print(json.dumps(media.fail(args.root, args.entry, args.uncertain, args.job_id), indent=2))
    except (ContractError, FileNotFoundError) as error:
        print(f"keyframes: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
