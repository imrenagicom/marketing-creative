#!/usr/bin/env python3
"""Final checks for render versions and dailies review of generated takes (stdlib + ffmpeg/ffprobe).

Writes qc/report.json, dailies review files and frames for visual review.
Automated checks never replace watching and listening; reports list what a
person still has to do.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "studio-producer/scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "editor/scripts"))
from edit import measure, version_dir, versions  # noqa: E402
from studio import ContractError, load, now, require  # noqa: E402

DURATION_TOLERANCE = 0.15
LOUDNESS_TOLERANCE = 1.0
BLACK_LIMIT = 0.5
SILENCE_LIMIT = 1.5
MANUAL = [
    "Watch every canvas start to finish with sound",
    "Check keyword timing against the narration at each shot boundary",
    "Check text fits inside safe areas on a phone-sized preview",
    "Listen for mispronounced names and English terms",
    "Confirm claims, numbers and the CTA are approved",
]


def probe(path):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "stream=codec_type,width,height,r_frame_rate:format=duration", "-of", "json", str(path)],
                            capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    video = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    audio = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    num, den = (video["r_frame_rate"].split("/") + ["1"])[:2] if video else ("0", "1")
    return {"width": video and video["width"], "height": video and video["height"],
            "fps": round(int(num) / int(den), 3) if video else None, "audio": audio is not None,
            "duration": float(data["format"]["duration"])}


def detect(path, kind):
    """Return [(start, end)] spans of black video or silent audio."""
    if kind == "black":
        args, pattern = ["-vf", "blackdetect=d=0.1:pix_th=0.05", "-an"], r"black_start:([\d.]+) black_end:([\d.]+)"
    else:
        args, pattern = ["-af", "silencedetect=n=-45dB:d=0.3", "-vn"], None
    result = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), *args, "-f", "null", "-"],
                            capture_output=True, text=True)
    if pattern:
        return [(float(a), float(b)) for a, b in re.findall(pattern, result.stderr)]
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", result.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", result.stderr)]
    return list(zip(starts, ends + [None] * (len(starts) - len(ends))))


def parse_srt(path):
    def seconds(stamp):
        h, m, rest = stamp.split(":")
        s, ms = rest.split(",")
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    return [(seconds(a), seconds(b)) for a, b in re.findall(r"(\d+:\d+:\d+,\d+) --> (\d+:\d+:\d+,\d+)", path.read_text())]


def final(root, version=None):
    root = Path(root)
    version = version or (versions(root) or [None])[-1]
    require(version, "Nothing rendered yet; run the editor first")
    folder = version_dir(root, version)
    manifest = json.loads((folder / "manifest.json").read_text())
    project, words, shots = load(root, "project"), load(root, "words", required=False), load(root, "shots")
    formats = {f["id"]: f for f in project["formats"]}
    delivered = {d["canvas"]: d for d in manifest.get("delivery", [])}
    checks = []

    def check(canvas, name, ok, detail, level="fail"):
        checks.append({"canvas": canvas, "check": name, "status": "pass" if ok else level, "detail": detail})

    for item in manifest["renders"]:
        canvas = item["canvas"]
        delivery = delivered.get(canvas)
        path = folder / (delivery["file"] if delivery else item["file"])
        check(canvas, "delivery", delivery is not None, f"checked {path.relative_to(root)}", "warn")
        info = probe(path)
        expected = formats[canvas]
        check(canvas, "dimensions", (info["width"], info["height"]) == (expected["width"], expected["height"]),
              f"{info['width']}x{info['height']} vs {expected['width']}x{expected['height']}")
        check(canvas, "frame rate", abs((info["fps"] or 0) - project["fps"]) < 0.01, f"{info['fps']} fps vs {project['fps']}")
        planned = shots["shots"][-1]["end"]
        check(canvas, "duration", abs(info["duration"] - planned) <= DURATION_TOLERANCE + 1 / project["fps"],
              f"{info['duration']:.3f}s vs planned {planned:.3f}s")
        check(canvas, "audio stream", info["audio"], "narration track present" if info["audio"] else "no audio stream")
        if info["audio"]:
            loud = measure(path)
            target = delivery["target_lufs"] if delivery else -14.0
            check(canvas, "loudness", abs(float(loud["input_i"]) - target) <= LOUDNESS_TOLERANCE,
                  f"{loud['input_i']} LUFS vs {target}", "fail" if delivery else "warn")
            peak = delivery["target_true_peak"] if delivery else -1.0
            check(canvas, "true peak", float(loud["input_tp"]) <= peak + 0.5, f"{loud['input_tp']} dBTP vs {peak}")
            gaps = [(a, b) for a, b in detect(path, "silence")
                    if a > 0.5 and (b or info["duration"]) < info["duration"] - 1.0 and (b or info["duration"]) - a > SILENCE_LIMIT]
            check(canvas, "mid-video silence", not gaps, f"silent spans {gaps}" if gaps else "none over 1.5s", "warn")
        blacks = [(a, b) for a, b in detect(path, "black") if b - a > BLACK_LIMIT]
        check(canvas, "black frames", not blacks, f"black spans {blacks}" if blacks else "none over 0.5s")
        frames = root / "qc" / "frames" / f"v{version}" / canvas
        frames.mkdir(parents=True, exist_ok=True)
        for shot in shots["shots"]:
            at = (shot["start"] + shot["end"]) / 2
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{at:.3f}", "-i", str(path), "-frames:v", "1",
                            str(frames / f"{shot['id']}.png")], check=True)
        check(canvas, "review frames", True, f"{len(shots['shots'])} frames in {frames.relative_to(root)}")
    srt = root / "captions" / f"{words['language']}.srt" if words else None
    if words is None:
        check("all", "captions", True, "no narration or dialogue timings; captions not required")
    elif srt.is_file():
        spans = parse_srt(srt)
        covered = spans and spans[0][0] <= words["words"][0]["start"] + 0.05 and spans[-1][1] >= words["words"][-1]["end"] - 0.05
        ordered = all(a[1] <= b[0] + 1e-3 for a, b in zip(spans, spans[1:]))
        check("all", "captions", bool(covered and ordered), f"{len(spans)} cues; covers narration: {bool(covered)}; no overlaps: {ordered}")
    else:
        check("all", "captions", False, "no captions file; run edit.py captions", "warn")
    report = {"version": version, "checks": checks, "failed": sum(c["status"] == "fail" for c in checks),
              "warnings": sum(c["status"] == "warn" for c in checks), "manual_checks_remaining": MANUAL}
    (root / "qc").mkdir(exist_ok=True)
    (root / "qc" / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


PILLARS = ("face", "outfit", "location", "movement")
SHOT_TOLERANCE = 0.5


def review_path(root, take_id):
    return Path(root) / "qc" / "dailies" / take_id / "review.json"


def dailies(root, take_id):
    """Frames, a contact sheet and technical checks for one take; pillar verdicts start unreviewed."""
    root = Path(root)
    takes, shots, project = load(root, "takes"), load(root, "shots"), load(root, "project")
    take = next((t for t in takes["takes"] if t["id"] == take_id), None)
    require(take is not None, f"No take {take_id}")
    require(take.get("clips"), f"{take_id} has no shot clips yet ({take['status']}); ingest and split it first")
    canvas = next(f for f in project["formats"] if f["id"] == take["canvas"])
    by_id = {s["id"]: s for s in shots["shots"]}
    folder = root / "qc" / "dailies" / take_id
    folder.mkdir(parents=True, exist_ok=True)
    review = json.loads(review_path(root, take_id).read_text()) if review_path(root, take_id).exists() else {}
    frames, entries = [], {}
    for shot_id in take["shots"]:
        clip = root / take["clips"][shot_id]
        info = probe(clip)
        planned = by_id[shot_id]["end"] - by_id[shot_id]["start"]
        ratio_ok = abs(info["width"] / info["height"] - canvas["width"] / canvas["height"]) < 0.02
        checks = {"aspect": ratio_ok, "duration": abs(info["duration"] - planned) <= SHOT_TOLERANCE}
        shot_frames = []
        for label, fraction in (("a", 0.1), ("b", 0.5), ("c", 0.9)):
            target = folder / f"{shot_id}-{label}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{info['duration'] * fraction:.3f}", "-i", str(clip),
                            "-frames:v", "1", "-vf", "scale=480:-2", str(target)], check=True)
            shot_frames.append(target.name)
            frames.append(target)
        previous = (review.get("shots") or {}).get(shot_id, {})
        entries[shot_id] = {"clip": take["clips"][shot_id], "frames": shot_frames,
                            "measured": {"width": info["width"], "height": info["height"], "duration": info["duration"]},
                            "planned_duration": round(planned, 3), "checks": checks,
                            "pillars": previous.get("pillars") or {pillar: {"status": "unreviewed"} for pillar in PILLARS},
                            "refs": by_id[shot_id].get("refs", [])}
    listing = folder / "sheet.txt"
    listing.write_text("".join(f"file '{p.resolve()}'\nduration 1\n" for p in frames))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-vf",
                    "scale=320:-2,tile=3x%d:padding=4:color=black" % len(take["shots"]), "-frames:v", "1",
                    str(folder / "sheet.png")], check=True)
    listing.unlink()
    bible = load(root, "bible", required=False) or {"references": []}
    review = {"take": take_id, "canvas": take["canvas"], "split": take.get("split"), "created": review.get("created", now()),
              "updated": now(), "sheet": "sheet.png", "shots": entries,
              "reference_images": {ref["id"]: ref.get("images", []) for ref in bible["references"]}}
    review_path(root, take_id).write_text(json.dumps(review, indent=2) + "\n")
    return review


def verdict(root, take_id, shot_id, pillar, passed, note=""):
    path = review_path(root, take_id)
    require(path.exists(), f"Run dailies for {take_id} first")
    review = json.loads(path.read_text())
    require(shot_id in review["shots"], f"{take_id} does not cover {shot_id}")
    require(pillar in PILLARS, f"Pillar must be one of {PILLARS}")
    require(passed or note.strip(), "A failed pillar needs a note saying what drifted")
    review["shots"][shot_id]["pillars"][pillar] = {"status": "pass" if passed else "fail", "note": note, "at": now()}
    review["updated"] = now()
    path.write_text(json.dumps(review, indent=2) + "\n")
    return review["shots"][shot_id]["pillars"]


def passed(root, take_id, shot_id):
    """True when every pillar and automated check passed for this shot in this take."""
    path = review_path(root, take_id)
    if not path.exists():
        return False
    entry = json.loads(path.read_text())["shots"].get(shot_id)
    return bool(entry) and all(entry["checks"].values()) and all(p["status"] == "pass" for p in entry["pillars"].values())


def retakes(root):
    """Shots whose latest dailies have a failed pillar or check."""
    root = Path(root)
    result = []
    for path in sorted((root / "qc" / "dailies").glob("*/review.json")):
        review = json.loads(path.read_text())
        for shot_id, entry in review["shots"].items():
            failed = [p for p, v in entry["pillars"].items() if v["status"] == "fail"]
            failed += [c for c, ok in entry["checks"].items() if not ok]
            if failed:
                result.append({"take": review["take"], "canvas": review["canvas"], "shot": shot_id, "failed": failed,
                               "notes": [v.get("note") for v in entry["pillars"].values() if v.get("note")]})
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    end = sub.add_parser("final", help="Final checks on a render version")
    end.add_argument("root")
    end.add_argument("--version", type=int)
    day = sub.add_parser("dailies", help="Frames, contact sheet and checks for one generated take")
    day.add_argument("root")
    day.add_argument("--take", required=True)
    mark = sub.add_parser("verdict", help="Record a pillar verdict after looking at the frames")
    mark.add_argument("root")
    mark.add_argument("--take", required=True)
    mark.add_argument("--shot", required=True)
    mark.add_argument("--pillar", required=True, choices=PILLARS + ("all",))
    group = mark.add_mutually_exclusive_group(required=True)
    group.add_argument("--pass", dest="passed", action="store_true")
    group.add_argument("--fail", dest="failed", action="store_true")
    mark.add_argument("--note", default="")
    todo = sub.add_parser("retakes", help="List shots that failed dailies")
    todo.add_argument("root")
    args = parser.parse_args(argv)
    try:
        if args.command == "final":
            report = final(args.root, args.version)
            print(json.dumps(report, indent=2))
            return 1 if report["failed"] else 0
        if args.command == "dailies":
            print(json.dumps(dailies(args.root, args.take), indent=2))
        elif args.command == "verdict":
            pillars = PILLARS if args.pillar == "all" else (args.pillar,)
            for pillar in pillars:
                result = verdict(args.root, args.take, args.shot, pillar, args.passed, args.note)
            print(json.dumps(result, indent=2))
        else:
            print(json.dumps(retakes(args.root), indent=2))
    except (ContractError, subprocess.CalledProcessError) as error:
        print(f"qc: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
