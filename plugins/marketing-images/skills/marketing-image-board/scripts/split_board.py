#!/usr/bin/env python3
"""Split a generated contact sheet locally; no Gemini calls or resampling."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

RATIOS = {"1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9",
          "1:4", "4:1", "1:8", "8:1"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def image_tools():
    try:
        from PIL import Image, ImageOps
    except ImportError:
        raise ValueError("Install Pillow using the image producer's scripts/requirements.txt") from None
    return Image, ImageOps


def resolve_grid(plan):
    """Use the same deterministic packing for generation and subsequent crops."""
    items=plan.get("items",[])
    count=len(items)
    require(1<=count<=100,"Board needs 1..100 concepts")
    grid=plan.get("grid",{})
    require(isinstance(grid,dict),"Grid must be an object")
    for field in ("rows","columns"):
        if field in grid:
            require(type(grid[field]) is int and 1<=grid[field]<=10,"Invalid grid dimensions")
    ratio=grid.get("aspectRatio")
    require(ratio is None or ratio in RATIOS,"Unsupported board aspect ratio")
    def numeric(value):
        w,h=map(int,value.split(":"))
        return w/h
    require(all(item.get("aspectRatio","1:1") in RATIOS for item in items),"Unsupported item aspect ratio")
    targets=[numeric(item.get("aspectRatio","1:1")) for item in items]
    target=math.exp(sum(math.log(value) for value in targets)/count)
    # Prefer useful cell framing, little empty space, and a readable sheet shape.
    candidates=[]
    for rows in ([grid["rows"]] if "rows" in grid else range(1,11)):
        for columns in ([grid["columns"]] if "columns" in grid else range(1,11)):
            if rows*columns<count:
                continue
            for sheet in ([ratio] if ratio else sorted(RATIOS-{"1:4","4:1","1:8","8:1"})):
                aspect=numeric(sheet)
                score=abs(math.log(aspect*rows/columns/target))+.35*(rows*columns-count)/count+.08*abs(math.log(aspect))+.01*max(rows,columns)
                candidates.append((score,rows*columns,rows,columns,sheet))
    require(candidates,"Board grid has fewer cells than concepts")
    _,_,rows,columns,ratio=min(candidates)
    return {"rows":rows,"columns":columns,"aspectRatio":ratio}


def split(source, output, rows=3, columns=3, ids=None, inset=0, boxes=None):
    require(type(rows) is int and 1 <= rows <= 10 and type(columns) is int and 1 <= columns <= 10,
            "Rows/columns must be integers in 1..10")
    require(isinstance(inset, int) and inset >= 0, "Inset must be a nonnegative integer")
    ids = ids or [f"tile-{i+1:02d}" for i in range(rows * columns)]
    require(1 <= len(ids) <= rows * columns and len(set(ids)) == len(ids), "Grid needs one unique ID per occupied tile")
    require(all(isinstance(i, str) and re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_-]*", i) for i in ids), "Invalid tile ID")
    Image, ImageOps = image_tools()
    source, requested = Path(source).resolve(), Path(output).expanduser()
    require(not requested.is_symlink(), "Refusing symlink output directory")
    output = requested.resolve()
    require(not output.exists(), "Output directory already exists; choose a new version")
    with Image.open(source) as opened:
        require(opened.format in ("PNG", "JPEG", "WEBP"), "Supported board formats: PNG, JPEG, WEBP")
        image = ImageOps.exif_transpose(opened)
        # Preserve transparent reference pixels, including palette transparency.
        image = image.convert("RGBA" if "A" in image.getbands() or "transparency" in image.info else "RGB")
        width, height = image.size
        require(width >= columns and height >= rows, "Board is smaller than its grid")
        if boxes is None:
            boxes = [(c*width//columns, r*height//rows, (c+1)*width//columns, (r+1)*height//rows)
                     for r in range(rows) for c in range(columns)][:len(ids)]
        require(len(boxes) == len(ids), "Measured boxes must match tile count")
        checked = []
        for box in boxes:
            require(len(box) == 4 and all(isinstance(n, int) and not isinstance(n, bool) for n in box), "Boxes use integer [left,top,right,bottom]")
            left, top, right, bottom = box
            require(0 <= left < right <= width and 0 <= top < bottom <= height, "Crop box outside board")
            crop = (left+inset, top+inset, right-inset, bottom-inset)
            require(crop[0] < crop[2] and crop[1] < crop[3], "Inset removes the whole tile")
            checked.append(crop)
        output.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".tiles-", dir=output.parent))
        try:
            tiles = []
            for index, (item, box) in enumerate(zip(ids, checked)):
                tile = image.crop(box)
                file = staging / f"{item}.png"
                tile.save(file)
                tiles.append({"id": item, "index": index, "row": index//columns, "column": index%columns,
                              "path": file.name, "box": list(box), "width": tile.width, "height": tile.height,
                              "sha256": hashlib.sha256(file.read_bytes()).hexdigest(), "reviewed": False})
            manifest = {"schemaVersion": 1, "sourceSha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                        "sourceWidth": width, "sourceHeight": height, "rows": rows, "columns": columns,
                        "unusedCells":rows*columns-len(ids),
                        "inset": inset, "geometry": "measured" if boxes != [(c*width//columns, r*height//rows, (c+1)*width//columns, (r+1)*height//rows) for r in range(rows) for c in range(columns)][:len(ids)] else "equal-grid",
                        "purpose": "ideation previews, not automatically final assets", "tiles": tiles}
            (staging / "tiles.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
            # Never merge/overwrite another split directory.
            require(not output.exists(), "Output appeared during splitting; refusing overwrite")
            os.rename(staging, output)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image")
    parser.add_argument("--out", required=True)
    parser.add_argument("--rows", type=int, default=3)
    parser.add_argument("--columns", type=int, default=3)
    parser.add_argument("--plan", help="Use item IDs from the campaign plan")
    parser.add_argument("--inset", type=int, default=0, help="Trim this many pixels from each tile edge")
    parser.add_argument("--boxes", help="JSON file containing measured crop boxes in reading order")
    args = parser.parse_args()
    plan = json.loads(Path(args.plan).read_text()) if args.plan else None
    if plan:
        grid=resolve_grid(plan)
        args.rows, args.columns = grid["rows"],grid["columns"]
    ids = [item["id"] for item in plan["items"]] if plan else None
    boxes = json.loads(Path(args.boxes).read_text()) if args.boxes else None
    result = split(args.image, args.out, args.rows, args.columns, ids, args.inset, boxes)
    print(f"Saved {len(result['tiles'])} previews; inspect grid alignment and text before selection")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"split: {error}", file=sys.stderr)
        sys.exit(1)
