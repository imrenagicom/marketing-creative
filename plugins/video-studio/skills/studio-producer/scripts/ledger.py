#!/usr/bin/env python3
"""Video Studio cost ledger: per-project caps, pre-call checks and spend records (stdlib only).

A cap is recorded only after the user approves it in chat. Calls under a capped
provider run without prompting while the ledger stays under the cap; a call that
would exceed it is refused so the agent stops and asks. Per-request providers
need an approval bound to the exact request's fingerprint before submission.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from studio import ContractError, load, now, require, write  # noqa: E402

CAPPED_PROVIDERS = {"elevenlabs", "higgsfield-image", "gemini-image"}
PER_REQUEST_PROVIDERS = {"higgsfield-video", "higgsfield-reframe", "higgsfield-upscale", "gemini-video"}
UNITS = {"gemini-image": "USD", "gemini-video": "USD"}  # everything else is the provider's credits
WARN_AT = 0.8
COUNTED = {"submitted", "succeeded", "unknown"}
STATUSES = {"planned", "approved", "submitted", "succeeded", "failed", "unknown", "withdrawn"}


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
    decision = {"provider": provider, "estimate": estimate, "spent": used, "cap": cap and cap["credits"],
                "unit": UNITS.get(provider, "credits")}
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


def approve(root, provider, operation, request, estimate, note=""):
    """Record the user's approval of one exact request (call only after a clear yes in chat)."""
    require(provider in PER_REQUEST_PROVIDERS, f"{provider} is not a per-request provider")
    require(estimate >= 0, "record the provider's cost estimate for the request the user saw")
    entry = record(root, provider, operation, estimate, request, status="approved")
    return update(root, entry["id"], outputs=None, note=note or None)


def find_approval(ledger, provider, request):
    """The unused approval matching this exact request, or None."""
    fingerprint = request_sha256(request)
    return next((e for e in ledger["entries"] if e["provider"] == provider and e["status"] == "approved"
                 and e["request_sha256"] == fingerprint), None)


def consume_approval(root, provider, request):
    """Mark the matching approval as submitted; refuse when the request changed or was never approved."""
    entry = find_approval(read(root), provider, request)
    require(entry is not None, "No approval matches this exact request; show the changed request and ask again")
    return update(root, entry["id"], status="submitted")


def update(root, entry_id, status=None, actual=None, outputs=None, note=None, job_id=None):
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
    if note:
        entry["note"] = note
    if job_id:
        entry["job_id"] = job_id
    entry["updated"] = now()
    write(root, "ledger", ledger)
    return entry


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    cap = sub.add_parser("cap", help="Record a cap the user approved in chat")
    cap.add_argument("root")
    cap.add_argument("--provider", required=True, choices=sorted(CAPPED_PROVIDERS))
    cap.add_argument("--credits", required=True, type=float, help="Provider credits, or USD for gemini-*")
    cap.add_argument("--basis", required=True, help="How the estimate was made, as shown to the user")
    test = sub.add_parser("check", help="Would a call of this estimate fit under the cap?")
    test.add_argument("root")
    test.add_argument("--provider", required=True)
    test.add_argument("--estimate", required=True, type=float)
    allow = sub.add_parser("approve", help="Record approval of one exact request the user approved in chat")
    allow.add_argument("root")
    allow.add_argument("--provider", required=True, choices=sorted(PER_REQUEST_PROVIDERS))
    allow.add_argument("--operation", required=True)
    allow.add_argument("--request", required=True, help="Path to the exact request JSON shown to the user")
    allow.add_argument("--estimate", required=True, type=float)
    show = sub.add_parser("show")
    show.add_argument("root")
    args = parser.parse_args(argv)
    try:
        if args.command == "cap":
            print(json.dumps(set_cap(args.root, args.provider, args.credits, args.basis), indent=2))
        elif args.command == "approve":
            request = json.loads(Path(args.request).read_text(encoding="utf-8"))
            print(json.dumps(approve(args.root, args.provider, args.operation, request, args.estimate), indent=2))
        elif args.command == "check":
            decision = check(read(args.root), args.provider, args.estimate)
            print(json.dumps(decision, indent=2))
            return 0 if decision["allowed"] else 2
        else:
            ledger = read(args.root)
            summary = {provider: {"cap": cap["credits"], "spent": spent(ledger, provider)}
                       for provider, cap in ledger["caps"].items()}
            summary.update({provider: {"cap": None, "spent": spent(ledger, provider)} for provider in PER_REQUEST_PROVIDERS
                            if any(e["provider"] == provider for e in ledger["entries"])})
            unresolved = [e["id"] for e in ledger["entries"] if e["status"] in {"submitted", "unknown"}]
            print(json.dumps({"caps": summary, "unresolved": unresolved, "entries": len(ledger["entries"])}, indent=2))
    except ContractError as error:
        print(f"ledger: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
