#!/usr/bin/env python3
"""Measure a reference video: cuts, shot lengths, frames per shot, audio level and silences (stdlib + ffmpeg).

The numbers and frames are evidence for a techniques report; they are not the
report. Optional transcription uses the ElevenLabs CLI under the project's cap.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "studio-producer/scripts"))
import ledger  # noqa: E402
from studio import ContractError, now, require  # noqa: E402

MAX_FRAMES = 60


def run(args):
    return subprocess.run(args, capture_output=True, text=True)


def probe(path):
    result = run(["ffprobe", "-v", "error", "-show_entries",
                  "stream=codec_type,codec_name,width,height,r_frame_rate:format=duration,bit_rate", "-of", "json", str(path)])
    require(result.returncode == 0, f"ffprobe could not read {path}")
    data = json.loads(result.stdout)
    video = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    audio = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    require(video is not None, "The reference has no video stream")
    num, den = (video["r_frame_rate"].split("/") + ["1"])[:2]
    width, height = video["width"], video["height"]
    return {"duration": round(float(data["format"]["duration"]), 3), "width": width, "height": height,
            "aspect": f"{width}:{height}", "orientation": "vertical" if height > width else "horizontal" if width > height else "square",
            "fps": round(int(num) / int(den), 3), "video_codec": video.get("codec_name"),
            "audio_codec": audio and audio.get("codec_name"), "has_audio": audio is not None}


def cuts(path, threshold):
    """Scene-change timestamps from ffmpeg's scene score."""
    result = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-an", "-vf",
                  f"select='gt(scene,{threshold})',showinfo", "-f", "null", "-"])
    return sorted({round(float(t), 3) for t in re.findall(r"pts_time:([\d.]+)", result.stderr)})


def shots_from(cut_times, duration, min_length=0.25):
    bounds = [0.0] + [t for t in cut_times if 0 < t < duration] + [duration]
    shots, start = [], bounds[0]
    for end in bounds[1:]:
        if end - start >= min_length:
            shots.append({"id": f"R{len(shots) + 1:02d}", "start": round(start, 3), "end": round(end, 3),
                          "length": round(end - start, 3)})
            start = end
        elif shots:
            shots[-1]["end"] = round(end, 3)
            shots[-1]["length"] = round(end - shots[-1]["start"], 3)
            start = end
    return shots


def audio_stats(path):
    loud = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "loudnorm=print_format=json", "-f", "null", "-"])
    match = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", loud.stderr)
    silence = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", "silencedetect=n=-40dB:d=0.4", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", silence.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", silence.stderr)]
    values = json.loads(match.group(0)) if match else {}
    return {"integrated_lufs": float(values["input_i"]) if values else None,
            "true_peak": float(values["input_tp"]) if values else None,
            "silences": [{"start": round(a, 3), "end": round(b, 3) if b is not None else None}
                         for a, b in zip(starts, ends + [None] * (len(starts) - len(ends)))]}


def frames(path, shots, folder):
    folder.mkdir(parents=True, exist_ok=True)
    step = max(1, -(-len(shots) // MAX_FRAMES))
    written = []
    for shot in shots[::step]:
        target = folder / f"{shot['id']}.png"
        middle = (shot["start"] + shot["end"]) / 2
        result = run(["ffmpeg", "-v", "error", "-y", "-ss", f"{middle:.3f}", "-i", str(path), "-frames:v", "1",
                      "-vf", "scale=480:-2", str(target)])
        if result.returncode == 0 and target.exists():
            shot["frame"] = f"frames/{target.name}"
            written.append(target)
    return written


def contact_sheet(images, target, columns=6):
    if not images:
        return None
    listing = target.parent / "sheet-inputs.txt"
    listing.write_text("".join(f"file '{p.resolve()}'\nduration 1\n" for p in images))
    rows = -(-len(images) // columns)
    result = run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-vf",
                  f"scale=320:-2,tile={columns}x{rows}:padding=4:color=black", "-frames:v", "1", str(target)])
    listing.unlink()
    return target.name if result.returncode == 0 else None


def transcribe(path, project, estimate, language):
    """Paid: word-level transcript through the ElevenLabs CLI, under the project's cap."""
    decision = ledger.check(ledger.read(project), "elevenlabs", estimate)
    require(decision["allowed"], decision.get("reason", ""))
    request = {"file": Path(path).name, "model_id": "scribe_v2", "language_code": language}
    entry = ledger.record(project, "elevenlabs", "speech-to-text.convert", estimate, request)
    args = [os.environ.get("VIDEO_STUDIO_ELEVENLABS_BIN", "elevenlabs"), "speech-to-text", "convert", "--file", str(path),
            "--model-id", "scribe_v2", "--timestamps-granularity", "word", "--tag-audio-events", "true", "--format", "json"]
    if language:
        args += ["--language-code", language]
    result = run(args)
    if result.returncode != 0:
        ledger.update(project, entry["id"], status="failed")
        raise ContractError(f"Transcription failed: {result.stderr.strip()[:300]}")
    ledger.update(project, entry["id"], status="succeeded")
    return json.loads(result.stdout)


def analyze(video, out, threshold=0.3, project=None, transcribe_estimate=None, language=None):
    require(shutil.which("ffmpeg") and shutil.which("ffprobe"), "reference analysis needs ffmpeg and ffprobe")
    video = Path(video).resolve()
    require(video.is_file(), f"No video at {video}")
    out = Path(out)
    require(not (out / "analysis.json").exists(), f"{out}/analysis.json exists; analyse into a new directory")
    out.mkdir(parents=True, exist_ok=True)
    meta = probe(video)
    found = cuts(video, threshold)
    shots = shots_from(found, meta["duration"])
    lengths = [s["length"] for s in shots]
    pacing = {"shots": len(shots), "average_shot_length": round(sum(lengths) / len(lengths), 3),
              "shortest": min(lengths), "longest": max(lengths),
              "cuts_per_minute": round(len(shots) / meta["duration"] * 60, 1),
              "cuts_in_first_3s": sum(1 for t in found if t <= 3.0)}
    images = frames(video, shots, out / "frames")
    sheet = contact_sheet(images, out / "contact-sheet.png")
    analysis = {"schema": "video-studio/reference-analysis@1", "source": video.name, "analysed_at": now(),
                "scene_threshold": threshold, "metadata": meta, "pacing": pacing, "shots": shots,
                "audio": audio_stats(video) if meta["has_audio"] else None, "contact_sheet": sheet,
                "note": "Cut detection misses dissolves and fast whip-pans and can split on flashes; check the frames."}
    if transcribe_estimate is not None:
        require(project, "Transcription needs --project for the ElevenLabs cap")
        transcript = transcribe(video, project, transcribe_estimate, language)
        (out / "transcript.json").write_text(json.dumps(transcript, indent=2, ensure_ascii=False) + "\n")
        analysis["transcript"] = "transcript.json"
    (out / "analysis.json").write_text(json.dumps(analysis, indent=2, ensure_ascii=False) + "\n")
    return analysis


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("video")
    parser.add_argument("--out", required=True, help="New directory, e.g. <project>/references/<name>")
    parser.add_argument("--threshold", type=float, default=0.3, help="Scene score for a cut (0.2 sensitive, 0.4 strict)")
    parser.add_argument("--transcribe-estimate", type=float, help="Paid: transcribe with ElevenLabs at this credit estimate")
    parser.add_argument("--project", help="Project directory whose ElevenLabs cap covers transcription")
    parser.add_argument("--language", choices=["en", "id"])
    args = parser.parse_args(argv)
    try:
        result = analyze(args.video, args.out, args.threshold, args.project, args.transcribe_estimate, args.language)
    except ContractError as error:
        print(f"analyze: {error}", file=sys.stderr)
        return 1
    print(json.dumps({"out": args.out, "pacing": result["pacing"], "metadata": result["metadata"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
