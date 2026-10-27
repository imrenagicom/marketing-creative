#!/usr/bin/env python3
"""Compile, approve, submit, ingest and split Higgsfield video takes for a Video Studio film (stdlib + ffmpeg).

The agent makes the MCP calls. This helper owns the exact request, its
fingerprinted approval, the job record and the split of each take into shot
clips, so nothing paid is sent that the user did not approve.
"""
import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[2] / "studio-producer/scripts"))
sys.path.insert(0, str(HERE.parents[2] / "reference-analyst/scripts"))
sys.path.insert(0, str(HERE.parents[2] / "qc-reviewer/scripts"))
import ledger  # noqa: E402
from analyze import cuts, probe  # noqa: E402
import qc  # noqa: E402
from prompting import ASPECT, ELEMENT_MODELS, environment, label, media_refs, refs_for  # noqa: E402
from studio import (ContractError, load, now, require, validate_bible, validate_lock,  # noqa: E402
                    validate_project, validate_shots, validate_takes, write)

PROVIDER = "higgsfield-video"
DEFAULT_MODEL = "seedance_2_5"
SPLIT_TOLERANCE = 0.6


def stamp(seconds):
    return f"{int(seconds // 60):02d}:{seconds % 60:05.2f}".replace(".00", "")


def inputs(root):
    project, lock, bible, shots = load(root, "project"), load(root, "lock"), load(root, "bible"), load(root, "shots")
    validate_project(project)
    validate_lock(lock)
    validate_bible(bible, lock)
    script, words = load(root, "script", required=False), load(root, "words", required=False)
    validate_shots(shots, script, lock, words, bible)
    require(all("start" in shot for shot in shots["shots"]), "Time the shots first (`shots.py time`)")
    takes = load(root, "takes", required=False) or {"schema": "video-studio/takes@1", "takes": [], "selected": {}}
    return project, lock, bible, shots, script, takes


def compile_prompt(members, lock, bible, script, model, canvas, duration):
    """The take prompt: reference roles, locks, environment, timed beats, camera, performance, audio, negatives."""
    refs = {}
    for shot in members:
        for ref in refs_for(shot, bible):
            refs[ref["id"]] = ref
    env, lights = environment(list(refs.values()))
    origin = members[0]["start"]
    characters = {c["id"]: c for c in lock["characters"]}
    lines = {line["id"]: line for line in (script or {}).get("lines", [])}
    out = [f"TITLE: {lock['logline']}", "",
           f"FORMAT: {duration} seconds, {ASPECT[canvas]}, {bible['capture']['look']}. "
           f"{len(members)} shot{'s' if len(members) > 1 else ''} with hard cuts at the times below. "
           "Generate from the references and this text.", "", "REFERENCE ROLES:"]
    for ref in refs.values():
        if ref["role"] == "environment":
            continue
        out.append(f"- {label(ref, model)} — {ref['role'].upper()}: {ref['description']} "
                   f"Preserve {', '.join(ref['preserve'])}. Never redesign or morph.")
    if bible.get("locks"):
        out += ["", "LOCKS:"] + [f"- {item['text']}" for item in bible["locks"]]
    if env:
        out += ["", f"ENVIRONMENT: {label(env, model)} — {env['description']} "
                    f"Light sources: {'; '.join(lights)}. Keep geography and light direction consistent."]
    out += ["", "TIMELINE:"]
    for shot in members:
        start, end = shot["start"] - origin, shot["end"] - origin
        out.append(f"{stamp(start)}–{stamp(end)} — {shot['id']}: {shot['action']}.")
        out.append(f"Camera: {shot['framing']}; {shot['movement']}. Light: {shot['light_source']}. Sound: {shot['sound']}.")
        for line_id in shot.get("lines", []):
            line = lines.get(line_id)
            if line:
                out.append(f'Dialogue ({script["language"]}, {line["speaker"]}): "{line["text"]}"')
    directions = sorted({shot.get("screen_direction", "neutral") for shot in members} - {"neutral"})
    out += ["", "CAMERA LANGUAGE: every camera move has a reason — following action, revealing information or showing "
                "cause and effect. " + (f"Maintain screen direction ({', '.join(directions)}). " if directions else "") +
            "".join(f"{rule.rstrip('.').capitalize()}. " for rule in bible["capture"].get("motion_rules", [])).strip()]
    performers = [characters[ref["character"]] for ref in refs.values() if ref.get("character") in characters]
    if performers:
        out += ["", "PERFORMANCE:"] + [f"- {c['id']}: {c['acting_baseline']}" for c in performers]
    audio = bible.get("audio_policy") or lock.get("audio_policy") or {}
    out += ["", "AUDIO: " + "; ".join(f"{key}: {value}" for key, value in audio.items())]
    if bible.get("negatives"):
        out += ["", "AVOID: " + "; ".join(bible["negatives"]) + "."]
    out += ["", "FINAL PRIORITY: preserve every reference's identity and the location's geography in every shot; "
                "connect the shots with physically coherent movement; keep faces and action readable."]
    return "\n".join(out)


def request_for(members, lock, bible, script, model, canvas, anchors=None):
    duration = math.ceil(round(members[-1]["end"] - members[0]["start"], 3))
    refs = []
    for shot in members:
        refs.extend(ref for ref in refs_for(shot, bible) if ref not in refs)
    medias = media_refs(refs, model)
    start = (anchors or {}).get("start") or (members[0].get("keyframes", {}).get(canvas) or {}).get("start")
    if start:
        medias.insert(0, {"role": "start_image", "asset": start})
    if (anchors or {}).get("end"):
        medias.append({"role": "end_image", "asset": anchors["end"]})
    prompt = compile_prompt(members, lock, bible, script, model, canvas, duration)
    if anchors:
        prompt += "\n\nCONTINUITY: continue seamlessly from the previous shot's last frame" + \
                  (" and end on the next shot's first frame." if anchors.get("end") else ".")
    return {"provider": "higgsfield", "tool": "generate_video", "model": model, "prompt": prompt,
            "duration": duration, "aspect_ratio": ASPECT[canvas], "medias": medias}


def take_id(takes, base):
    existing = {take["id"] for take in takes["takes"]}
    if base not in existing:
        return base
    version = 2
    while f"{base}-v{version}" in existing:
        version += 1
    return f"{base}-v{version}"


def plan(root, canvas, model=DEFAULT_MODEL, only=None):
    project, lock, bible, shots, script, takes = inputs(root)
    require(canvas in {f["id"] for f in project["formats"]}, f"{canvas} is not a project canvas")
    if model not in ELEMENT_MODELS and any(ref.get("higgsfield_element_id") for ref in bible["references"]):
        note = f"{model} ignores element placeholders; reference images are attached as media instead"
    else:
        note = None
    groups = []
    for shot in shots["shots"]:
        if shot["kind"] != "camera":
            continue
        key = shot.get("take") or shot["id"]
        if groups and groups[-1][0] == key:
            groups[-1][1].append(shot)
        else:
            groups.append((key, [shot]))
    planned = []
    for key, members in groups:
        if only and key not in only:
            continue
        base = f"{key}-{canvas}"
        drafts = [t for t in takes["takes"] if t["id"].startswith(base) and t["status"] == "draft"]
        request = request_for(members, lock, bible, script, model, canvas)
        if drafts:
            take = drafts[-1]
        else:
            take = {"id": take_id(takes, base), "canvas": canvas, "shots": [s["id"] for s in members]}
            takes["takes"].append(take)
        take.update({"status": "draft", "provider": "higgsfield", "model": model, "duration": request["duration"],
                     "aspect_ratio": request["aspect_ratio"], "request": request,
                     "request_sha256": ledger.request_sha256(request), "approval": None, "planned_at": now()})
        planned.append(take["id"])
    validate_takes(takes, shots, project)
    write(root, "takes", takes)
    return {"planned": planned, "note": note}


def get_take(takes, take_id):
    take = next((t for t in takes["takes"] if t["id"] == take_id), None)
    require(take is not None, f"No take {take_id}")
    return take


def approve(root, take_id, estimate):
    """Record the user's approval of this take's exact request (only after a clear yes in chat)."""
    project, _, _, shots, _, takes = inputs(root)
    take = get_take(takes, take_id)
    require(take["status"] == "draft", f"{take_id} is {take['status']}; plan a new take instead of re-approving")
    entry = ledger.approve(root, PROVIDER, "generate_video", take["request"], estimate, note=take_id)
    take["status"] = "approved"
    take["approval"] = {"fingerprint": take["request_sha256"], "ledger_entry": entry["id"], "estimate": estimate,
                        "approved_at": now()}
    write(root, "takes", takes)
    return take["approval"]


def submit(root, take_id):
    """Consume the approval right before the MCP call; refuses if the request changed since approval."""
    _, _, _, shots, _, takes = inputs(root)
    take = get_take(takes, take_id)
    require(take["status"] == "approved", f"{take_id} is {take['status']}, not approved")
    require(ledger.request_sha256(take["request"]) == take["approval"]["fingerprint"],
            "The request changed after approval; plan it again and ask the user")
    ledger.consume_approval(root, PROVIDER, take["request"])
    take["status"] = "submitted"
    take["submitted_at"] = now()
    write(root, "takes", takes)
    return take["request"]


def job(root, take_id, job_id):
    _, _, _, _, _, takes = inputs(root)
    take = get_take(takes, take_id)
    require(take["status"] in {"submitted", "unknown"}, f"{take_id} is {take['status']}")
    take["job_id"] = job_id
    ledger.update(root, take["approval"]["ledger_entry"], job_id=job_id)
    write(root, "takes", takes)
    return take


def fail(root, take_id, uncertain=False):
    _, _, _, _, _, takes = inputs(root)
    take = get_take(takes, take_id)
    take["status"] = "unknown" if uncertain else "failed"
    ledger.update(root, take["approval"]["ledger_entry"], status=take["status"])
    write(root, "takes", takes)
    return take


def cut_clips(raw, folder, members, bounds, width, height):
    folder.mkdir(parents=True, exist_ok=True)
    clips = {}
    for shot, (start, end) in zip(members, bounds):
        target = folder / f"{shot}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-to", f"{end:.3f}", "-i", str(raw),
                        "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "aac", str(target)], check=True)
        clips[shot] = target
    return clips


def split(root, take_id, at=None, threshold=0.3):
    """Split a take into shot clips at detected cuts, or at times the user confirmed."""
    project, _, _, shots, _, takes = inputs(root)
    take = get_take(takes, take_id)
    require(take.get("raw"), f"{take_id} has no ingested video")
    raw = Path(root) / take["raw"]
    info = probe(raw)
    members = take["shots"]
    by_id = {s["id"]: s for s in shots["shots"]}
    origin = by_id[members[0]]["start"]
    planned = [round(by_id[s]["end"] - origin, 3) for s in members[:-1]]
    if at is not None:
        boundaries, source = sorted(at), "manual"
    elif len(members) == 1:
        boundaries, source = [], "single shot"
    else:
        detected = [t for t in cuts(raw, threshold) if 0.2 < t < info["duration"] - 0.2]
        take["detected_cuts"] = detected
        matched = len(detected) == len(planned) and all(abs(d - p) <= SPLIT_TOLERANCE for d, p in zip(detected, planned))
        if not matched:
            take["status"] = "needs-split"
            take["split"] = {"planned": planned, "detected": detected, "reason": "detected cuts do not match the plan"}
            write(root, "takes", takes)
            return take
        boundaries, source = detected, "detected"
    require(len(boundaries) == len(members) - 1, f"{take_id} needs {len(members) - 1} cut time(s)")
    edges = [0.0] + boundaries + [info["duration"]]
    folder = Path(root) / "takes" / take_id / "clips"
    clips = cut_clips(raw, folder, members, list(zip(edges, edges[1:])), info["width"], info["height"])
    take["clips"] = {shot: str(path.relative_to(root)) for shot, path in clips.items()}
    take["split"] = {"source": source, "boundaries": boundaries, "planned": planned}
    take["status"] = "succeeded"
    write(root, "takes", takes)
    return take


def ingest(root, take_id, source):
    """Store the returned video beside the take, check it, and split it into shot clips."""
    project, _, _, shots, _, takes = inputs(root)
    take = get_take(takes, take_id)
    require(take["status"] in {"submitted", "unknown"}, f"{take_id} is {take['status']}; only submitted takes are ingested")
    source = Path(source)
    require(source.is_file(), f"No file at {source}")
    folder = Path(root) / "takes" / take_id
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "raw.mp4"
    require(not target.exists(), f"{take_id} already has a raw video; plan a retake instead of replacing it")
    shutil.copy2(source, target)
    info = probe(target)
    take["raw"] = str(target.relative_to(root))
    take["raw_info"] = info
    take["ingested_at"] = now()
    take["status"] = "submitted"
    ledger.update(root, take["approval"]["ledger_entry"], status="succeeded", outputs=[take["raw"]])
    write(root, "takes", takes)
    return split(root, take_id)


def select(root, take_id, shot_ids=None, skip_dailies=None):
    project, _, _, shots, _, takes = inputs(root)
    take = get_take(takes, take_id)
    require(take["status"] == "succeeded", f"{take_id} has no clips yet ({take['status']})")
    chosen = takes.setdefault("selected", {}).setdefault(take["canvas"], {})
    for shot in shot_ids or take["shots"]:
        require(shot in take["shots"], f"{take_id} does not cover {shot}")
        if not skip_dailies:
            require(qc.passed(root, take_id, shot), f"{shot} in {take_id} has not passed dailies; run qc.py dailies and "
                                                     "record verdicts, or pass --skip-dailies with the user's reason")
        chosen[shot] = take_id
    if skip_dailies:
        take.setdefault("dailies_skipped", []).append({"shots": shot_ids or take["shots"], "reason": skip_dailies, "at": now()})
    validate_takes(takes, shots, project)
    write(root, "takes", takes)
    return takes["selected"]


def frame_at(video, seconds, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, seconds):.3f}", "-i", str(video), "-frames:v", "1",
                    str(target)], check=True)
    return target


def retake(root, canvas, shot_id, model=DEFAULT_MODEL, with_end=False):
    """Plan a single-shot retake anchored on the neighbouring shots' selected clips."""
    project, lock, bible, shots, script, takes = inputs(root)
    order = [s["id"] for s in shots["shots"]]
    require(shot_id in order, f"No shot {shot_id}")
    index = order.index(shot_id)
    chosen = (takes.get("selected") or {}).get(canvas, {})
    by_take = {t["id"]: t for t in takes["takes"]}
    new_id = take_id(takes, f"{shot_id}-retake-{canvas}")
    anchors = {}
    if index > 0 and order[index - 1] in chosen:
        clip = Path(root) / by_take[chosen[order[index - 1]]]["clips"][order[index - 1]]
        length = probe(clip)["duration"]
        anchors["start"] = str(frame_at(clip, length - 0.05, Path(root) / "takes" / new_id / "anchors/start.png").relative_to(root))
    if with_end and index + 1 < len(order) and order[index + 1] in chosen:
        clip = Path(root) / by_take[chosen[order[index + 1]]]["clips"][order[index + 1]]
        anchors["end"] = str(frame_at(clip, 0, Path(root) / "takes" / new_id / "anchors/end.png").relative_to(root))
    shot = shots["shots"][index]
    request = request_for([shot], lock, bible, script, model, canvas, anchors or None)
    takes["takes"].append({"id": new_id, "canvas": canvas, "shots": [shot_id], "status": "draft", "provider": "higgsfield",
                           "model": model, "duration": request["duration"], "aspect_ratio": request["aspect_ratio"],
                           "request": request, "request_sha256": ledger.request_sha256(request), "approval": None,
                           "retake_of": chosen.get(shot_id), "planned_at": now()})
    validate_takes(takes, shots, project)
    write(root, "takes", takes)
    return new_id


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    draft = sub.add_parser("plan", help="Compile take requests for a canvas")
    draft.add_argument("root")
    draft.add_argument("--canvas", required=True)
    draft.add_argument("--model", default=DEFAULT_MODEL)
    draft.add_argument("--take", action="append", help="Limit to take groups (shot `take` ids)")
    show = sub.add_parser("show", help="Print a take's exact request")
    show.add_argument("root")
    show.add_argument("--take", required=True)
    allow = sub.add_parser("approve", help="Record the user's approval of a take's exact request")
    allow.add_argument("root")
    allow.add_argument("--take", required=True)
    allow.add_argument("--estimate", required=True, type=float, help="Credits from get_cost for this exact request")
    send = sub.add_parser("submit", help="Consume the approval right before calling generate_video")
    send.add_argument("root")
    send.add_argument("--take", required=True)
    record = sub.add_parser("job", help="Record the returned job id")
    record.add_argument("root")
    record.add_argument("--take", required=True)
    record.add_argument("--job-id", required=True)
    lost = sub.add_parser("fail", help="Record a refused or uncertain submission")
    lost.add_argument("root")
    lost.add_argument("--take", required=True)
    lost.add_argument("--uncertain", action="store_true")
    take_in = sub.add_parser("ingest", help="Store the downloaded take and split it into shot clips")
    take_in.add_argument("root")
    take_in.add_argument("--take", required=True)
    take_in.add_argument("--file", required=True)
    cut = sub.add_parser("split", help="Split at confirmed cut times (seconds into the take)")
    cut.add_argument("root")
    cut.add_argument("--take", required=True)
    cut.add_argument("--at", required=True, help="Comma-separated seconds, one per cut")
    pick = sub.add_parser("select", help="Use a take's clips for its shots (or only --shot)")
    pick.add_argument("root")
    pick.add_argument("--take", required=True)
    pick.add_argument("--shot", action="append")
    pick.add_argument("--skip-dailies", metavar="REASON", help="Select without a passed dailies review (record why)")
    again = sub.add_parser("retake", help="Plan a single-shot retake anchored on neighbouring clips")
    again.add_argument("root")
    again.add_argument("--canvas", required=True)
    again.add_argument("--shot", required=True)
    again.add_argument("--model", default=DEFAULT_MODEL)
    again.add_argument("--with-end", action="store_true", help="Also anchor the end on the next shot (model must support end frames)")
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            result = plan(args.root, args.canvas, args.model, args.take)
        elif args.command == "show":
            result = get_take(inputs(args.root)[5], args.take)["request"]
        elif args.command == "approve":
            result = approve(args.root, args.take, args.estimate)
        elif args.command == "submit":
            result = submit(args.root, args.take)
        elif args.command == "job":
            result = {"take": args.take, "job_id": job(args.root, args.take, args.job_id)["job_id"]}
        elif args.command == "fail":
            result = {"take": args.take, "status": fail(args.root, args.take, args.uncertain)["status"]}
        elif args.command == "ingest":
            take = ingest(args.root, args.take, args.file)
            result = {"take": args.take, "status": take["status"], "clips": take.get("clips"), "split": take.get("split")}
        elif args.command == "split":
            times = [float(x) for x in args.at.split(",") if x.strip()]
            take = split(args.root, args.take, times)
            result = {"take": args.take, "status": take["status"], "clips": take.get("clips")}
        elif args.command == "select":
            result = select(args.root, args.take, args.shot, args.skip_dailies)
        else:
            result = {"planned": retake(args.root, args.canvas, args.shot, args.model, args.with_end)}
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except (ContractError, subprocess.CalledProcessError) as error:
        print(f"takes: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
