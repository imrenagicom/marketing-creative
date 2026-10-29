# Image workflow and artifacts

Python 3.10+ and Pillow are required. No Google SDK is needed: the helper uses Gemini REST generateContent for both synchronous images and the Batch API's request format. Install [requirements.txt](../scripts/requirements.txt) in a virtual environment; never bundle that environment or credentials.

## Campaign plan

```json
{
  "schemaVersion": 1,
  "references": [
    {"path": "product.png", "role": "product"},
    {"path": "look.png", "role": "style"}
  ],
  "brief": "Verified product facts, audience, campaign objective and actual offer.",
  "style": "Brand palette, image treatment, type direction and desired feeling.",
  "grid": {"aspectRatio": "16:9"},
  "items": [
    {"id": "demo", "prompt": "A complete visual concept and composition.", "copy": "Exact approved copy", "aspectRatio": "1:1"}
  ]
}
```

Set items to the concept count needed, without a fixed nine-item requirement. The [complete campaign example](../../marketing-image-board/assets/campaign.example.json) is one possible 3×3 layout. Every item needs a unique filename-safe ID. Omit grid for automatic sheet ratio/packing, constrain only its aspectRatio, or set rows/columns explicitly. Extra trailing grid cells are blank and not cropped. Use the same saved plan for generation and splitting.

References are optional: omit references or use [] for brief-only generation. Entries can be path strings or objects with path/role; paths resolve relative to the plan. The older reference string still works for a single product image; use either reference or references. Repeated --reference /path/to/image flags override plan references, with paths relative to the current directory and default product role. Reference PNG/JPEG/WEBP files must each be under 18 MiB; total request limits still apply. At most fourteen images are accepted per request, including the selected tile (so at most thirteen other references with --tiles).

Supported sheet and final ratios are 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9, 1:4, 4:1, 1:8 and 8:1 for the default model. Other --model choices may support fewer ratios. Use separate item IDs for multiple placement variants. Each item's aspectRatio controls its final reconstruction, while grid.aspectRatio controls the whole board; equal-grid tiles inherit the cell shape.

No API key belongs in this JSON. Brand/product facts and copy are supplied by the campaign, not inferred from a fictional example.

## Setup

Set GEMINI_API_KEY in the same shell that invokes the script. The repository README recommends ~/.config/marketing-creative/.env and shows explicit export. Obtain a key through [Google AI Studio](https://aistudio.google.com/apikey), attach the intended API project/billing and confirm model access. A Gemini consumer subscription is not an API credential or a promise of API quota.

```sh
python3 -m venv /path/to/image-tools-env
/path/to/image-tools-env/bin/python -m pip install -r /path/to/marketing-image-producer/scripts/requirements.txt
```

Use that Python interpreter for generation and local splitting. Dry-run validates any supplied local references but requires no reference, key or paid call.

## Single final

```sh
python3 "$IMG_TOOL" image campaign.json --select demo --tiles /path/to/work/tiles-v1 --size 4K --out /path/to/work/final-demo-v1 --dry-run
python3 "$IMG_TOOL" image campaign.json --select demo --tiles /path/to/work/tiles-v1 --size 4K --out /path/to/work/final-demo-v1
```

Omit --tiles to work directly from the brief and any supplied references. image requires exactly one selected item (or a plan with one item). For an ad-hoc reference, add --reference /path/to/product.png; repeat the flag to supply additional images. Use the actual output filename in assets.json.

## Discounted final batch

```sh
python3 "$IMG_TOOL" batch-submit campaign.json --select demo objection action --tiles /path/to/work/tiles-v1 --size 4K --out /path/to/work/finals-v1 --dry-run
python3 "$IMG_TOOL" batch-submit campaign.json --select demo objection action --tiles /path/to/work/tiles-v1 --size 4K --out /path/to/work/finals-v1
python3 "$IMG_TOOL" batch-status /path/to/work/finals-v1
python3 "$IMG_TOOL" batch-download /path/to/work/finals-v1
```

Omitting --select means every plan item: only do so when all finals are requested. --transport auto chooses inline below an 18 MiB safety margin and uploaded JSONL otherwise. --transport file forces JSONL; --transport inline refuses oversized payloads. The local file-backed guard is 200 MiB per job, below the API's documented maximum. Split larger work into deliberate jobs.

A batch is asynchronous and discounted; it does not itself improve image quality. Higher-resolution individual regeneration and deliberate prompts provide the production-quality step. Google documents batch pricing at 50% of equivalent standard inference, with a target completion window up to 24 hours; verify current pricing before spend. Input/reference tokens, output resolution and any future tools affect total cost. The helper enables no paid search-grounding tools.

batch-status returns once. batch-download checks success, maps explicit response keys (or a fully unkeyed ordered response), saves successful images and reports item errors. Interrupted downloads can resume: existing files must match the returned image hashes and are never overwritten. Changed local files are retained and reported as errors. assets.json checkpoints progress with collectionComplete=false until collection finishes. A failed/unknown submit is not automatically repeated. Cancellation: batch-cancel JOB_DIR, then check status; it may already have completed.

Unexpected output ratios are preserved with ratioMatches=false and reviewIssues; inspect the actual dimensions before use. Requested 4K is recorded separately from actual width/height. A successful response does not establish resolution, spelling or placement readiness. Downloading again rebuilds the generated manifest; keep your review notes separately so recovery does not replace them.

## Run artifacts

- state.json: model, plan/reference/request fingerprints, operation name, transport and submission/collection state.
- requests.json: compact batch key/config map with its fingerprint; no base64 source image dump or key.
- assets.json: generated files, requested ratio/size, actual dimensions, ratio warnings, hashes, usage metadata when provided, reviewed=false and item errors.
- images/: downloaded batch finals; interactive board/final image lives at the run root.
- tiles.json and PNGs: local crop geometry and source/tile hashes from the split tool.
- review notes: which concepts were selected and which assets were actually inspected.

Keep runs outside the plugin source and release ZIP. Back up original references separately. Files API uploads can be removed through AI Studio/API when no longer needed; the state retains inputFile, but the helper does not delete remote files automatically.
