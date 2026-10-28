"""Reserve, complete and recover capped Higgsfield image jobs (stdlib only).

The agent calls the Higgsfield MCP itself; these helpers make sure the cap is
checked and the call is recorded before submission, and that the returned file
lands in the project with its provenance.
"""
import hashlib
import json
from pathlib import Path
import shutil

import ledger
from studio import ContractError, now, require

PROVIDER = "higgsfield-image"


def reserve(root, operation, request, estimate):
    """Check the image cap and record the job before the MCP call; returns the ledger entry."""
    decision = ledger.check(ledger.read(root), PROVIDER, estimate)
    require(decision["allowed"], decision.get("reason", ""))
    entry = ledger.record(root, PROVIDER, operation, estimate, request)
    if decision.get("warning"):
        entry["warning"] = decision["warning"]
    return entry


def complete(root, entry_id, source, destination, job_id=None, actual=None):
    """Copy the returned image into the project and mark the job succeeded."""
    source = Path(source)
    require(source.is_file(), f"No file at {source}")
    target = Path(root) / destination
    require(not target.exists(), f"{destination} already exists; keep earlier versions and pick a new name")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    provenance = {"entry": entry_id, "job_id": job_id, "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                  "recorded_at": now()}
    target.with_suffix(target.suffix + ".json").write_text(json.dumps(provenance, indent=2) + "\n")
    ledger.update(root, entry_id, status="succeeded", actual=actual, outputs=[destination], job_id=job_id)
    return provenance


def fail(root, entry_id, uncertain=False, job_id=None):
    """A clean refusal is failed; a timeout or lost response stays unknown and counted."""
    if not any(e["id"] == entry_id for e in ledger.read(root)["entries"]):
        raise ContractError(f"Unknown ledger entry {entry_id}")
    return ledger.update(root, entry_id, status="unknown" if uncertain else "failed", job_id=job_id)


def next_name(folder, stem, suffix):
    """stem-v1.png, stem-v2.png … so earlier versions are never overwritten."""
    folder = Path(folder)
    version = 1
    while (folder / f"{stem}-v{version}{suffix}").exists():
        version += 1
    return f"{stem}-v{version}{suffix}"
