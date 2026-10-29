"""Build, preview and run `gemini-api` CLI requests for keyframes and video takes (stdlib only).

Requests are stored with project-relative paths so their fingerprints stay
stable; the CLI command is derived from them deterministically. The CLI reads
GEMINI_API_KEY (or its own keychain/config) itself; nothing here loads `.env`.

Contract read from google-gemini/gemini-api-cli main@68ce6f1 (2026-10-28) and
prices from https://ai.google.dev/gemini-api/docs/pricing on 2026-10-29
(Standard paid tier, USD). Re-check both when the CLI or models change.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess

IMAGE_MODEL = "gemini-nano-banana-2.1"
VIDEO_MODEL = "gemini-omni-1.1-flash"
# Output price per image; input tokens are billed on top and are small for prompts and a few references.
IMAGE_PRICES = {
    "gemini-nano-banana-2.1": {"1K": 0.0336, "2K": 0.0504, "4K": 0.113},
    "gemini-3-pro-image": {"1K": 0.134, "2K": 0.134, "4K": 0.24},
    "gemini-3.1-flash-image": {"512": 0.045, "1K": 0.067, "2K": 0.101, "4K": 0.151},
    "gemini-3.1-flash-lite-image": {"1K": 0.0336},
}
# Approximate output price per second; only 720p is published for Omni.
VIDEO_PRICES = {"gemini-omni-1.1-flash": {"720p": 0.10}}
IMAGE_ASPECTS = {"1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"}
IMAGE_SIZES = {"512", "1K", "2K", "4K"}
VIDEO_ASPECTS = {"16:9", "9:16"}
VIDEO_RESOLUTIONS = {"360p", "720p", "1080p", "4k"}
VIDEO_SECONDS = (3, 10)
# Exit codes: 2 invalid usage/validation and 3 authentication fail before anything is generated.
REFUSED = {2, 3}


class GeminiError(Exception):
    """A CLI call that did not produce a result; `uncertain` means it may have been billed."""

    def __init__(self, message, uncertain=False):
        super().__init__(message)
        self.uncertain = uncertain


def cli():
    return os.environ.get("VIDEO_STUDIO_GEMINI_BIN", "gemini-api")


def image_request(model, prompt, aspect_ratio, image_size, inputs):
    return {"provider": "gemini", "tool": "gemini-api image", "model": model, "prompt": prompt,
            "aspect_ratio": aspect_ratio, "image_size": image_size, "inputs": list(inputs)}


def video_request(model, prompt, duration, aspect_ratio, resolution, start=None, end=None, references=()):
    """First/last frames bind by input order (image_to_video); otherwise images are references."""
    if start:
        inputs, task = [start] + ([end] if end else []), "image_to_video"
    elif references:
        inputs, task = list(references), "reference_to_video"
    else:
        inputs, task = [], "text_to_video"
    return {"provider": "gemini", "tool": "gemini-api video", "model": model, "prompt": prompt, "duration": duration,
            "aspect_ratio": aspect_ratio, "resolution": resolution, "task": task, "inputs": inputs}


def problems(request):
    """What the provider would reject, checked before anything is approved or spent."""
    found = []
    if request["tool"] == "gemini-api image":
        if request["aspect_ratio"] not in IMAGE_ASPECTS:
            found.append(f"aspect ratio {request['aspect_ratio']} is not offered for images")
        if request["image_size"] not in IMAGE_SIZES:
            found.append(f"image size {request['image_size']} is not one of {', '.join(sorted(IMAGE_SIZES))}")
    else:
        if request["aspect_ratio"] not in VIDEO_ASPECTS:
            found.append(f"{request['aspect_ratio']} video is not generated natively (16:9 and 9:16 only)")
        if request["resolution"] not in VIDEO_RESOLUTIONS:
            found.append(f"resolution {request['resolution']} is not one of {', '.join(sorted(VIDEO_RESOLUTIONS))}")
        low, high = VIDEO_SECONDS
        if not low <= request["duration"] <= high:
            found.append(f"{request['duration']}s is outside the {low}–{high}s a generation returns")
    return found


def estimate(request):
    """USD estimate for the request, or None when no published price covers it."""
    if request["tool"] == "gemini-api image":
        price = IMAGE_PRICES.get(request["model"], {}).get(request["image_size"])
        return price
    rate = VIDEO_PRICES.get(request["model"], {}).get(request["resolution"])
    return None if rate is None else round(rate * request["duration"], 4)


def body(request):
    if request["tool"] == "gemini-api image":
        return {"model": request["model"],
                "response_format": {"type": "image", "aspect_ratio": request["aspect_ratio"],
                                    "image_size": request["image_size"]}}
    return {"model": request["model"],
            "response_format": {"type": "video", "aspect_ratio": request["aspect_ratio"],
                                "resolution": request["resolution"], "duration": f"{request['duration']}s"},
            "generation_config": {"video_config": {"task": request["task"]}}}


def command(root, request, out=None):
    """The exact CLI arguments for a stored request; video creation returns at once with --async."""
    verb = "image" if request["tool"] == "gemini-api image" else "video"
    args = [cli(), verb, request["prompt"], "--body", json.dumps(body(request), sort_keys=True)]
    for asset in request["inputs"]:
        args += ["-i", str(Path(root) / asset)]
    args += ["--out", str(out)] if verb == "image" and out else []
    args += ["--async"] if verb == "video" else []
    return args + ["--output-format", "json", "--no-interactive"]


def resume_command(interaction_id, out):
    return [cli(), "video", "--resume", interaction_id, "--out", str(out), "--output-format", "json", "--no-interactive"]


def preview(root, request):
    """Offline check: the CLI validates flags and prints the redacted request without a network call."""
    args = command(root, request, Path(root) / ".gemini-incoming")
    missing = [asset for asset in request["inputs"] if not (Path(root) / asset).is_file()]
    result = {"command": args, "estimate_usd": estimate(request), "problems": problems(request), "missing_inputs": missing}
    if not shutil.which(args[0]):
        result["dry_run"] = f"{args[0]} is not installed; install gemini-api to validate the request offline"
        return result
    run = subprocess.run(args + ["--dry-run"], capture_output=True, text=True)
    result["dry_run"] = {"exit": run.returncode, "output": (run.stdout or run.stderr).strip()}
    return result


def invoke(args, timeout):
    if not shutil.which(args[0]):
        raise GeminiError(f"{args[0]} is not installed; see the gemini-api CLI installation instructions")
    try:
        run = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        raise GeminiError("gemini-api timed out; the request may have been accepted", uncertain=True) from error
    if run.returncode != 0:
        detail = (run.stderr or run.stdout).strip()[-800:]
        raise GeminiError(f"gemini-api exited {run.returncode}: {detail}", uncertain=run.returncode not in REFUSED)
    try:
        return json.loads(run.stdout)
    except json.JSONDecodeError as error:
        raise GeminiError(f"gemini-api returned unreadable output: {run.stdout[:200]}", uncertain=True) from error


def generate_image(root, request, folder, timeout=600):
    """Run one image request; returns (written file, response id)."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    artifact = invoke(command(root, request, folder), timeout)
    path = Path(artifact.get("path") or "")
    if not path.is_file():
        raise GeminiError(f"gemini-api reported no image file ({artifact.get('status')})", uncertain=True)
    return path, artifact.get("response_id")


def submit_video(root, request, timeout=120):
    """Create the video interaction and return its id without waiting for the render."""
    created = invoke(command(root, request), timeout)
    if not created.get("id"):
        raise GeminiError(f"gemini-api returned no interaction id: {json.dumps(created)[:200]}", uncertain=True)
    return created["id"], created.get("status")


def fetch_video(interaction_id, folder, timeout=1200):
    """Poll a known interaction (no new generation) and download the finished video."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    artifact = invoke(resume_command(interaction_id, folder), timeout)
    path = Path(artifact.get("path") or "")
    if not path.is_file():
        raise GeminiError(f"Interaction {interaction_id} ended {artifact.get('status')} without a video")
    return path
