#!/usr/bin/env python3
"""One-call concept boards, reference-image finals and discounted Gemini batches.

Python 3.10+, Pillow. All paid commands have --dry-run. No automatic retries.
"""
import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import runpy
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

API = "https://generativelanguage.googleapis.com"
DEFAULT_MODEL = "gemini-nano-banana-2.1"  # Verified in official docs, 2026-10-15.
# Share packing with the crop tool so an automatic layout is reproducible.
_layout=runpy.run_path(str(Path(__file__).resolve().parents[2]/"marketing-image-board/scripts/split_board.py"))
RATIOS = _layout["RATIOS"]
resolve_grid = _layout["resolve_grid"]
SIZES = {"1K", "2K", "4K"}
INLINE_LIMIT = 18 * 1024 * 1024  # Below the documented 20 MB inline limit.
FILE_LIMIT = 200 * 1024 * 1024   # Local implementation guard; not the API maximum.


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()


def encoding_stats(value):
    """Fingerprint/count without materializing hundreds of repeated references."""
    digest, length = hashlib.sha256(), 0
    for chunk in json.JSONEncoder(ensure_ascii=False,separators=(",", ":")).iterencode(value):
        data=chunk.encode()
        length+=len(data)
        require(length<FILE_LIMIT,"Payload exceeds local 200 MiB guard; split it into explicit smaller jobs")
        digest.update(data)
    return digest.hexdigest(),length


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, value):
    path = Path(path)
    require(not path.is_symlink(), "Refusing symlink state file")
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", value), "Invalid item ID")
    return value


def pillow():
    try:
        from PIL import Image
    except ImportError:
        raise ValueError("Install scripts/requirements.txt in a Python environment first") from None
    return Image


def image_info(data):
    Image = pillow()
    with Image.open(io.BytesIO(data)) as image:
        require(image.format in {"PNG", "JPEG", "WEBP"}, "Use PNG, JPEG or WEBP images")
        image.verify()
        return {"width": image.width, "height": image.height,
                "mimeType": {"PNG":"image/png", "JPEG":"image/jpeg", "WEBP":"image/webp"}[image.format]}


def reference(path):
    file = Path(path).expanduser().resolve()
    require(file.is_file() and file.stat().st_size <= 18*1024*1024, "Reference must be an image under 18 MiB")
    data = file.read_bytes()
    info = image_info(data)
    return {"inlineData": {"mimeType": info["mimeType"], "data": base64.b64encode(data).decode()}}, {"sha256":sha(data), **info}


def load_plan(path, reference_paths=None):
    path = Path(path).resolve()
    plan = read(path)
    require(plan.get("schemaVersion") == 1, "Unsupported image plan version")
    require(isinstance(plan.get("brief"), str) and plan["brief"].strip(), "Plan needs a factual marketing brief")
    items = plan.get("items")
    require(isinstance(items, list) and items and len(items) <= 100, "Plan needs 1..100 items")
    ids = set()
    for item in items:
        identifier(item.get("id"))
        require(item["id"] not in ids, "Duplicate item ID")
        ids.add(item["id"])
        require(isinstance(item.get("prompt"), str) and item["prompt"].strip(), "Item prompt is required")
        require(isinstance(item.get("copy", ""), str), "Item copy must be a string")
        require(item.get("aspectRatio", "1:1") in RATIOS, "Unsupported final aspect ratio")
    require(reference_paths is not None or not ("reference" in plan and "references" in plan),"Use reference or references, not both")
    definitions=reference_paths if reference_paths is not None else plan.get("references",[plan["reference"]] if "reference" in plan else [])
    require(isinstance(definitions,list) and len(definitions)<=14,"Use zero to fourteen reference images")
    parts,metadata=[],[]
    for index,definition in enumerate(definitions,1):
        if isinstance(definition,str):
            definition={"path":definition,"role":"product"}
        require(isinstance(definition,dict) and isinstance(definition.get("path"),str) and definition["path"],"Reference needs an image path")
        role=definition.get("role","product")
        require(isinstance(role,str) and role.strip(),"Reference role must be a nonempty string")
        base=Path.cwd() if reference_paths is not None else path.parent
        part,info=reference(base/definition["path"])
        parts.append(part)
        metadata.append({"imageNumber":index,"role":role,**info})
    return plan, parts, metadata


def make_request(prompt, parts, model, ratio, size):
    require(ratio in RATIOS and size in SIZES, "Unsupported ratio or image size")
    return {"model": "models/"+model, "contents": [{"role":"user", "parts":[{"text":prompt}, *parts]}],
            "generationConfig": {"responseModalities":["TEXT","IMAGE"],
                                 "imageConfig":{"aspectRatio":ratio,"imageSize":size}}}


def prepare(plan_path, mode, model=DEFAULT_MODEL, size=None, selected=None, tiles_dir=None, reference_paths=None):
    require(re.fullmatch(r"[a-z][a-z0-9._-]+", model), "Invalid model ID")
    plan, sources, metadata = load_plan(plan_path,reference_paths)
    items = plan["items"]
    if selected:
        require(len(set(selected)) == len(selected), "Duplicate selected ID")
        require(set(selected) <= {i["id"] for i in items}, "Unknown selected ID")
        items = [next(i for i in items if i["id"] == key) for key in selected]
    common = ("Create marketing imagery from the brief and any supplied reference images. Preserve supplied product identity and brand details. "
              "Only use the factual claims and exact copy below. Do not invent offers, statistics, features or endorsements.\n"
              f"Marketing brief: {plan['brief']}\nVisual direction: {plan.get('style', 'Follow the supplied identity')}\n")
    for info in metadata:
        common+=f"Reference image {info['imageNumber']} role: {info['role']}. Use it only for that role; reference imagery is not evidence for new marketing claims.\n"
    requests = []
    references = list(metadata)
    grid=None
    if mode == "board":
        require(not selected and not tiles_dir, "Board includes the full plan; selections are for final generation")
        grid = resolve_grid(plan)
        rows,columns,ratio=grid["rows"],grid["columns"],grid["aspectRatio"]
        prompt = common + (f"Return ONE image containing an exact {rows}-row by {columns}-column equal-cell contact sheet. "
            "Each cell is a separate complete marketing asset. Reading order is left-to-right, top-to-bottom. "
            "No gutters, frames, outside labels, board title or shared objects crossing cell edges. "
            "Keep important content inside each cell with a modest internal margin. "
            "Do not turn this into one continuous scene. Follow each tile's distinct concept, composition and exact copy.\n")
        if rows*columns>len(items):
            prompt+=f"Only the first {len(items)} cells contain concepts. Leave the remaining {rows*columns-len(items)} trailing cells empty with a plain background.\n"
        for n,item in enumerate(items,1):
            prompt += f"Cell {n} ({item['id']}): {item['prompt']}\nExact visible copy: {json.dumps(item.get('copy',''),ensure_ascii=False)}\n"
        requests.append({"key":"board", "request":make_request(prompt,sources,model,ratio,size or "2K")})
    else:
        tiles = None
        if tiles_dir:
            folder = Path(tiles_dir).resolve()
            manifest = read(folder / "tiles.json")
            tiles = {i["id"]:i for i in manifest["tiles"]}
        for item in items:
            parts = list(sources)
            if tiles is not None:
                require(item["id"] in tiles, "Selected item has no preview tile")
                tile = tiles[item["id"]]
                file = (folder/tile["path"]).resolve()
                require(file.is_relative_to(folder), "Tile path escapes preview directory")
                require(sha(file.read_bytes()) == tile["sha256"], "Preview tile changed; inspect and regenerate its manifest")
                part, info = reference(file)
                parts.append(part)
                require(len(parts)<=14,"Selected tile plus references exceeds fourteen images; use at most thirteen references with --tiles")
                references.append({"item":item["id"], **info})
            prompt = common + f"Make ONE standalone finished asset, not a grid.\nConcept: {item['prompt']}\nExact visible copy: {json.dumps(item.get('copy',''),ensure_ascii=False)}\n"
            if tiles is not None:
                prompt += f"Image {len(parts)} is the selected low-resolution layout reference. Rebuild it at full quality using any original identity references; do not merely upscale its pixels. Preserve the chosen idea and adapt framing to the requested ratio.\n"
            requests.append({"key":item["id"], "request":make_request(prompt,parts,model,item.get("aspectRatio","1:1"),size or "4K")})
    fingerprint,payload_bytes=encoding_stats(requests)
    return requests, {"schemaVersion":1, "model":model, "mode":mode, "planSha256":sha(Path(plan_path).read_bytes()),
                      "references":references, "keys":[r["key"] for r in requests],
                      "requestSha256":fingerprint, "payloadBytes":payload_bytes, "imageSize":size or ("2K" if mode=="board" else "4K"),
                      "grid":grid}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Unexpected API redirect refused")


class Client:
    def __init__(self):
        self.key = os.environ.get("GEMINI_API_KEY")
        require(self.key, "Set GEMINI_API_KEY in the helper's environment; .env is not loaded automatically")
        self.opener = urllib.request.build_opener(NoRedirect())

    def send(self, method, endpoint, body=None, headers=None, raw=False):
        url = endpoint if endpoint.startswith("https://") else API + endpoint
        parsed = urllib.parse.urlsplit(url)
        require(parsed.scheme == "https" and parsed.hostname == "generativelanguage.googleapis.com"
                and not parsed.username and not parsed.password and parsed.port in (None,443), "Untrusted API URL")
        payload = body if isinstance(body,bytes) else encoded(body) if body is not None else None
        req = urllib.request.Request(url,data=payload,method=method,
            headers={"x-goog-api-key":self.key,"Content-Type":"application/json", **(headers or {})})
        try:
            with self.opener.open(req,timeout=180) as response:
                data, response_headers = response.read(), dict(response.headers)
        except urllib.error.HTTPError as error:
            raise ValueError(f"Gemini HTTP {error.code}; no automatic retry. Inspect local run state before resubmitting") from None
        except (urllib.error.URLError, TimeoutError):
            raise ValueError("Gemini request failed or timed out; submission outcome may be unknown. Do not automatically resubmit") from None
        return (data if raw else json.loads(data or b"{}")), response_headers

    def upload(self, data, display_name):
        _, headers = self.send("POST","/upload/v1beta/files", {"file":{"displayName":display_name}},
            {"X-Goog-Upload-Protocol":"resumable","X-Goog-Upload-Command":"start",
             "X-Goog-Upload-Header-Content-Length":str(len(data)),"X-Goog-Upload-Header-Content-Type":"application/jsonl"})
        url = next((v for k,v in headers.items() if k.lower()=="x-goog-upload-url"),None)
        require(url,"File upload returned no resumable URL")
        result,_ = self.send("POST",url,data,{"Content-Type":"application/jsonl","Content-Length":str(len(data)),
                "X-Goog-Upload-Offset":"0","X-Goog-Upload-Command":"upload, finalize"})
        name = result.get("file",{}).get("name")
        require(isinstance(name,str) and re.fullmatch(r"files/[A-Za-z0-9_-]+",name), "Invalid uploaded file name")
        return name


def new_run(output, metadata):
    requested = Path(output).expanduser()
    require(not requested.is_symlink(),"Refusing symlink run directory")
    root = requested.resolve()
    root.mkdir(parents=True,exist_ok=False)
    state = {**metadata, "status":"submitting", "displayName":"marketing-images-"+uuid.uuid4().hex}
    save(root/"state.json",state)
    return root,state


def generated_image(response):
    require(not response.get("promptFeedback",{}).get("blockReason"), "Generation blocked; no image saved")
    images = []
    for candidate in response.get("candidates",[]):
        require(candidate.get("finishReason") not in {"SAFETY","IMAGE_SAFETY","PROHIBITED_CONTENT"}, "Generation blocked")
        for part in candidate.get("content",{}).get("parts",[]):
            data = part.get("inlineData") or part.get("inline_data")
            if data and not part.get("thought",False):
                images.append(data)
    require(len(images)==1,"Expected exactly one generated image; no image or multiple images returned")
    data = base64.b64decode(images[0]["data"],validate=True)
    info = image_info(data)
    require(info["mimeType"] == images[0].get("mimeType",images[0].get("mime_type")), "Response MIME type differs from image bytes")
    return data, info


def store_image(root, key, response, request):
    identifier(key)
    data,info = generated_image(response)
    ratio = request["generationConfig"]["imageConfig"]["aspectRatio"]
    w,h = map(int,ratio.split(":"))
    ratio_matches = abs(info["width"]/info["height"]-w/h)/(w/h) < .025
    ext = {"image/png":"png","image/jpeg":"jpg","image/webp":"webp"}[info["mimeType"]]
    file = root/f"{key}.{ext}"
    require(not file.is_symlink(), "Refusing symlink image")
    if file.exists():
        # An interrupted collection can resume without overwriting local changes.
        require(file.is_file() and sha(file.read_bytes())==sha(data), "Existing image differs; preserve it before recovery")
    else:
        temporary=file.with_name(file.name+".tmp-"+uuid.uuid4().hex)
        try:
            temporary.write_bytes(data)
            os.replace(temporary,file)
        finally:
            temporary.unlink(missing_ok=True)
    return {"id":key,"path":file.name,"sha256":sha(data),**info,"reviewed":False,
            "requestedAspectRatio":ratio,"ratioMatches":ratio_matches,
            "requestedImageSize":request["generationConfig"]["imageConfig"].get("imageSize"),
            "reviewIssues":[] if ratio_matches else ["Generated aspect ratio differs; inspect preserved output"],
            "usageMetadata":response.get("usageMetadata",{})}


def generate(requests, metadata, output, client=None):
    require(len(requests)==1,"Interactive generation accepts one image/board; use batch for multiple finals")
    require(len(encoded(requests[0]["request"])) < INLINE_LIMIT,"Interactive request too large; shrink reference file")
    client = client or Client()
    root,state = new_run(output,metadata)
    try:
        body = dict(requests[0]["request"])
        body.pop("model",None)
        result,_ = client.send("POST",f"/v1beta/models/{metadata['model']}:generateContent",body)
        item = store_image(root,requests[0]["key"],result,requests[0]["request"])
        save(root/"assets.json",{"schemaVersion":1,"requestSha256":metadata["requestSha256"],"assets":[item]})
        state["status"] = "completed-with-warnings" if item["reviewIssues"] else "completed"
        save(root/"state.json",state)
        return item
    except Exception:
        state["status"]="failed-or-unknown"
        save(root/"state.json",state)
        raise


def submit(requests, metadata, output, transport="auto", client=None):
    entries = [{"request":r["request"],"metadata":{"key":r["key"]}} for r in requests]
    inline = {"batch":{"displayName":"pending", "inputConfig":{"requests":{"requests":entries}}}}
    _,length = encoding_stats(inline)
    if transport=="auto":
        transport="inline" if length<INLINE_LIMIT else "file"
    require(transport in {"inline","file"}, "Invalid batch transport")
    require(transport!="inline" or length<INLINE_LIMIT,"Inline batch exceeds 18 MiB guard; use --transport file")
    lines=None
    if transport=="file":
        lines = b"".join(encoded({"key":r["key"],"request":r["request"]})+b"\n" for r in requests)
        require(len(lines)<FILE_LIMIT,"Batch exceeds local 200 MiB guard; split it into explicit smaller jobs")
    client=client or Client()
    root,state=new_run(output,{**metadata,"transport":transport})
    # Persist only a compact redacted job map, not repeated base64 references.
    mapping={"schemaVersion":1,"requestSha256":metadata["requestSha256"],"requests":[
        {"key":r["key"],"request":{"generationConfig":r["request"]["generationConfig"]}} for r in requests]}
    save(root/"requests.json",mapping)
    state["mappingSha256"]=sha((root/"requests.json").read_bytes())
    save(root/"state.json",state)
    try:
        if transport=="file":
            name=client.upload(lines,state["displayName"])
            state["inputFile"]=name
            save(root/"state.json",state)
            body={"batch":{"displayName":state["displayName"],"inputConfig":{"fileName":name}}}
        else:
            body=inline
            body["batch"]["displayName"]=state["displayName"]
        result,_=client.send("POST",f"/v1beta/models/{metadata['model']}:batchGenerateContent",body)
        name=result.get("name")
        require(isinstance(name,str) and re.fullmatch(r"batches/[A-Za-z0-9_-]+",name),"Batch API returned no valid job name")
        state.update({"jobName":name,"status":"submitted"})
        save(root/"state.json",state)
        return state
    except Exception:
        state["status"]="failed-or-unknown"
        save(root/"state.json",state)
        raise


def job_state(result):
    state=result.get("metadata",{}).get("state") or result.get("state")
    if state:
        return re.sub(r"^(JOB|BATCH)_STATE_","",state)
    if result.get("done"):
        return "FAILED" if result.get("error") else "SUCCEEDED"
    return "PENDING"


def read_job(directory):
    requested=Path(directory).expanduser()
    require(not requested.is_symlink(),"Refusing symlink job directory")
    root=requested.resolve()
    require(not (root/"state.json").is_symlink(),"Refusing symlink job state")
    state=read(root/"state.json")
    require(re.fullmatch(r"batches/[A-Za-z0-9_-]+",state.get("jobName","")),
            "No known job name; inspect AI Studio using displayName before resubmitting")
    return root,state


def get_job(directory, client=None):
    root,state=read_job(directory)
    result,_=(client or Client()).send("GET","/v1beta/"+state["jobName"])
    require(result.get("name",state["jobName"])==state["jobName"],"Job identity differs")
    state["remoteState"]=job_state(result)
    save(root/"state.json",state)
    return root,state,result


def response_entries(result, client):
    output=result.get("response") or result.get("dest") or result.get("output") or {}
    entries=output.get("inlinedResponses") or output.get("inlined_responses")
    if isinstance(entries,dict):
        entries=entries.get("inlinedResponses",[])
    if entries is not None:
        require(isinstance(entries,list),"Unexpected inline results shape")
        return entries
    file=output.get("responsesFile") or output.get("fileName") or output.get("file_name")
    require(isinstance(file,str) and re.fullmatch(r"files/[A-Za-z0-9_-]+",file),"No downloadable batch results")
    data,_=client.send("GET",f"/download/v1beta/{file}:download?alt=media",raw=True)
    return [json.loads(line) for line in data.decode().splitlines() if line.strip()]


def collect(directory, client=None):
    client=client or Client()
    root,state,result=get_job(directory,client)
    require(state["remoteState"]=="SUCCEEDED",f"Batch is {state['remoteState']}; no final images downloaded")
    mapping_file=root/"requests.json"
    require(not mapping_file.is_symlink() and sha(mapping_file.read_bytes())==state["mappingSha256"],"Job mapping changed")
    mapping=read(mapping_file)["requests"]
    entries=response_entries(result,client)
    require(len(entries)==len(mapping),"Batch result count differs; inspect provider job")
    keys=[r["key"] for r in mapping]
    # Match explicit keys; positional fallback only when the entire ordered result has no keys.
    def entry_key(entry):
        return entry.get("key") or entry.get("metadata",{}).get("key")
    explicit=[entry_key(e) for e in entries]
    if any(explicit):
        require(all(explicit) and len(set(explicit))==len(keys) and set(explicit)==set(keys),"Missing/duplicate/unknown result keys")
        by_key=dict(zip(explicit,entries))
        entries=[by_key[k] for k in keys]
    output=root/"images"
    require(not output.is_symlink() and (not output.exists() or output.is_dir()),"Invalid images directory")
    output.mkdir(exist_ok=True)
    assets,errors=[],[]
    report={"schemaVersion":1,"jobName":state["jobName"],"model":state["model"],
            "requestSha256":state["requestSha256"],"assets":assets,"errors":errors,"reviewed":False,
            "collectionComplete":False}
    for request,entry in zip(mapping,entries):
        key=request["key"]
        if entry.get("error"):
            errors.append({"id":key,"code":entry["error"].get("code"),"reason":"provider request error"})
        else:
            try:
                response=entry.get("response") or (entry if "candidates" in entry else {})
                assets.append(store_image(output,key,response,request["request"]))
            except (ValueError,KeyError,TypeError,OSError) as error:
                errors.append({"id":key,"reason":str(error)})
        save(root/"assets.json",report)
    report["collectionComplete"]=True
    save(root/"assets.json",report)
    state["status"]="collected-with-errors" if errors else "collected-with-warnings" if any(a["reviewIssues"] for a in assets) else "collected"
    save(root/"state.json",state)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="command",required=True)
    for name in ("board","image","batch-submit"):
        p=sub.add_parser(name)
        p.add_argument("plan")
        p.add_argument("--out",required=True)
        p.add_argument("--model",default=DEFAULT_MODEL)
        p.add_argument("--size",choices=sorted(SIZES))
        p.add_argument("--dry-run",action="store_true")
        p.add_argument("--reference",action="append",help="Optional reference image; repeat for multiple images. Overrides plan references; paths relative to current directory")
        if name!="board":
            p.add_argument("--select",nargs="+")
            p.add_argument("--tiles",help="Selected preview tiles directory with tiles.json")
        if name=="batch-submit":
            p.add_argument("--transport",choices=("auto","inline","file"),default="auto")
    for name in ("batch-status","batch-download","batch-cancel"):
        sub.add_parser(name).add_argument("job")
    args=parser.parse_args()
    if args.command in {"board","image","batch-submit"}:
        mode="board" if args.command=="board" else "final"
        requests,meta=prepare(args.plan,mode,args.model,args.size,getattr(args,"select",None),getattr(args,"tiles",None),args.reference)
        require(args.command!="image" or len(requests)==1,"Select exactly one item for image; use batch-submit for multiple")
        if args.dry_run:
            print(json.dumps({**meta,"requestCount":len(requests),
                "billableSubmission":False,"note":"No API call, key lookup or output writes; board is one image, finals one image per selected item"},ensure_ascii=False,indent=2))
            return
        if args.command=="batch-submit":
            result=submit(requests,meta,args.out,args.transport)
            print(f"Submitted {result['jobName']} with {len(requests)} images; check later with batch-status")
        else:
            result=generate(requests,meta,args.out)
            print(f"Saved {result['path']} ({result['width']}×{result['height']}); visual review required")
            for issue in result["reviewIssues"]:
                print(issue,file=sys.stderr)
    elif args.command=="batch-status":
        _,state,_=get_job(args.job)
        print(state["jobName"],state["remoteState"])
    elif args.command=="batch-download":
        report=collect(args.job)
        warnings=sum(bool(a["reviewIssues"]) for a in report["assets"])
        print(f"Saved {len(report['assets'])} images; {len(report['errors'])} errors; {warnings} ratio warnings")
        if report["errors"]:
            sys.exit(2)
    else:
        root,state=read_job(args.job)
        Client().send("POST","/v1beta/"+state["jobName"]+":cancel",{})
        state["status"]="cancellation-requested"
        save(root/"state.json",state)
        print("Cancellation requested; check batch-status for the outcome")


if __name__=="__main__":
    try:
        main()
    except (ValueError,KeyError,OSError,TypeError) as error:
        print(f"gemini-images: {error}",file=sys.stderr)
        sys.exit(1)
