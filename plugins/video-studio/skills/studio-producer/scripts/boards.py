"""Contact-sheet boards: many low-resolution previews from ONE Gemini image call, cropped locally.

A board is exploration, not production. Its tiles are previews with stable cell
IDs; they are never registered as keyframes or bible images. Selected tiles can
be attached to a later full-resolution request as a composition reference.
Cropping uses FFmpeg's crop filter (no resampling); everything else is stdlib.
"""
import json
import math
from pathlib import Path
import shutil
import subprocess

import gemini
import media
from studio import now, require

MAX_CELLS = 12
TILE_NOTE = ("A low-resolution board tile of this frame is attached as a composition and staging reference only; "
             "rebuild it as one full-resolution frame and take identity and facts from the other references.")


def ratio(text):
    width, height = (float(part) for part in text.split(":"))
    return width / height


def nearest_aspect(value):
    return min(gemini.IMAGE_ASPECTS, key=lambda aspect: abs(math.log(value / ratio(aspect))))


def layout(count, cell_aspect, grid=None):
    """(rows, columns, sheet aspect) that keeps every cell close to cell_aspect."""
    require(1 <= count <= MAX_CELLS, f"A board holds 1–{MAX_CELLS} cells so each tile keeps enough pixels; "
                                     f"split {count} cells into several boards")
    cell = ratio(cell_aspect)
    if grid:
        rows, columns = grid
        require(rows * columns >= count, f"A {rows}x{columns} grid cannot hold {count} cells")
        return rows, columns, nearest_aspect(columns * cell / rows)

    def score(columns):
        rows = math.ceil(count / columns)
        sheet = columns * cell / rows
        return abs(math.log(sheet / ratio(nearest_aspect(sheet)))) + 0.15 * (rows * columns - count)
    columns = min(range(1, count + 1), key=score)
    rows = math.ceil(count / columns)
    return rows, columns, nearest_aspect(columns * cell / rows)


def parse_grid(text):
    if not text:
        return None
    rows, _, columns = text.lower().partition("x")
    require(rows.isdigit() and columns.isdigit() and int(rows) > 0 and int(columns) > 0, "Use --grid ROWSxCOLUMNS, e.g. 3x3")
    return int(rows), int(columns)


def sheet_prompt(cells, rows, columns, cell_aspect, preamble):
    lines = [f"A contact sheet of {len(cells)} separate {cell_aspect} frames in a precise grid of {rows} rows and "
             f"{columns} columns that fills the whole image edge to edge. Every cell is the same size, divided by thin "
             "uniform dark gutters. No labels, numbers, captions or text anywhere. Each frame is composed on its own; "
             "nothing crosses a gutter.", preamble.strip()]
    for index, cell in enumerate(cells):
        row, column = divmod(index, columns)
        lines.append(f"Frame {index + 1} (row {row + 1}, column {column + 1}): {cell['prompt']}")
    if rows * columns > len(cells):
        lines.append(f"Leave the cells after frame {len(cells)} plain mid-grey.")
    return "\n".join(line for line in lines if line)


def plan(root, folder, cells, cell_aspect, preamble="", inputs=(), grid=None, model=None, image_size="2K"):
    """Write <folder>/board-vN/board.json for one board call; returns (board path, board)."""
    require(len({cell["id"] for cell in cells}) == len(cells), "Board cell IDs must be unique")
    rows, columns, sheet = layout(len(cells), cell_aspect, grid)
    request = gemini.image_request(model or gemini.IMAGE_MODEL, sheet_prompt(cells, rows, columns, cell_aspect, preamble),
                                   sheet, image_size, list(dict.fromkeys(inputs)))
    found = gemini.problems(request)
    require(not found, "; ".join(found))
    base = Path(root) / folder
    version = 1
    while (base / f"board-v{version}").exists():
        version += 1
    relative = f"{folder}/board-v{version}"
    board = {"id": f"board-v{version}", "status": "planned", "rows": rows, "columns": columns, "sheet_aspect": sheet,
             "cell_aspect": cell_aspect, "cells": [{"id": c["id"], "prompt": c["prompt"]} for c in cells],
             "request": request, "estimate_usd": gemini.estimate(request), "created_at": now()}
    (Path(root) / relative).mkdir(parents=True)
    write(root, relative, board)
    return relative, board


def read(root, relative):
    path = Path(root) / relative / "board.json"
    require(path.is_file(), f"No board at {relative}; plan one first")
    return json.loads(path.read_text(encoding="utf-8"))


def write(root, relative, board):
    (Path(root) / relative / "board.json").write_text(json.dumps(board, indent=2, ensure_ascii=False) + "\n")


def generate(root, relative, estimate=None):
    """One gemini-api image call under the gemini-image cap, then a local split into tiles."""
    board = read(root, relative)
    require(board["status"] == "planned", f"{relative} was already sent ({board['status']}); plan a new board to try again")
    entry, path, response_id = media.generate_gemini(root, "gemini-api image:board", board["request"], estimate)
    destination = f"{relative}/board{Path(path).suffix or '.png'}"
    media.complete(root, entry["id"], path, destination, response_id)
    board.update(status="generated", image=destination, entry=entry["id"])
    write(root, relative, board)
    result = split(root, relative)
    return {**result, "entry": entry["id"], "estimate_usd": entry["estimate"],
            **({"warning": entry["warning"]} if entry.get("warning") else {})}


def dimensions(path):
    run = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                          "-of", "json", str(path)], capture_output=True, text=True)
    require(run.returncode == 0, f"ffprobe could not read {path}: {run.stderr.strip()}")
    stream = json.loads(run.stdout)["streams"][0]
    return stream["width"], stream["height"]


def split(root, relative, inset=0):
    """Crop the returned sheet into tiles-vN/<cell>.png on the planned grid; never resamples."""
    require(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg and ffprobe are needed to split a board")
    board = read(root, relative)
    require(board.get("image"), f"{relative} has no returned sheet yet")
    sheet = Path(root) / board["image"]
    width, height = dimensions(sheet)
    cell_w, cell_h = width // board["columns"], height // board["rows"]
    require(0 <= inset * 2 < min(cell_w, cell_h), f"Inset {inset}px leaves no tile")
    version = 1
    while (Path(root) / relative / f"tiles-v{version}").exists():
        version += 1
    folder = f"{relative}/tiles-v{version}"
    (Path(root) / folder).mkdir()
    tiles = {}
    for index, cell in enumerate(board["cells"]):
        row, column = divmod(index, board["columns"])
        box = [column * cell_w + inset, row * cell_h + inset, cell_w - 2 * inset, cell_h - 2 * inset]
        target = f"{folder}/{cell['id']}.png"
        run = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(sheet), "-vf",
                              "crop={2}:{3}:{0}:{1}".format(*box), "-frames:v", "1", str(Path(root) / target)],
                             capture_output=True, text=True)
        require(run.returncode == 0, f"Could not crop {cell['id']}: {run.stderr.strip()}")
        tiles[cell["id"]] = {"file": target, "box": box}
    board.setdefault("splits", []).append({"folder": folder, "sheet": [width, height], "inset": inset, "tiles": tiles,
                                           "at": now()})
    board["status"] = "split"
    write(root, relative, board)
    return {"board": relative, "sheet": board["image"], "tiles": folder,
            "tile_size": [cell_w - 2 * inset, cell_h - 2 * inset],
            "note": "Previews only: inspect the whole sheet first; if the model ignored the grid, re-split with --inset "
                    "or plan a new board. Tiles are not keyframes or bible images."}
