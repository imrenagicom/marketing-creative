# Board workflow

The single-call board exchanges per-asset resolution and isolation for fewer generated output images. It is an ideation technique, not a guaranteed ninefold cost reduction.

## Inputs

A factual marketing brief, visual direction and ordered item descriptions, with zero or more optional PNG/JPEG/WEBP references. Give each reference a role such as product, style, logo or character. Use exact approved copy; omit unsupported offers and numbers. A supplied user image can ground several ad concepts without inventing product features.

Choose the concept count for the task (the helper supports 1..100), balancing variety against pixels per tile. All concepts can share the supplied identity but have different composition, persuasive mechanisms and copy. For a carousel, continuity and slide order replace alternative-concept variety.

Choose grid rows/columns in 1..10 and a supported sheet ratio; 3×3 is only an example. A 2×3 landscape sheet provides six cells, while a 3×2 portrait sheet provides six taller previews. Items fill cells in reading order, left-to-right and top-to-bottom. An incomplete last row is allowed: trailing empty cells are excluded from crops. The grid must have at least as many cells as concepts.

Omit grid dimensions to let the shared helper choose packing based on item count, intended asset ratios, empty space and readability. Set only grid.aspectRatio to constrain the sheet ratio while selecting dimensions automatically; omit grid entirely to select both. Dry-run prints the resolved grid. The splitter uses the same calculation with --plan, so generation and cropping agree. Preserve the plan version used for generation; changing concept count, ordering or ratios before cropping can change automatic packing.

## Commands

Set IMG_TOOL to the installed marketing-image-producer/scripts/gemini_images.py path and SPLIT_TOOL to this skill's scripts/split_board.py. See [setup and plan contract](../../marketing-image-producer/references/image-workflow.md).

```sh
python3 "$IMG_TOOL" board campaign.json --out /path/to/work/board-v1 --dry-run
python3 "$IMG_TOOL" board campaign.json --out /path/to/work/board-v1
python3 "$SPLIT_TOOL" /path/to/work/board-v1/board.png --plan campaign.json --out /path/to/work/tiles-v1
```

Use the actual returned image extension from assets.json (PNG/JPEG/WEBP), not an assumed PNG. No output directory is created by dry-run. An actual run needs a new output directory; preserve prior versions.

Optional --inset trims pixels inside every crop to remove fine separators. For irregular model placement, --boxes accepts a JSON list of measured [left,top,right,bottom] pixel rectangles in the same reading order. The tool applies EXIF orientation before measuring; use the displayed orientation. Crops are PNG with no resizing and preserve RGB/alpha pixels, including palette transparency. Integer partitioning accounts for every pixel when dimensions are not divisible by three; tile sizes can differ by one pixel.

A rectangular grid changes cell ratio: cell aspect = sheet aspect × rows / columns. Choose the sheet/grid combination deliberately; a sheet ratio and an asset ratio are different settings. Equal-grid previews have one cell shape, even when concepts target different final ratios. Regenerate selected assets at each item's intended ratio instead of distorting the preview. For irregular rectangles in the returned board, --boxes supplies a separately measured crop per concept.

## Review limits

Pixel geometry can be checked mechanically; cell composition cannot. Check the model did not add gutters, board labels or cross-cell elements. Include exact dimensions and concept IDs with review notes. The original board, tiles.json and tile hashes give traceability; they do not prove correct spelling or publication readiness.
