#!/usr/bin/env python3
"""Video Studio cost ledger: per-project caps, pre-call checks and spend records (stdlib only).

A cap is recorded only after the user approves it in chat. Calls under a capped
provider run without prompting while the ledger stays under the cap; a call that
would exceed it is refused so the agent stops and asks.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from studio import ContractError, load, now, require, write  # noqa: E402

CAPPED_PROVIDERS = {"elevenlabs", "higgsfield-image"}
WARN_AT = 0.8
COUNTED = {"submitted", "succeeded", "unknown"}
STATUSES = {"planned", "submitted", "succeeded", "failed", "unknown"}


def empty():
    return {"schema": "video-studio/ledger@1", "caps": {}, "entries": []}


def read(root):
    ledger = load(root, "ledger", required=False) or empty()
    require(ledger.get("schema") == "video-studio/ledger@1", "ledger.json must declare schema video-studio/ledger@1")
    return ledger


def spent(ledger, provider):
    """Credits committed so far: actual when known, otherwise the estimate."""
    total = 0.0
    for entry in ledger["entries"]:
        if entry["provider"] == provider and entry["status"] in COUNTED:
            total += entry["actual"] if entry.get("actual") is not None else entry["estimate"]
    return total


def check(ledger, provider, estimate):
    """Return a decision dict; allowed is False when the cap is missing or would be exceeded."""
    require(provider in CAPPED_PROVIDERS, f"{provider} is not a capped provider; it needs per-request approval")
    require(estimate >= 0, "estimate must be non-negative")
    cap = ledger["caps"].get(provider)
    used = spent(ledger, provider)
    decision = {"provider": provider, "estimate": estimate, "spent": used, "cap": cap and cap["credits"]}
    if not cap:
        return {**decision, "allowed": False, "reason": f"No approved {provider} cap; propose one and ask the user"}
    after = used + estimate
    decision["after"] = after
    if after > cap["credits"]:
        return {**decision, "allowed": False,
                "reason": f"Would exceed the approved cap ({after:g} > {cap['credits']:g}); ask the user to raise it"}
    decision["allowed"] = True
    if after >= WARN_AT * cap["credits"]:
        decision["warning"] = f"{after / cap['credits']:.0%} of the approved {provider} cap"
    return decision


def request_sha256(request):
    return hashlib.sha256(json.dumps(request, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def set_cap(root, provider, credits, basis):
    require(provider in CAPPED_PROVIDERS, f"{provider} cannot be capped")
    require(credits > 0, "cap must be positive")
    require(basis.strip(), "record the estimate basis the user approved")
    ledger = read(root)
    ledger["caps"][provider] = {"credits": credits, "approved_by": "user", "approved_at": now(), "basis": basis}
    write(root, "ledger", ledger)
    return ledger["caps"][provider]


def record(root, provider, operation, estimate, request, status="submitted", entry_id=None):
    """Record a call before submission so an interrupted call keeps its identity."""
    require(status in STATUSES, f"Unknown status {status}")
    ledger = read(root)
    entry = {
        "id": entry_id or f"{provider}-{uuid.uuid4().hex[:12]}",
        "provider": provider,
        "operation": operation,
        "estimate": estimate,
        "actual": None,
        "status": status,
        "request_sha256": request_sha256(request),
        "outputs": [],
        "at": now(),
    }
    ledger["entries"].append(entry)
    write(root, "ledger", ledger)
    return entry


def update(root, entry_id, status=None, actual=None, outputs=None):
    ledger = read(root)
    entry = next((item for item in ledger["entries"] if item["id"] == entry_id), None)
    require(entry is not None, f"Unknown ledger entry {entry_id}")
    if status is not None:
        require(status in STATUSES, f"Unknown status {status}")
        entry["status"] = status
    if actual is not None:
        entry["actual"] = actual
    if outputs:
        entry["outputs"].extend(outputs)
    entry["updated"] = now()
    write(root, "ledger", ledger)
    return entry


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    cap = sub.add_parser("cap", help="Record a cap the user approved in chat")
    cap.add_argument("root")
    cap.add_argument("--provider", required=True, choices=sorted(CAPPED_PROVIDERS))
    cap.add_argument("--credits", required=True, type=float)
    cap.add_argument("--basis", required=True, help="How the estimate was made, as shown to the user")
    test = sub.add_parser("check", help="Would a call of this estimate fit under the cap?")
    test.add_argument("root")
    test.add_argument("--provider", required=True)
    test.add_argument("--estimate", required=True, type=float)
    show = sub.add_parser("show")
    show.add_argument("root")
    args = parser.parse_args(argv)
    try:
        if args.command == "cap":
            print(json.dumps(set_cap(args.root, args.provider, args.credits, args.basis), indent=2))
        elif args.command == "check":
            decision = check(read(args.root), args.provider, args.estimate)
            print(json.dumps(decision, indent=2))
            return 0 if decision["allowed"] else 2
        else:
            ledger = read(args.root)
            summary = {provider: {"cap": cap["credits"], "spent": spent(ledger, provider)}
                       for provider, cap in ledger["caps"].items()}
            unresolved = [e["id"] for e in ledger["entries"] if e["status"] in {"submitted", "unknown"}]
            print(json.dumps({"caps": summary, "unresolved": unresolved, "entries": len(ledger["entries"])}, indent=2))
    except ContractError as error:
        print(f"ledger: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
