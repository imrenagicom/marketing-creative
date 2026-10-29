#!/usr/bin/env python3
"""Plan, reserve and record start/end keyframes for camera shots under the Higgsfield or Gemini image cap,
or preview many shots at once on one Gemini contact-sheet board."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "studio-producer/scripts"))
import boards  # noqa: E402
import gemini  # noqa: E402
import media  # noqa: E402
from prompting import ASPECT, environment, media_refs, refs_for, subject  # noqa: E402
from studio import (ContractError, load, require, validate_bible, validate_lock, validate_project,  # noqa: E402
                    validate_shots, write)

DEFAULT_MODEL = "nano_banana_pro"
DEFAULT_MODELS = {"higgsfield": DEFAULT_MODEL, "gemini": gemini.IMAGE_MODEL}
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


def plan(root, canvas, model=None, ends=False, only=None, provider="higgsfield", image_size="2K", tiles=None):
    model = model or DEFAULT_MODELS[provider]
    require(not tiles or provider == "gemini", "Board tiles attach only to Gemini keyframe requests")
    project, lock, bible, shots = inputs(root)
    require(canvas in {f["id"] for f in project["formats"]}, f"{canvas} is not a project canvas")
    requests = []
    for shot in shots["shots"]:
        if shot["kind"] != "camera" or (only and shot["id"] not in only):
            continue
        for frame in FRAMES if ends else FRAMES[:1]:
            refs = refs_for(shot, bible)
            prompt = prompt_for(shot, frame, bible, lock, model, canvas)
            if provider == "gemini":
                # Gemini has no element ids: reference images go in as inputs and the prompt names them.
                images = [item["asset"] for item in media_refs(refs, model)]
                tile = f"{tiles}/{shot['id']}-{frame}.png" if tiles else None
                if tile and (Path(root) / tile).is_file():
                    images.append(tile)
                    prompt = f"{prompt} {boards.TILE_NOTE}"
                request = gemini.image_request(model, prompt, ASPECT[canvas], image_size, images)
                require(not gemini.problems(request), "; ".join(gemini.problems(request)))
            else:
                request = {"model": model, "aspect_ratio": ASPECT[canvas], "prompt": prompt, "medias": media_refs(refs, model)}
            requests.append({"shot": shot["id"], "frame": frame, "canvas": canvas, **request})
    folder = Path(root) / "keyframes"
    folder.mkdir(exist_ok=True)
    (folder / f"requests-{canvas}.json").write_text(json.dumps({"requests": requests}, indent=2, ensure_ascii=False) + "\n")
    return requests


def board(root, canvas, only=None, frame="start", grid=None, model=None, image_size="2K"):
    """Plan one contact sheet previewing the chosen camera shots' keyframes in a single Gemini call."""
    project, lock, bible, shots = inputs(root)
    require(canvas in {f["id"] for f in project["formats"]}, f"{canvas} is not a project canvas")
    model = model or gemini.IMAGE_MODEL
    chosen = [s for s in shots["shots"] if s["kind"] == "camera" and (not only or s["id"] in only)]
    require(chosen, "No camera shots to put on a board")
    cells, images = [], []
    for shot in chosen:
        refs = refs_for(shot, bible)
        images += [item["asset"] for item in media_refs(refs, model)]
        cells.append({"id": f"{shot['id']}-{frame}", "prompt": prompt_for(shot, frame, bible, lock, model, canvas)})
    preamble = ("These frames are consecutive shots of one film: keep every character, outfit, prop and location "
                f"identical between frames, as shown in the attached references. Look: {bible['capture']['look']}.")
    relative, planned = boards.plan(root, f"keyframes/boards/{canvas}", cells, ASPECT[canvas], preamble, images,
                                    grid, model, image_size)
    return {"board": relative, "cells": [c["id"] for c in planned["cells"]], "grid": f"{planned['rows']}x{planned['columns']}",
            "sheet_aspect": planned["sheet_aspect"], "estimate_usd": planned["estimate_usd"]}


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


def generate(root, canvas, shot_id, frame, estimate=None):
    """Run a planned Gemini keyframe under the gemini-image cap and record it."""
    request = find_request(root, canvas, shot_id, frame)
    require(request.get("provider") == "gemini", f"The {frame} keyframe for {shot_id} is planned for Higgsfield; "
                                                "use reserve → generate_image → record")
    entry, path, response_id = media.generate_gemini(root, "gemini-api image:keyframe", request, estimate)
    destination = record(root, canvas, shot_id, frame, entry["id"], path, response_id)
    return {"keyframe": destination, "entry": entry["id"], "estimate_usd": entry["estimate"],
            **({"warning": entry["warning"]} if entry.get("warning") else {})}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    draft = sub.add_parser("plan", help="Write keyframe requests for camera shots")
    draft.add_argument("root")
    draft.add_argument("--canvas", required=True)
    draft.add_argument("--provider", choices=sorted(DEFAULT_MODELS), default="higgsfield")
    draft.add_argument("--model", help=f"Default {DEFAULT_MODEL} (higgsfield) or {gemini.IMAGE_MODEL} (gemini)")
    draft.add_argument("--image-size", default="2K", help="Gemini only: 512, 1K, 2K or 4K")
    draft.add_argument("--ends", action="store_true", help="Also plan end frames (for start/end-frame video models)")
    draft.add_argument("--shot", action="append", help="Limit to shots (repeatable)")
    draft.add_argument("--tiles", help="Gemini only: a board tiles-vN folder; a selected <shot>-<frame>.png is attached")
    sheet = sub.add_parser("board", help="Gemini: plan one contact sheet previewing many shots' keyframes")
    sheet.add_argument("root")
    sheet.add_argument("--canvas", required=True)
    sheet.add_argument("--shot", action="append", help="Limit to shots (repeatable); at most 12 per board")
    sheet.add_argument("--frame", choices=FRAMES, default="start")
    sheet.add_argument("--grid", help="ROWSxCOLUMNS; default packs cells close to the canvas ratio")
    sheet.add_argument("--model", help=f"Default {gemini.IMAGE_MODEL}")
    sheet.add_argument("--image-size", default="2K", help="512, 1K, 2K or 4K for the whole sheet")
    for name, text in (("board-preview", "Gemini: the board's exact CLI command, estimate and offline --dry-run"),
                       ("board-generate", "Gemini: one board call under the image cap, then split it into preview tiles"),
                       ("board-split", "Re-split a returned board, for example with an inset to clear gutters")):
        part = sub.add_parser(name, help=text)
        part.add_argument("root")
        part.add_argument("--board", required=True, help="Board folder, e.g. keyframes/boards/16x9/board-v1")
        if name == "board-generate":
            part.add_argument("--estimate", type=float, help="USD; needed only when no published price covers it")
        if name == "board-split":
            part.add_argument("--inset", type=int, default=0, help="Pixels trimmed from every tile edge")
    hold = sub.add_parser("reserve", help="Check the image cap and record one keyframe job before the MCP call")
    hold.add_argument("root")
    hold.add_argument("--canvas", required=True)
    hold.add_argument("--shot", required=True)
    hold.add_argument("--frame", choices=FRAMES, default="start")
    hold.add_argument("--estimate", required=True, type=float, help="Credits from get_cost")
    look = sub.add_parser("preview", help="Gemini: show the exact CLI command, estimate and offline --dry-run")
    look.add_argument("root")
    look.add_argument("--canvas", required=True)
    look.add_argument("--shot", required=True)
    look.add_argument("--frame", choices=FRAMES, default="start")
    run = sub.add_parser("generate", help="Gemini: reserve under the image cap, run gemini-api image and record")
    run.add_argument("root")
    run.add_argument("--canvas", required=True)
    run.add_argument("--shot", required=True)
    run.add_argument("--frame", choices=FRAMES, default="start")
    run.add_argument("--estimate", type=float, help="USD; needed only when no published price covers the model/size")
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
            requests = plan(args.root, args.canvas, args.model, args.ends, args.shot, args.provider, args.image_size,
                            args.tiles)
            print(json.dumps({"requests": len(requests), "file": f"keyframes/requests-{args.canvas}.json"}))
        elif args.command == "board":
            print(json.dumps(board(args.root, args.canvas, args.shot, args.frame, boards.parse_grid(args.grid),
                                   args.model, args.image_size), indent=2))
        elif args.command == "board-preview":
            print(json.dumps(gemini.preview(args.root, boards.read(args.root, args.board)["request"]), indent=2,
                             ensure_ascii=False))
        elif args.command == "board-generate":
            print(json.dumps(boards.generate(args.root, args.board, args.estimate), indent=2))
        elif args.command == "board-split":
            print(json.dumps(boards.split(args.root, args.board, args.inset), indent=2))
        elif args.command == "reserve":
            request = find_request(args.root, args.canvas, args.shot, args.frame)
            print(json.dumps(media.reserve(args.root, "generate_image:keyframe", request, args.estimate), indent=2))
        elif args.command == "preview":
            request = find_request(args.root, args.canvas, args.shot, args.frame)
            require(request.get("provider") == "gemini", "preview runs the gemini-api dry-run; this request is for Higgsfield")
            print(json.dumps(gemini.preview(args.root, request), indent=2, ensure_ascii=False))
        elif args.command == "generate":
            print(json.dumps(generate(args.root, args.canvas, args.shot, args.frame, args.estimate), indent=2))
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
