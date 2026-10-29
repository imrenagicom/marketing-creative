#!/usr/bin/env python3
"""Check the continuity bible, derive negative constraints, and track reference images (Higgsfield or Gemini) and Higgsfield elements;
preview look options for one reference on a Gemini contact-sheet board."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "studio-producer/scripts"))
import boards  # noqa: E402
import gemini  # noqa: E402
import media  # noqa: E402
from studio import ContractError, load, require, validate_bible, validate_lock, write  # noqa: E402

ELEMENT_CATEGORY = {"character": "character", "environment": "environment", "prop": "prop", "vehicle": "prop"}
SHEETS = {
    "character": "Character reference sheet of {name}: {description}. Front, three-quarter, side and back views on a neutral "
                 "grey background, full body plus a head close-up, even soft studio light, no props, no text.",
    "environment": "Environment master of {name}: {description}. Wide establishing view at eye level showing the full layout, "
                   "lit by {lights}. No people.",
    "prop": "Product reference of {name}: {description}. Front, side and top views on a neutral grey background, even light, no text.",
    "vehicle": "Vehicle reference of {name}: {description}. Front, side, rear and three-quarter views on a neutral grey background, "
               "even light, no text.",
    "style": "Style frame for {name}: {description}.",
}


def inputs(root):
    lock, bible = load(root, "lock"), load(root, "bible")
    validate_lock(lock)
    validate_bible(bible, lock)
    return lock, bible


def check(root):
    _, bible = inputs(root)
    warnings = []
    for ref in bible["references"]:
        missing = [path for path in ref.get("images", []) if not (Path(root) / path).is_file()]
        if missing:
            warnings.append(f"{ref['id']} lists missing images {missing}")
        if not ref.get("images"):
            warnings.append(f"{ref['id']} has no reference image; generate or supply one before keyframes")
        if ref["role"] in ELEMENT_CATEGORY and ref.get("images") and not ref.get("higgsfield_element_id"):
            warnings.append(f"{ref['id']} has images but no Higgsfield element; create one so prompts can lock identity")
        if len(ref["preserve"]) < 3 and ref["role"] in {"character", "vehicle"}:
            warnings.append(f"{ref['id']} preserves only {len(ref['preserve'])} features; list what must never change")
    if not any(ref["role"] == "environment" for ref in bible["references"]):
        warnings.append("No environment reference; every shot will invent its own location and light")
    return {"warnings": warnings}


def negatives(bible):
    """Negative constraints derived from preserve lists, locks and capture rules."""
    result = []
    for ref in bible["references"]:
        if ref["role"] == "character":
            result.append(f"no change to {ref['name']}'s face, hair, outfit or proportions ({', '.join(ref['preserve'])})")
        elif ref["role"] in {"prop", "vehicle"}:
            result.append(f"no redesign of the {ref['name']} ({', '.join(ref['preserve'])})")
        elif ref["role"] == "environment":
            result.append(f"no change to the {ref['name']} layout or light direction")
    result += ["no duplicated or extra characters", "no distorted hands or faces", "no teleporting or random camera rotations",
               "no added text, subtitles, logos or watermarks"]
    return result


def derive(root):
    _, bible = inputs(root)
    bible["negatives"] = negatives(bible)
    write(root, "bible", bible)
    return bible["negatives"]


def sheet_prompt(ref, look):
    prompt = SHEETS[ref["role"]].format(name=ref["name"], description=ref["description"],
                                        lights=", ".join(ref.get("light_sources", [])) or "soft daylight")
    if ref["role"] in {"environment", "style"}:
        prompt += f" Look: {look}."
    return prompt, "16:9" if ref["role"] in {"environment", "style"} else "3:2"


def sheet_requests(root, model, provider="higgsfield", image_size="2K", tiles=None):
    """Image requests for missing reference images (run them under the image cap).

    tiles maps a reference id to a chosen board tile, attached to its Gemini request as a look reference.
    """
    _, bible = inputs(root)
    tiles = tiles or {}
    require(not tiles or provider == "gemini", "Board tiles attach only to Gemini sheet requests")
    look = bible["capture"]["look"]
    requests = []
    for ref in bible["references"]:
        if ref.get("images"):
            continue
        prompt, aspect = sheet_prompt(ref, look)
        if provider == "gemini":
            chosen = [tiles[ref["id"]]] if ref["id"] in tiles else []
            require(all((Path(root) / tile).is_file() for tile in chosen), f"No board tile at {chosen}")
            if chosen:
                prompt = (f"{prompt} The attached board tile is the look option the user chose; match its design, "
                          "then render the full sheet cleanly at full resolution.")
            requests.append({"ref": ref["id"], **gemini.image_request(model, prompt, aspect, image_size, chosen)})
        else:
            requests.append({"ref": ref["id"], "model": model, "prompt": prompt, "aspect_ratio": aspect})
    path = Path(root) / "bible/image-requests.json"
    path.write_text(json.dumps({"requests": requests}, indent=2, ensure_ascii=False) + "\n")
    return requests


def board(root, ref_id, variants, grid=None, model=None, image_size="2K"):
    """Plan one contact sheet of look options for a reference that has no approved image yet."""
    _, bible = inputs(root)
    ref = next((item for item in bible["references"] if item["id"] == ref_id), None)
    require(ref is not None, f"No bible reference {ref_id}")
    require(len(variants) >= 2, "Give at least two --variant options; a board compares choices")
    prompt, aspect = sheet_prompt(ref, bible["capture"]["look"])
    cells = [{"id": f"{ref_id}-{index + 1}", "prompt": f"{prompt} Option: {text}"} for index, text in enumerate(variants)]
    preamble = (f"Every frame shows a different design option for the same {ref['role']}, {ref['name']}. Keep these "
                f"features in every option: {', '.join(ref['preserve'])}.")
    relative, planned = boards.plan(root, f"bible/boards/{ref_id}", cells, aspect, preamble, ref.get("images", []),
                                    grid, model, image_size)
    return {"board": relative, "cells": [c["id"] for c in planned["cells"]], "grid": f"{planned['rows']}x{planned['columns']}",
            "estimate_usd": planned["estimate_usd"]}


def add_image(root, ref_id, entry_id, source, job_id=None):
    lock, bible = inputs(root)
    ref = next((item for item in bible["references"] if item["id"] == ref_id), None)
    require(ref is not None, f"No bible reference {ref_id}")
    name = media.next_name(Path(root) / "bible/images", ref_id, Path(source).suffix or ".png")
    destination = f"bible/images/{name}"
    media.complete(root, entry_id, source, destination, job_id)
    ref.setdefault("images", []).append(destination)
    write(root, "bible", bible)
    return destination


def find_request(root, ref_id):
    requests = json.loads((Path(root) / "bible/image-requests.json").read_text())["requests"]
    request = next((r for r in requests if r["ref"] == ref_id), None)
    require(request is not None, f"No image request for {ref_id}; run `bible.py sheets` first")
    return request


def generate(root, ref_id, estimate=None):
    """Run a Gemini sheet request under the gemini-image cap and add the image to the reference."""
    request = find_request(root, ref_id)
    require(request.get("provider") == "gemini", f"The {ref_id} request is for Higgsfield; use reserve → generate_image → add-image")
    entry, path, response_id = media.generate_gemini(root, "gemini-api image:reference", request, estimate)
    return {"image": add_image(root, ref_id, entry["id"], path, response_id), "entry": entry["id"],
            "estimate_usd": entry["estimate"], **({"warning": entry["warning"]} if entry.get("warning") else {})}


def link(root, ref_id, element_id):
    _, bible = inputs(root)
    ref = next((item for item in bible["references"] if item["id"] == ref_id), None)
    require(ref is not None, f"No bible reference {ref_id}")
    require(ref["role"] in ELEMENT_CATEGORY, f"{ref['role']} references are not Higgsfield elements")
    ref["higgsfield_element_id"] = element_id
    write(root, "bible", bible)
    return ref


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "negatives"):
        sub.add_parser(name).add_argument("root")
    sheets = sub.add_parser("sheets", help="Write image requests for references without images")
    sheets.add_argument("root")
    sheets.add_argument("--provider", choices=["gemini", "higgsfield"], default="higgsfield")
    sheets.add_argument("--model", help=f"Default gpt_image_2_5 (higgsfield) or {gemini.IMAGE_MODEL} (gemini)")
    sheets.add_argument("--image-size", default="2K", help="Gemini only: 512, 1K, 2K or 4K")
    sheets.add_argument("--tile", action="append", default=[], metavar="REF=PATH",
                        help="Gemini only: attach the chosen board tile to that reference's request (repeatable)")
    options = sub.add_parser("board", help="Gemini: plan one contact sheet of look options for a reference")
    options.add_argument("root")
    options.add_argument("--ref", required=True)
    options.add_argument("--variant", action="append", required=True, help="One design option per cell (2–12)")
    options.add_argument("--grid", help="ROWSxCOLUMNS; default packs cells close to the sheet ratio")
    options.add_argument("--model", help=f"Default {gemini.IMAGE_MODEL}")
    options.add_argument("--image-size", default="2K", help="512, 1K, 2K or 4K for the whole sheet")
    for name, text in (("board-preview", "Gemini: the board's exact CLI command, estimate and offline --dry-run"),
                       ("board-generate", "Gemini: one board call under the image cap, then split it into preview tiles"),
                       ("board-split", "Re-split a returned board, for example with an inset to clear gutters")):
        part = sub.add_parser(name, help=text)
        part.add_argument("root")
        part.add_argument("--board", required=True, help="Board folder, e.g. bible/boards/courier/board-v1")
        if name == "board-generate":
            part.add_argument("--estimate", type=float, help="USD; needed only when no published price covers it")
        if name == "board-split":
            part.add_argument("--inset", type=int, default=0, help="Pixels trimmed from every tile edge")
    run = sub.add_parser("generate", help="Gemini: run a sheet request under the image cap and add the image")
    run.add_argument("root")
    run.add_argument("--ref", required=True)
    run.add_argument("--estimate", type=float, help="USD; needed only when no published price covers the model/size")
    look = sub.add_parser("preview", help="Gemini: show the exact CLI command, estimate and offline --dry-run")
    look.add_argument("root")
    look.add_argument("--ref", required=True)
    reserve = sub.add_parser("reserve", help="Check the image cap and record one reference-image job before the MCP call")
    reserve.add_argument("root")
    reserve.add_argument("--ref", required=True)
    reserve.add_argument("--estimate", required=True, type=float, help="Credits from get_cost")
    add = sub.add_parser("add-image", help="Store a returned reference image")
    add.add_argument("root")
    add.add_argument("--ref", required=True)
    add.add_argument("--entry", required=True)
    add.add_argument("--file", required=True)
    add.add_argument("--job-id")
    lost = sub.add_parser("fail", help="Record a failed or uncertain reference-image job")
    lost.add_argument("root")
    lost.add_argument("--entry", required=True)
    lost.add_argument("--uncertain", action="store_true", help="Timeout or lost response: keep it counted, do not resubmit")
    connect = sub.add_parser("link", help="Record a Higgsfield element id for a reference")
    connect.add_argument("root")
    connect.add_argument("--ref", required=True)
    connect.add_argument("--element", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            print(json.dumps(check(args.root), indent=2, ensure_ascii=False))
        elif args.command == "negatives":
            print(json.dumps(derive(args.root), indent=2, ensure_ascii=False))
        elif args.command == "sheets":
            model = args.model or (gemini.IMAGE_MODEL if args.provider == "gemini" else "gpt_image_2_5")
            tiles = dict(item.split("=", 1) for item in args.tile if "=" in item)
            require(len(tiles) == len(args.tile), "Use --tile REF=PATH")
            print(json.dumps(sheet_requests(args.root, model, args.provider, args.image_size, tiles), indent=2,
                             ensure_ascii=False))
        elif args.command == "board":
            print(json.dumps(board(args.root, args.ref, args.variant, boards.parse_grid(args.grid), args.model,
                                   args.image_size), indent=2))
        elif args.command == "board-preview":
            print(json.dumps(gemini.preview(args.root, boards.read(args.root, args.board)["request"]), indent=2,
                             ensure_ascii=False))
        elif args.command == "board-generate":
            print(json.dumps(boards.generate(args.root, args.board, args.estimate), indent=2))
        elif args.command == "board-split":
            print(json.dumps(boards.split(args.root, args.board, args.inset), indent=2))
        elif args.command == "generate":
            print(json.dumps(generate(args.root, args.ref, args.estimate), indent=2))
        elif args.command == "preview":
            request = find_request(args.root, args.ref)
            require(request.get("provider") == "gemini", "preview runs the gemini-api dry-run; this request is for Higgsfield")
            print(json.dumps(gemini.preview(args.root, request), indent=2, ensure_ascii=False))
        elif args.command == "reserve":
            request = find_request(args.root, args.ref)
            print(json.dumps(media.reserve(args.root, "generate_image:reference", request, args.estimate), indent=2))
        elif args.command == "fail":
            print(json.dumps(media.fail(args.root, args.entry, args.uncertain), indent=2))
        elif args.command == "add-image":
            print(json.dumps({"image": add_image(args.root, args.ref, args.entry, args.file, args.job_id)}))
        else:
            print(json.dumps(link(args.root, args.ref, args.element), indent=2, ensure_ascii=False))
    except (ContractError, FileNotFoundError) as error:
        print(f"bible: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
