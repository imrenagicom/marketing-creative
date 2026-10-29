#!/usr/bin/env python3
"""Check the continuity bible, derive negative constraints, and track reference images (Higgsfield or Gemini) and Higgsfield elements."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "studio-producer/scripts"))
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


def sheet_requests(root, model, provider="higgsfield", image_size="2K"):
    """Image requests for missing reference images (run them under the image cap)."""
    _, bible = inputs(root)
    look = bible["capture"]["look"]
    requests = []
    for ref in bible["references"]:
        if ref.get("images"):
            continue
        prompt = SHEETS[ref["role"]].format(name=ref["name"], description=ref["description"],
                                            lights=", ".join(ref.get("light_sources", [])) or "soft daylight")
        if ref["role"] in {"environment", "style"}:
            prompt += f" Look: {look}."
        aspect = "16:9" if ref["role"] in {"environment", "style"} else "3:2"
        if provider == "gemini":
            requests.append({"ref": ref["id"], **gemini.image_request(model, prompt, aspect, image_size, [])})
        else:
            requests.append({"ref": ref["id"], "model": model, "prompt": prompt, "aspect_ratio": aspect})
    path = Path(root) / "bible/image-requests.json"
    path.write_text(json.dumps({"requests": requests}, indent=2, ensure_ascii=False) + "\n")
    return requests


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
            print(json.dumps(sheet_requests(args.root, model, args.provider, args.image_size), indent=2, ensure_ascii=False))
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
