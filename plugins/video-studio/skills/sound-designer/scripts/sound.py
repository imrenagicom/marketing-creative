#!/usr/bin/env python3
"""Plan and generate sound effects, ambience beds and music with the ElevenLabs CLI, placed on the shot timeline.

Calls run under the project's approved ElevenLabs cap and are recorded before
they are sent. `plan` is the dry run.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "studio-producer/scripts"))
import ledger  # noqa: E402
from studio import ContractError, load, now, require, write  # noqa: E402

PROVIDER = "elevenlabs"
MAX_SFX = 30.0
GAIN = {"sfx": -6.0, "ambience": -18.0, "music": -16.0}
NONE = {"none", "no", "off", "false", ""}


def cli():
    return os.environ.get("VIDEO_STUDIO_ELEVENLABS_BIN", "elevenlabs")


def policy_off(value):
    return str(value or "").strip().casefold().split(":")[0].split(",")[0] in NONE


def inputs(root):
    project, lock, shots = load(root, "project"), load(root, "lock"), load(root, "shots")
    require(all("start" in shot for shot in shots["shots"]), "Time the shots first (`shots.py time`)")
    config = load(root, "sound_config")
    require(config.get("schema") == "video-studio/sound-config@1", "sound-config.json must declare video-studio/sound-config@1")
    for key in ("sfx_credits_per_second", "music_credits_per_second"):
        require(isinstance(config.get(key), (int, float)) and config[key] >= 0, f"sound-config needs {key} (current rate)")
    bible = load(root, "bible", required=False)
    return project, lock, shots, config, bible


def plan(root):
    project, lock, shots, config, bible = inputs(root)
    audio = (bible or {}).get("audio_policy") or lock.get("audio_policy") or {}
    items = shots["shots"]
    total = items[-1]["end"]
    cues = []
    if not policy_off(audio.get("sfx")):
        for shot in items:
            if shot.get("sound"):
                length = round(min(shot["end"] - shot["start"], MAX_SFX), 2)
                cues.append({"id": f"sfx-{shot['id']}", "kind": "sfx", "shot": shot["id"], "start": shot["start"],
                             "duration": length, "loop": False, "gain_db": GAIN["sfx"],
                             "request": {"text": f"{shot['sound']}. Context: {shot.get('action', '')}".strip(),
                                         "duration_seconds": max(0.5, length), "prompt_influence": 0.5}})
        environments = [ref for ref in (bible or {}).get("references", []) if ref["role"] == "environment"]
        for env in environments:
            cues.append({"id": f"amb-{env['id']}", "kind": "ambience", "start": 0.0, "duration": total, "loop": True,
                         "gain_db": GAIN["ambience"],
                         "request": {"text": f"Ambient room tone and background atmosphere of {env['description']}",
                                     "duration_seconds": min(MAX_SFX, max(5.0, total)), "loop": True}})
    if not policy_off(audio.get("music")):
        cues.append({"id": "music", "kind": "music", "start": 0.0, "duration": total, "loop": False, "gain_db": GAIN["music"],
                     "request": {"prompt": f"{audio.get('music')}. Score for: {lock['logline']}",
                                 "music_length_ms": int(round(total * 1000)), "model_id": config.get("music_model", "music_v2_5"),
                                 "force_instrumental": True}})
    for cue in cues:
        seconds = cue["request"].get("duration_seconds") or cue["request"].get("music_length_ms", 0) / 1000
        rate = config["music_credits_per_second"] if cue["kind"] == "music" else config["sfx_credits_per_second"]
        cue["estimate"] = round(seconds * rate, 2)
        if cue["kind"] != "music" and config.get("sfx_model"):
            cue["request"]["model_id"] = config["sfx_model"]
    document = {"schema": "video-studio/sound-plan@1", "planned_at": now(), "cues": cues,
                "estimate": round(sum(c["estimate"] for c in cues), 2)}
    path = Path(root) / "sound/plan.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n")
    return document


def generate(root, only=None):
    project, lock, shots, config, bible = inputs(root)
    planned = json.loads((Path(root) / "sound/plan.json").read_text(encoding="utf-8"))
    placed = load(root, "sound", required=False) or {"schema": "video-studio/sound@1", "cues": [], "ducking": True,
                                                       "use_take_audio": bool(config.get("use_take_audio"))}
    done = {cue["id"] for cue in placed["cues"]}
    results = []
    for cue in planned["cues"]:
        if (only and cue["id"] not in only) or (not only and cue["id"] in done):
            continue
        decision = ledger.check(ledger.read(root), PROVIDER, cue["estimate"])
        require(decision["allowed"], decision.get("reason", ""))
        folder = Path(root) / "sound" / cue["kind"]
        folder.mkdir(parents=True, exist_ok=True)
        version = 1
        while (folder / f"{cue['id']}-v{version}.mp3").exists():
            version += 1
        target = folder / f"{cue['id']}-v{version}.mp3"
        command = ["music", "compose"] if cue["kind"] == "music" else ["text-to-sound-effects", "convert"]
        entry = ledger.record(root, PROVIDER, ".".join(command), cue["estimate"], cue["request"])
        result = subprocess.run([cli(), *command, "--json", "-", "-o", str(target)], input=json.dumps(cue["request"]),
                                capture_output=True, text=True)
        if result.returncode != 0 or not target.is_file() or target.stat().st_size == 0:
            refused = result.returncode != 0
            ledger.update(root, entry["id"], status="failed" if refused else "unknown")
            raise ContractError(f"{cue['id']} failed: {result.stderr.strip()[:300] or 'no audio written'}")
        relative = str(target.relative_to(root))
        ledger.update(root, entry["id"], status="succeeded", outputs=[relative])
        placed["cues"] = [c for c in placed["cues"] if c["id"] != cue["id"]]
        placed["cues"].append({k: cue[k] for k in ("id", "kind", "start", "duration", "loop", "gain_db")} |
                              {"shot": cue.get("shot"), "file": relative, "ledger_entry": entry["id"]})
        results.append(relative)
    placed["cues"].sort(key=lambda c: (c["start"], c["id"]))
    write(root, "sound", placed)
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan", help="Dry run: cue list, requests and estimate").add_argument("root")
    make = sub.add_parser("generate", help="Generate planned cues not yet placed (or only --cue)")
    make.add_argument("root")
    make.add_argument("--cue", action="append")
    gain = sub.add_parser("gain", help="Set a placed cue's level in dB")
    gain.add_argument("root")
    gain.add_argument("--cue", required=True)
    gain.add_argument("--db", required=True, type=float)
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            document = plan(args.root)
            decision = ledger.check(ledger.read(args.root), PROVIDER, document["estimate"])
            print(json.dumps({"cues": [{k: c[k] for k in ("id", "kind", "start", "duration", "estimate")} for c in document["cues"]],
                              "estimate": document["estimate"], "cap": decision}, indent=2))
        elif args.command == "generate":
            print(json.dumps({"generated": generate(args.root, args.cue)}, indent=2))
        else:
            placed = load(args.root, "sound")
            cue = next((c for c in placed["cues"] if c["id"] == args.cue), None)
            require(cue is not None, f"No placed cue {args.cue}")
            cue["gain_db"] = args.db
            write(args.root, "sound", placed)
            print(json.dumps(cue, indent=2))
    except (ContractError, FileNotFoundError) as error:
        print(f"sound: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
