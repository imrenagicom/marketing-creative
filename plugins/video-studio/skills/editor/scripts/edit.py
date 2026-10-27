#!/usr/bin/env python3
"""Render compositions or assemble footage into versioned outputs, write captions and finish loudness (stdlib + ffmpeg)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "studio-producer/scripts"))
from craft import CAPTION_LINE  # noqa: E402
from studio import ContractError, load, require, validate  # noqa: E402

HYPERFRAMES = "npx --yes hyperframes@0.8.206"
TARGETS = {"social": (-14.0, -1.0), "podcast": (-16.0, -1.0), "broadcast": (-23.0, -1.0)}
MAX_CUE = 6.0
MIN_CUE = 0.8


def hyperframes():
    return shlex.split(os.environ.get("VIDEO_STUDIO_HYPERFRAMES", HYPERFRAMES))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def versions(root):
    folder = Path(root) / "renders"
    return sorted(int(p.name[1:]) for p in folder.glob("v*") if p.name[1:].isdigit()) if folder.exists() else []


def version_dir(root, version):
    path = Path(root) / "renders" / f"v{version}"
    require(path.is_dir(), f"No render version v{version}")
    return path


def render(root, canvases=None):
    """Render each composition into a new renders/v<N>/ directory; never overwrite earlier versions."""
    validate(root)
    project = load(root, "project")
    wanted = [f["id"] for f in project["formats"] if not canvases or f["id"] in canvases]
    require(wanted, "No matching canvas in project.json")
    version = (versions(root) or [0])[-1] + 1
    out = Path(root) / "renders" / f"v{version}"
    out.mkdir(parents=True)
    manifest = {"version": version, "renders": []}
    for canvas in wanted:
        composition = Path(root) / "compositions" / canvas
        build = composition / "build.json"
        require(build.is_file(), f"compositions/{canvas} has not been built; run motion-designer first")
        target = out / f"{canvas}.mp4"
        result = subprocess.run([*hyperframes(), "render", "-o", str(target.resolve())], cwd=composition,
                                stdin=subprocess.DEVNULL, capture_output=True, text=True)
        (out / f"{canvas}.render.log").write_text(result.stdout[-20000:] + result.stderr[-20000:])
        require(result.returncode == 0 and target.is_file(), f"Render of {canvas} failed; see renders/v{version}/{canvas}.render.log")
        built = json.loads(build.read_text())
        manifest["renders"].append({"canvas": canvas, "file": target.name, "sha256": sha(target),
                                    "composition_inputs": built.get("inputHashes"), "duration": built.get("duration"),
                                    "local_gsap": built.get("localGsap")})
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def has_audio(path):
    result = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                             "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return bool(result.stdout.strip())


def timeline_for(root, canvas, shots, takes):
    chosen = (takes.get("selected") or {}).get(canvas, {})
    by_take = {t["id"]: t for t in takes["takes"]}
    entries = []
    for shot in shots["shots"]:
        require(shot["kind"] == "camera", f"{shot['id']} is a graphic shot; footage assembly handles camera shots only")
        take_id = chosen.get(shot["id"])
        require(take_id, f"No selected clip for {shot['id']} on {canvas}; select takes after dailies first")
        entries.append({"shot": shot["id"], "take": take_id, "clip": by_take[take_id]["clips"][shot["id"]],
                        "start": shot["start"], "duration": round(shot["end"] - shot["start"], 3),
                        "transition": shot.get("transition", "cut")})
    return entries


def mix_graph(inputs, total, narration_index, cue_inputs, take_inputs, ducking):
    """Audio filter graph: speech on top, cues and take audio placed by delay, beds ducked under speech."""
    parts, beds, fx = [], [], []
    for index, cue in cue_inputs:
        delay = int(round(cue["start"] * 1000))
        chain = f"[{index}:a]atrim=duration={cue['duration']:.3f},adelay={delay}|{delay},volume={cue['gain_db']}dB[c{index}]"
        parts.append(chain)
        (beds if cue["kind"] in {"ambience", "music"} else fx).append(f"[c{index}]")
    for index, start, duration in take_inputs:
        delay = int(round(start * 1000))
        parts.append(f"[{index}:a]atrim=duration={duration:.3f},adelay={delay}|{delay}[t{index}]")
        fx.append(f"[t{index}]")
    voice = None
    if narration_index is not None:
        parts.append(f"[{narration_index}:a]asplit=2[voice][key]")
        voice = "[voice]"
    if beds:
        parts.append(f"{''.join(beds)}amix=inputs={len(beds)}:normalize=0[beds]")
        if voice and ducking:
            parts.append("[beds][key]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[ducked]")
            fx.append("[ducked]")
        else:
            fx.append("[beds]")
            if voice:
                parts.append("[key]anullsink")
    elif voice:
        parts.append("[key]anullsink")
    streams = fx + ([voice] if voice else [])
    if not streams:
        parts.append(f"anullsrc=r=48000:cl=stereo,atrim=duration={total:.3f}[aout]")
    else:
        parts.append(f"{''.join(streams)}amix=inputs={len(streams)}:normalize=0,apad,atrim=duration={total:.3f}[aout]")
    return parts


def assemble(root, canvases=None):
    """Cut selected take clips to the shot plan per canvas and mix speech, sound cues and optional take audio."""
    require(shutil.which("ffmpeg"), "assembly needs ffmpeg")
    validate(root)
    project, shots = load(root, "project"), load(root, "shots")
    takes = load(root, "takes")
    require(all("start" in shot for shot in shots["shots"]), "Time the shots first")
    sound = load(root, "sound", required=False) or {"cues": [], "ducking": True, "use_take_audio": False}
    words = load(root, "words", required=False)
    wanted = [f for f in project["formats"] if not canvases or f["id"] in canvases]
    require(wanted, "No matching canvas in project.json")
    timelines = {f["id"]: timeline_for(root, f["id"], shots, takes) for f in wanted}
    (Path(root) / "timeline.json").write_text(json.dumps({"schema": "video-studio/timeline@1", "canvases": timelines},
                                                         indent=2) + "\n")
    version = (versions(root) or [0])[-1] + 1
    out = Path(root) / "renders" / f"v{version}"
    out.mkdir(parents=True)
    manifest = {"version": version, "source": "footage", "renders": []}
    total = shots["shots"][-1]["end"]
    for fmt in wanted:
        width, height, fps = fmt["width"], fmt["height"], project["fps"]
        args, video, audio_takes = [], [], []
        for n, entry in enumerate(timelines[fmt["id"]]):
            clip = Path(root) / entry["clip"]
            args += ["-i", str(clip)]
            fade = ",fade=t=in:st=0:d=0.4" if entry["transition"] == "fade" else ""
            video.append(f"[{n}:v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},"
                         f"fps={fps},setsar=1,tpad=stop_mode=clone:stop_duration={entry['duration']:.3f},"
                         f"trim=duration={entry['duration']:.3f},setpts=PTS-STARTPTS{fade}[v{n}]")
            if sound.get("use_take_audio") and has_audio(clip):
                audio_takes.append((n, entry["start"], entry["duration"]))
        count = len(timelines[fmt["id"]])
        video.append("".join(f"[v{n}]" for n in range(count)) + f"concat=n={count}:v=1:a=0[vout]")
        index = count
        narration_index = None
        if words and (Path(root) / words["audio"]).is_file():
            args += ["-i", str(Path(root) / words["audio"])]
            narration_index, index = index, index + 1
        cue_inputs = []
        for cue in sound["cues"]:
            args += (["-stream_loop", "-1"] if cue.get("loop") else []) + ["-i", str(Path(root) / cue["file"])]
            cue_inputs.append((index, cue))
            index += 1
        graph = video + mix_graph(args, total, narration_index, cue_inputs, audio_takes, sound.get("ducking", True))
        target = out / f"{fmt['id']}.mp4"
        command = ["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", ";".join(graph), "-map", "[vout]",
                   "-map", "[aout]", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                   "-r", str(fps), "-c:a", "aac", "-ar", "48000", "-b:a", "192k", "-t", f"{total:.3f}",
                   "-movflags", "+faststart", str(target)]
        result = subprocess.run(command, capture_output=True, text=True)
        (out / f"{fmt['id']}.assemble.log").write_text(" ".join(command) + "\n\n" + result.stderr[-20000:])
        require(result.returncode == 0, f"Assembly of {fmt['id']} failed; see renders/v{version}/{fmt['id']}.assemble.log")
        manifest["renders"].append({"canvas": fmt["id"], "file": target.name, "sha256": sha(target), "duration": total,
                                    "clips": [e["clip"] for e in timelines[fmt["id"]]],
                                    "audio": {"narration": narration_index is not None, "cues": len(cue_inputs),
                                              "take_audio": bool(audio_takes)}})
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def cues(words, language, max_chars=None):
    """Group timed words into caption cues: at most two lines, broken at script lines and punctuation."""
    limit = max_chars or CAPTION_LINE[language]
    result, current = [], []

    def flush():
        if current:
            text = " ".join(w["text"] for w in current)
            result.append({"start": current[0]["start"], "end": current[-1]["end"], "text": wrap(text, limit)})
            current.clear()

    for word in words:
        if current:
            candidate = " ".join(w["text"] for w in current + [word])
            new_line = word["line"] != current[-1]["line"]
            too_long = len(candidate) > 2 * limit or word["end"] - current[0]["start"] > MAX_CUE
            if new_line or too_long:
                flush()
        current.append(word)
        if re.search(r"[.!?…]$", word["text"]) and word["end"] - current[0]["start"] >= MIN_CUE:
            flush()
    flush()
    for before, after in zip(result, result[1:]):
        if before["end"] - before["start"] < MIN_CUE:
            before["end"] = min(after["start"], before["start"] + MIN_CUE)
    return result


def wrap(text, limit):
    if len(text) <= limit:
        return text
    words = text.split()
    best = min(range(1, len(words)), key=lambda i: abs(len(" ".join(words[:i])) - len(" ".join(words[i:]))))
    return " ".join(words[:best]) + "\n" + " ".join(words[best:])


def stamp(seconds, separator):
    millis = round(seconds * 1000)
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{millis:03d}"


def captions(root):
    words = load(root, "words")
    validate(root)
    items = cues(words["words"], words["language"])
    folder = Path(root) / "captions"
    folder.mkdir(exist_ok=True)
    srt = "\n".join(f"{n}\n{stamp(c['start'], ',')} --> {stamp(c['end'], ',')}\n{c['text']}\n"
                    for n, c in enumerate(items, 1))
    vtt = "WEBVTT\n\n" + "\n".join(f"{stamp(c['start'], '.')} --> {stamp(c['end'], '.')}\n{c['text']}\n" for c in items)
    (folder / f"{words['language']}.srt").write_text(srt, encoding="utf-8")
    (folder / f"{words['language']}.vtt").write_text(vtt, encoding="utf-8")
    return {"cues": len(items), "files": [f"captions/{words['language']}.srt", f"captions/{words['language']}.vtt"]}


def measure(path):
    """Integrated loudness, true peak and range via ffmpeg loudnorm analysis."""
    result = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
                             "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    match = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", result.stderr)
    require(match, f"Could not measure loudness of {path}")
    return json.loads(match.group(0))


def has_filter(name):
    result = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True)
    return any(line.split()[1:2] == [name] for line in result.stdout.splitlines() if line.strip())


def finish(root, version, target="social", burn=False):
    """Normalize loudness (two-pass) and optionally burn captions into delivery copies."""
    require(shutil.which("ffmpeg"), "finishing needs ffmpeg")
    integrated, peak = TARGETS[target]
    folder = version_dir(root, version)
    manifest = json.loads((folder / "manifest.json").read_text())
    delivery = folder / "delivery"
    delivery.mkdir(exist_ok=True)
    words = load(root, "words", required=False)
    subtitle = Path(root) / "captions" / f"{words['language']}.srt" if words else None
    if burn:
        require(subtitle is not None and subtitle.is_file(), "Write captions before burning them in")
        require(has_filter("subtitles"), "This ffmpeg has no subtitles filter (built without libass); install an ffmpeg "
                                         "with libass or deliver the captions as a sidecar file instead")
    results = []
    for item in manifest["renders"]:
        source = folder / item["file"]
        first = measure(source)
        loudnorm = (f"loudnorm=I={integrated}:TP={peak}:LRA=11:measured_I={first['input_i']}:"
                    f"measured_TP={first['input_tp']}:measured_LRA={first['input_lra']}:"
                    f"measured_thresh={first['input_thresh']}:offset={first['target_offset']}:linear=true")
        output = delivery / item["file"]
        command = ["ffmpeg", "-v", "error", "-y", "-i", str(source), "-af", loudnorm, "-ar", "48000", "-c:a", "aac", "-b:a", "192k"]
        if burn:
            escaped = str(subtitle.resolve()).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
            command += ["-vf", f"subtitles='{escaped}'", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p"]
        else:
            command += ["-c:v", "copy"]
        command += ["-movflags", "+faststart", str(output)]
        subprocess.run(command, check=True)
        after = measure(output)
        results.append({"canvas": item["canvas"], "file": f"delivery/{item['file']}", "target": target,
                        "target_lufs": integrated, "target_true_peak": peak,
                        "measured_lufs": float(after["input_i"]), "measured_true_peak": float(after["input_tp"]),
                        "captions_burned": burn, "sha256": sha(output)})
    manifest["delivery"] = results
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    draw = sub.add_parser("render", help="Render compositions into a new renders/v<N>/")
    draw.add_argument("root")
    draw.add_argument("--canvas", action="append", help="Limit to a canvas (repeatable)")
    cut = sub.add_parser("assemble", help="Assemble selected footage clips and the sound mix into a new renders/v<N>/")
    cut.add_argument("root")
    cut.add_argument("--canvas", action="append", help="Limit to a canvas (repeatable)")
    text = sub.add_parser("captions", help="Write SRT and VTT captions from word timings")
    text.add_argument("root")
    done = sub.add_parser("finish", help="Loudness-normalize (and optionally burn captions) into delivery/")
    done.add_argument("root")
    done.add_argument("--version", type=int, help="Render version (default: latest)")
    done.add_argument("--target", choices=sorted(TARGETS), default="social")
    done.add_argument("--burn-captions", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "render":
            print(json.dumps(render(args.root, args.canvas), indent=2))
        elif args.command == "assemble":
            print(json.dumps(assemble(args.root, args.canvas), indent=2))
        elif args.command == "captions":
            print(json.dumps(captions(args.root), indent=2))
        else:
            version = args.version or (versions(args.root) or [None])[-1]
            require(version, "Nothing rendered yet")
            print(json.dumps(finish(args.root, version, args.target, args.burn_captions), indent=2))
    except (ContractError, subprocess.CalledProcessError) as error:
        print(f"edit: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
