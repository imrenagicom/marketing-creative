#!/usr/bin/env python3
"""Generate or align narration with the ElevenLabs CLI and write word timings (stdlib + ffmpeg).

Every paid call is checked against the project's approved ElevenLabs cap and
recorded in the ledger before it is sent. `plan` is the dry run.
"""
import argparse
import base64
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "studio-producer/scripts"))
import ledger  # noqa: E402
from craft import spoken  # noqa: E402
from studio import (ContractError, load, require, validate_lock, validate_project,  # noqa: E402
                    validate_script, validate_words, write)

PROVIDER = "elevenlabs"
MODES = {"single", "lines"}


class ProviderError(ContractError):
    """The CLI ran and the provider refused the request."""


def cli():
    return os.environ.get("VIDEO_STUDIO_ELEVENLABS_BIN", "elevenlabs")


def inputs(root):
    project, lock, script = load(root, "project"), load(root, "lock"), load(root, "script")
    validate_project(project)
    validate_lock(lock)
    validate_script(script, project, lock)
    config = load(root, "voice_config")
    require(config.get("schema") == "video-studio/voice-config@1", "voice-config.json must declare video-studio/voice-config@1")
    require(config.get("mode", "single") in MODES, "voice-config mode must be single or lines")
    require(isinstance(config.get("credits_per_char"), (int, float)) and config["credits_per_char"] > 0,
            "voice-config needs credits_per_char (check the current rate and record rate_checked)")
    speakers = {line["speaker"] for line in script["lines"]}
    for speaker in speakers:
        require((config.get("voices", {}).get(speaker) or {}).get("voice_id"), f"No voice_id configured for speaker {speaker}")
    if config.get("mode", "single") == "single":
        require(len(speakers) == 1, "single mode needs one speaker; use lines mode for several speakers")
    return project, script, config


def requests(script, config):
    """The exact provider requests a generation would send."""
    def body(text, speaker, previous=None, following=None):
        voice = config["voices"][speaker]
        request = {"text": text, "model_id": config.get("model_id", "eleven_v4"), "language_code": script["language"]}
        for key in ("voice_settings", "seed", "pronunciation_dictionary_locators"):
            value = voice.get(key, config.get(key))
            if value is not None:
                request[key] = value
        if previous:
            request["previous_text"] = previous
        if following:
            request["next_text"] = following
        # output_format is a query parameter, so it travels as a CLI flag, not in the body.
        return {"voice_id": voice["voice_id"], "output_format": config.get("output_format", "mp3_44100_128"),
                "lines": [], "body": request}

    lines = script["lines"]
    if config.get("mode", "single") == "single":
        item = body("\n\n".join(line["text"] for line in lines), lines[0]["speaker"])
        item["lines"] = [line["id"] for line in lines]
        return [item]
    result = []
    for index, line in enumerate(lines):
        previous = lines[index - 1]["text"] if index else None
        following = lines[index + 1]["text"] if index + 1 < len(lines) else None
        item = body(line["text"], line["speaker"], spoken(previous) if previous else None,
                    spoken(following) if following else None)
        item["lines"] = [line["id"]]
        result.append(item)
    return result


def estimate(items, config):
    return round(sum(len(item["body"]["text"]) for item in items) * config["credits_per_char"], 2)


def char_words(alignment):
    """Group character timings into words, dropping [audio tags] and whitespace."""
    words, current, depth = [], None, 0
    for char, start, end in zip(alignment["characters"], alignment["character_start_times_seconds"],
                                alignment["character_end_times_seconds"]):
        if char == "[":
            depth += 1
        if depth or char.isspace():
            if current:
                words.append(current)
                current = None
            if char == "]" and depth:
                depth -= 1
            continue
        if current is None:
            current = {"text": char, "start": start, "end": end}
        else:
            current["text"] += char
            current["end"] = end
    if current:
        words.append(current)
    return words


def assign_lines(words, script, line_ids, offset=0.0):
    """Attach line ids by spoken word counts; refuse when the counts disagree."""
    lines = {line["id"]: line for line in script["lines"]}
    expected = [(line_id, token) for line_id in line_ids for token in spoken(lines[line_id]["text"]).split()]
    require(len(expected) == len(words),
            f"Alignment has {len(words)} words but the script lines have {len(expected)}; inspect the take before using it")
    return [{"text": word["text"], "start": round(word["start"] + offset, 3), "end": round(word["end"] + offset, 3),
             "line": line_id} for word, (line_id, _) in zip(words, expected)]


def probe_duration(path):
    if not shutil.which("ffprobe"):
        return None
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                            capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except ValueError:
        return None


def call(args, stdin=None):
    result = subprocess.run([cli(), *args], input=stdin, capture_output=True, text=True)
    if result.returncode != 0:
        raise ProviderError(f"ElevenLabs CLI failed ({result.returncode}): {result.stderr.strip()[:400]}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise ContractError("ElevenLabs CLI returned non-JSON output") from error


def new_take(root):
    takes = Path(root) / "voice/takes"
    takes.mkdir(parents=True, exist_ok=True)
    take_id = "T" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M%S%f")
    (takes / take_id).mkdir()
    return take_id, takes / take_id


def concat(parts, gap, output):
    """Join per-line audio with silence gaps into one take (ffmpeg)."""
    require(shutil.which("ffmpeg"), "lines mode needs ffmpeg to join the line takes")
    with tempfile.TemporaryDirectory() as temp:
        silence = Path(temp) / "gap.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", str(gap),
                        str(silence)], check=True)
        listing = Path(temp) / "list.txt"
        entries = []
        for index, part in enumerate(parts):
            wav = Path(temp) / f"part{index}.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-i", str(part), "-ar", "44100", "-ac", "1", str(wav)], check=True)
            entries.append(f"file '{wav}'")
            if index + 1 < len(parts):
                entries.append(f"file '{silence}'")
        listing.write_text("\n".join(entries) + "\n")
        subprocess.run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
                        "-c:a", "libmp3lame", "-q:a", "2", str(output)], check=True)


def generate(root, take_note=""):
    project, script, config = inputs(root)
    items = requests(script, config)
    cost = estimate(items, config)
    decision = ledger.check(ledger.read(root), PROVIDER, cost)
    require(decision["allowed"], decision.get("reason", ""))
    take_id, folder = new_take(root)
    entry = ledger.record(root, PROVIDER, "text-to-speech.convert_with_timestamps", cost,
                          {"requests": items}, entry_id=f"elevenlabs-{take_id}")
    words, parts, offset = [], [], 0.0
    gap = float(config.get("line_gap", 0.35))
    try:
        for index, item in enumerate(items):
            response = call(["text-to-speech", "convert_with_timestamps", "--voice-id", item["voice_id"],
                             "--output-format", item["output_format"], "--json", "-", "--format", "json",
                             "--no-extract"], json.dumps(item["body"]))
            require(response.get("audio_base64") and response.get("alignment"), "Response lacks audio or alignment")
            audio = folder / (f"line-{index:03d}.mp3" if len(items) > 1 else "narration.mp3")
            audio.write_bytes(base64.b64decode(response["audio_base64"]))
            (folder / f"alignment-{index:03d}.json").write_text(
                json.dumps({k: v for k, v in response.items() if k != "audio_base64"}, ensure_ascii=False))
            line_words = assign_lines(char_words(response["alignment"]), script, item["lines"], offset)
            words.extend(line_words)
            parts.append(audio)
            length = probe_duration(audio) or response["alignment"]["character_end_times_seconds"][-1]
            offset += length + gap
    except Exception as error:
        # A clean refusal before any audio arrived spent nothing; anything else may have
        # been billed, so it stays counted as unknown and is never resubmitted automatically.
        refused = isinstance(error, ProviderError) and not parts
        ledger.update(root, entry["id"], status="failed" if refused else "unknown")
        raise
    if len(parts) > 1:
        narration = folder / "narration.mp3"
        concat(parts, gap, narration)
    else:
        narration = parts[0]
    duration = probe_duration(narration) or words[-1]["end"]
    result = {"schema": "video-studio/words@1", "audio": str(narration.relative_to(root)), "duration": round(duration, 3),
              "language": script["language"], "source": "elevenlabs-tts", "take": take_id, "note": take_note, "words": words}
    validate_words(result, script)
    (folder / "words.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    ledger.update(root, entry["id"], status="succeeded", outputs=[result["audio"]])
    if load(root, "words", required=False) is None:
        write(root, "words", result)
    return result


def align(root, audio, estimate_credits):
    """Forced-align a supplied recording against the script (paid; counts against the cap)."""
    project, lock, script = load(root, "project"), load(root, "lock"), load(root, "script")
    validate_project(project)
    validate_lock(lock)
    validate_script(script, project, lock)
    source = Path(audio).resolve()
    require(source.is_file(), f"No audio file at {audio}")
    transcript = " ".join(spoken(line["text"]) for line in script["lines"])
    decision = ledger.check(ledger.read(root), PROVIDER, estimate_credits)
    require(decision["allowed"], decision.get("reason", ""))
    take_id, folder = new_take(root)
    copy = folder / ("supplied" + source.suffix)
    shutil.copy2(source, copy)
    entry = ledger.record(root, PROVIDER, "forced-alignment.create", estimate_credits,
                          {"audio_sha256": hashlib.sha256(copy.read_bytes()).hexdigest(), "text": transcript},
                          entry_id=f"elevenlabs-{take_id}")
    try:
        response = call(["forced-alignment", "create", "--file", str(copy), "--text", transcript, "--format", "json"])
    except Exception as error:
        ledger.update(root, entry["id"], status="failed" if isinstance(error, ProviderError) else "unknown")
        raise
    (folder / "alignment.json").write_text(json.dumps(response, ensure_ascii=False))
    raw = [{"text": w["text"], "start": w["start"], "end": w["end"]} for w in response.get("words", []) if w["text"].strip()]
    words = assign_lines(raw, script, [line["id"] for line in script["lines"]])
    duration = probe_duration(copy) or words[-1]["end"]
    result = {"schema": "video-studio/words@1", "audio": str(copy.relative_to(root)), "duration": round(duration, 3),
              "language": script["language"], "source": "forced-alignment", "take": take_id, "words": words}
    validate_words(result, script)
    (folder / "words.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    ledger.update(root, entry["id"], status="succeeded", outputs=[result["audio"]])
    write(root, "words", result)
    return result


def select(root, take_id):
    script = load(root, "script")
    path = Path(root) / "voice/takes" / take_id / "words.json"
    require(path.is_file(), f"No words.json for take {take_id}")
    words = json.loads(path.read_text(encoding="utf-8"))
    validate_words(words, script)
    write(root, "words", words)
    return words


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "generate"):
        command = sub.add_parser(name)
        command.add_argument("root")
        if name == "generate":
            command.add_argument("--note", default="", help="Why this take exists (retake reason)")
    aligner = sub.add_parser("align", help="Align supplied narration to the script")
    aligner.add_argument("root")
    aligner.add_argument("--audio", required=True)
    aligner.add_argument("--estimate", required=True, type=float, help="Credits, from the current alignment rate")
    chooser = sub.add_parser("select", help="Use a take's timings as voice/words.json")
    chooser.add_argument("root")
    chooser.add_argument("--take", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            _, script, config = inputs(args.root)
            items = requests(script, config)
            cost = estimate(items, config)
            decision = ledger.check(ledger.read(args.root), PROVIDER, cost)
            print(json.dumps({"requests": items, "characters": sum(len(i["body"]["text"]) for i in items),
                              "estimate": cost, "cap": decision}, indent=2, ensure_ascii=False))
        elif args.command == "generate":
            result = generate(args.root, args.note)
            print(json.dumps({"take": result["take"], "audio": result["audio"], "duration": result["duration"],
                              "words": len(result["words"])}))
        elif args.command == "align":
            result = align(args.root, args.audio, args.estimate)
            print(json.dumps({"take": result["take"], "duration": result["duration"], "words": len(result["words"])}))
        else:
            result = select(args.root, args.take)
            print(json.dumps({"selected": args.take, "duration": result["duration"]}))
    except (ContractError, subprocess.CalledProcessError) as error:
        print(f"voice: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
