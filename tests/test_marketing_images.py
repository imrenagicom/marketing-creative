"""Offline image/crop and REST-contract regressions; no paid API calls."""
import base64
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "plugins/marketing-images/skills"


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


G=module("gemini_images",SKILLS/"marketing-image-producer/scripts/gemini_images.py")
S=module("split_board",SKILLS/"marketing-image-board/scripts/split_board.py")
try:
    from PIL import Image
except ImportError:
    Image=None


def png(width=90,height=90,color="red"):
    output=io.BytesIO()
    Image.new("RGB",(width,height),color).save(output,format="PNG")
    return output.getvalue()


def response(data=None):
    return {"candidates":[{"finishReason":"STOP","content":{"parts":[
        {"inlineData":{"mimeType":"image/png","data":base64.b64encode(data or png()).decode()}}]}}],
        "usageMetadata":{"totalTokenCount":10}}


class FakeClient:
    def __init__(self,results=None):
        self.calls=[]
        self.results=list(results or [])
        self.uploads=[]

    def send(self,method,endpoint,body=None,headers=None,raw=False):
        self.calls.append((method,endpoint,body,raw))
        result=self.results.pop(0)
        if isinstance(result,Exception):
            raise result
        return result,{}

    def upload(self,data,name):
        self.uploads.append((data,name))
        return "files/input123"


@unittest.skipUnless(Image,"Install image producer requirements.txt (Pillow)")
class MarketingImageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/"source.png").write_bytes(png())
        example=G.read(SKILLS/"marketing-image-board/assets/image-plan.example.json")
        example["reference"]="source.png"
        self.plan=self.root/"image-plan.json"
        G.save(self.plan,example)

    def prepared(self,mode="final",selected=None):
        return G.prepare(self.plan,mode,selected=selected)

    def test_board_one_request_for_nine_concepts(self):
        requests,meta=self.prepared("board")
        self.assertEqual(len(requests),1)
        self.assertEqual(meta["model"],"gemini-nano-banana-2.1")
        prompt=requests[0]["request"]["contents"][0]["parts"][0]["text"]
        self.assertIn("3-row by 3-column",prompt)
        self.assertIn("Cell 9",prompt)
        client=FakeClient([response()])
        G.generate(requests,meta,self.root/"board-v1",client)
        self.assertEqual(len(client.calls),1)
        self.assertIn(":generateContent",client.calls[0][1])
        self.assertEqual(len(G.read(self.root/"board-v1/assets.json")["assets"]),1)

    def test_dry_run_without_key_or_output_writes(self):
        env={k:v for k,v in os.environ.items() if k not in ("GEMINI_API_KEY","GOOGLE_API_KEY")}
        result=subprocess.run([sys.executable,str(SKILLS/"marketing-image-producer/scripts/gemini_images.py"),
            "board",str(self.plan),"--out",str(self.root/"dry"),"--dry-run"],capture_output=True,text=True,env=env)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)["requestCount"],1)
        self.assertFalse((self.root/"dry").exists())

    def test_split_retains_all_pixels_and_stable_ids(self):
        source=self.root/"odd.png"
        source.write_bytes(png(101,104))
        ids=[i["id"] for i in G.read(self.plan)["items"]]
        result=S.split(source,self.root/"tiles",ids=ids)
        self.assertEqual([t["id"] for t in result["tiles"]],ids)
        self.assertEqual(sum(t["width"]*t["height"] for t in result["tiles"]),101*104)
        self.assertEqual(result["tiles"][-1]["box"],[67,69,101,104])
        self.assertTrue(all(not t["reviewed"] for t in result["tiles"]))
        for tile in result["tiles"]:
            with Image.open(self.root/"tiles"/tile["path"]) as image:
                self.assertEqual(image.size,(tile["width"],tile["height"]))

    def test_measured_crops_inset_and_overwrite_protection(self):
        result=S.split(self.root/"source.png",self.root/"single",1,1,["one"],2,[[10,10,80,80]])
        self.assertEqual(result["tiles"][0]["box"],[12,12,78,78])
        with self.assertRaisesRegex(ValueError,"already exists"):
            S.split(self.root/"source.png",self.root/"single",1,1,["one"])
        with self.assertRaisesRegex(ValueError,"Invalid tile ID"):
            S.split(self.root/"source.png",self.root/"bad",1,1,["../escape"])

    def test_split_preserves_alpha_including_palette_transparency(self):
        for mode in ("RGBA","P"):
            source=self.root/f"alpha-{mode}.png"
            image=Image.new("RGBA",(9,9),(255,0,0,0))
            if mode=="P":
                image=image.convert("P")
            image.save(source)
            folder=self.root/f"tiles-{mode}"
            S.split(source,folder,1,1,["alpha"])
            with Image.open(folder/"alpha.png") as crop:
                self.assertEqual(crop.mode,"RGBA")
                self.assertEqual(crop.getpixel((0,0)),(255,0,0,0))

    def test_ratio_mismatch_preserves_paid_image_and_flags_review(self):
        requests,meta=self.prepared(selected=["demo"])
        requests[0]["request"]["generationConfig"]["imageConfig"]["aspectRatio"]="4:5"
        item=G.generate(requests,meta,self.root/"ratio",FakeClient([response()]))
        self.assertFalse(item["ratioMatches"])
        self.assertTrue(item["reviewIssues"])
        self.assertTrue((self.root/"ratio/demo.png").is_file())
        self.assertEqual(G.read(self.root/"ratio/state.json")["status"],"completed-with-warnings")

    def test_selected_finals_use_original_and_matching_tile(self):
        ids=[i["id"] for i in G.read(self.plan)["items"]]
        S.split(self.root/"source.png",self.root/"tiles",ids=ids)
        requests,meta=G.prepare(self.plan,"final",selected=["action","demo"],tiles_dir=self.root/"tiles")
        self.assertEqual(meta["keys"],["action","demo"])
        self.assertEqual(len(requests[0]["request"]["contents"][0]["parts"]),3)
        self.assertEqual(requests[0]["request"]["generationConfig"]["imageConfig"]["imageSize"],"4K")
        (self.root/"tiles/action.png").write_bytes(png(color="blue"))
        with self.assertRaisesRegex(ValueError,"tile changed"):
            G.prepare(self.plan,"final",selected=["action"],tiles_dir=self.root/"tiles")

    def test_batch_uses_discounted_api_not_sync_fanout(self):
        requests,meta=self.prepared(selected=["demo","action"])
        client=FakeClient([{"name":"batches/job123"}])
        state=G.submit(requests,meta,self.root/"job",client=client)
        self.assertEqual(len(client.calls),1)
        self.assertIn(":batchGenerateContent",client.calls[0][1])
        entries=client.calls[0][2]["batch"]["inputConfig"]["requests"]["requests"]
        self.assertEqual([e["metadata"]["key"] for e in entries],["demo","action"])
        self.assertEqual(state["status"],"submitted")
        self.assertNotIn("inlineData",(self.root/"job/requests.json").read_text())

    def test_file_batch_jsonl_transport(self):
        requests,meta=self.prepared(selected=["demo","action"])
        client=FakeClient([{"name":"batches/job123"}])
        state=G.submit(requests,meta,self.root/"file-job","file",client)
        self.assertEqual(state["inputFile"],"files/input123")
        rows=[json.loads(line) for line in client.uploads[0][0].splitlines()]
        self.assertEqual([r["key"] for r in rows],["demo","action"])
        self.assertEqual(client.calls[0][2]["batch"]["inputConfig"],{"fileName":"files/input123"})

    def test_resumable_upload_wire_headers_and_body(self):
        captured=[]
        class HTTPResponse(io.BytesIO):
            def __init__(self,data,headers):
                super().__init__(data)
                self.headers=headers
        class Opener:
            def open(self,request,timeout):
                captured.append(request)
                if len(captured)==1:
                    return HTTPResponse(b"{}",{"x-goog-upload-url":G.API+"/upload/session"})
                return HTTPResponse(b'{"file":{"name":"files/upload123"}}',{})
        with patch.dict(os.environ,{"GEMINI_API_KEY":"synthetic-test-value"}):
            client=G.Client()
        client.opener=Opener()
        self.assertEqual(client.upload(b'{"key":"demo"}\n',"test-job"),"files/upload123")
        headers=[{k.lower():v for k,v in req.header_items()} for req in captured]
        self.assertEqual(headers[0]["x-goog-upload-protocol"],"resumable")
        self.assertEqual(headers[0]["x-goog-upload-header-content-type"],"application/jsonl")
        self.assertEqual(headers[1]["x-goog-upload-command"],"upload, finalize")
        self.assertEqual(headers[1]["x-goog-upload-offset"],"0")
        self.assertEqual(captured[1].data,b'{"key":"demo"}\n')

    def test_final_requests_support_all_four_ratios_and_explicit_size(self):
        plan=G.read(self.plan)
        for item,ratio in zip(plan["items"],("1:1","4:5","9:16","16:9")):
            item["aspectRatio"]=ratio
        G.save(self.plan,plan)
        requests,_=G.prepare(self.plan,"final",size="2K",selected=[i["id"] for i in plan["items"][:4]])
        self.assertEqual([r["request"]["generationConfig"]["imageConfig"] for r in requests],
            [{"aspectRatio":r,"imageSize":"2K"} for r in ("1:1","4:5","9:16","16:9")])

    def job(self,keys=("demo","action")):
        requests,meta=self.prepared(selected=list(keys))
        G.submit(requests,meta,self.root/"job",client=FakeClient([{"name":"batches/job123"}]))
        return self.root/"job"

    def test_keyed_results_are_mapped_despite_reordering(self):
        job=self.job()
        entries=[{"metadata":{"key":"action"},"response":response(png(color="blue"))},
                 {"metadata":{"key":"demo"},"response":response(png(color="red"))}]
        client=FakeClient([{"name":"batches/job123","done":True,"response":{"inlinedResponses":{"inlinedResponses":entries}}}])
        report=G.collect(job,client)
        self.assertEqual([a["id"] for a in report["assets"]],["demo","action"])
        with Image.open(job/"images/action.png") as image:
            self.assertEqual(image.getpixel((0,0)),(0,0,255))

    def test_partial_errors_preserve_successes(self):
        job=self.job()
        entries=[{"metadata":{"key":"demo"},"response":response()},
                 {"metadata":{"key":"action"},"error":{"code":8,"message":"not printed"}}]
        report=G.collect(job,FakeClient([{"metadata":{"state":"BATCH_STATE_SUCCEEDED"},"response":{"inlinedResponses":{"inlinedResponses":entries}}}]))
        self.assertEqual(len(report["assets"]),1)
        self.assertEqual(report["errors"][0]["id"],"action")
        self.assertTrue((job/"images/demo.png").is_file())
        self.assertEqual(G.read(job/"state.json")["status"],"collected-with-errors")

    def test_interrupted_collection_resumes_without_generation_or_overwrite(self):
        job=self.job()
        result={"done":True,"response":{"inlinedResponses":[
            {"key":"demo","response":response()},
            {"key":"action","response":response(png(color="blue"))}]}}
        store=G.store_image
        def interrupt_second(root,key,*args):
            if key=="action":
                raise KeyboardInterrupt()
            return store(root,key,*args)
        with patch.object(G,"store_image",side_effect=interrupt_second):
            with self.assertRaises(KeyboardInterrupt):
                G.collect(job,FakeClient([result]))
        first=(job/"images/demo.png").read_bytes()
        self.assertFalse(G.read(job/"assets.json")["collectionComplete"])
        client=FakeClient([result])
        report=G.collect(job,client)
        self.assertEqual(len(report["assets"]),2)
        self.assertFalse(report["errors"])
        self.assertTrue(report["collectionComplete"])
        self.assertEqual(first,(job/"images/demo.png").read_bytes())
        self.assertEqual([c[0] for c in client.calls],["GET"])
        changed=png(color="green")
        (job/"images/demo.png").write_bytes(changed)
        report=G.collect(job,FakeClient([result]))
        self.assertEqual(report["errors"][0]["id"],"demo")
        self.assertEqual(changed,(job/"images/demo.png").read_bytes())

    def test_payload_guard_counts_without_full_serialization(self):
        value={"prompt":"文字","image":"x"*300}
        digest,size=G.encoding_stats(value)
        self.assertEqual((digest,size),(G.sha(G.encoded(value)),len(G.encoded(value))))
        with patch.object(G,"FILE_LIMIT",100):
            with self.assertRaisesRegex(ValueError,"200 MiB guard"):
                G.encoding_stats(value)

    def test_file_results_download_and_positional_fallback(self):
        job=self.job()
        rows=b"\n".join(G.encoded({"response":response()}) for _ in range(2))
        client=FakeClient([{"done":True,"response":{"responsesFile":"files/results123"}},rows])
        report=G.collect(job,client)
        self.assertEqual(len(report["assets"]),2)
        self.assertIn("/download/v1beta/files/results123:download?alt=media",client.calls[1][1])
        self.assertTrue(client.calls[1][3])

    def test_pending_batch_never_downloads_or_resubmits(self):
        job=self.job()
        client=FakeClient([{"metadata":{"state":"JOB_STATE_RUNNING"}}])
        with self.assertRaisesRegex(ValueError,"RUNNING"):
            G.collect(job,client)
        self.assertEqual(len(client.calls),1)
        self.assertEqual(client.calls[0][0],"GET")

    def test_ambiguous_result_keys_fail_before_saving_images(self):
        job=self.job()
        for keys in (("demo","demo"),("demo",None),("demo","unknown")):
            entries=[{"metadata":{"key":key},"response":response()} for key in keys]
            client=FakeClient([{"done":True,"response":{"inlinedResponses":entries}}])
            with self.assertRaisesRegex(ValueError,"result keys"):
                G.collect(job,client)
            self.assertFalse((job/"images").exists())

    def test_timeout_keeps_unknown_state_and_refuses_duplicate_run(self):
        requests,meta=self.prepared(selected=["demo"])
        client=FakeClient([TimeoutError("simulated")])
        with self.assertRaises(TimeoutError):
            G.submit(requests,meta,self.root/"unknown",client=client)
        self.assertEqual(G.read(self.root/"unknown/state.json")["status"],"failed-or-unknown")
        with self.assertRaises(FileExistsError):
            G.submit(requests,meta,self.root/"unknown",client=FakeClient())

    def test_safety_block_and_no_image_are_not_success(self):
        with self.assertRaisesRegex(ValueError,"blocked"):
            G.generated_image({"promptFeedback":{"blockReason":"SAFETY"}})
        with self.assertRaisesRegex(ValueError,"exactly one"):
            G.generated_image({"candidates":[{"content":{"parts":[{"text":"No image"}]}}]})

    def test_no_key_in_saved_state_and_upload_url_is_restricted(self):
        requests,meta=self.prepared(selected=["demo"])
        G.submit(requests,meta,self.root/"job",client=FakeClient([{"name":"batches/job123"}]))
        self.assertNotIn("GEMINI_API_KEY",(self.root/"job/state.json").read_text())
        with patch.dict(os.environ,{"GEMINI_API_KEY":"synthetic-test-value"}):
            with self.assertRaisesRegex(ValueError,"Untrusted API URL"):
                G.Client().send("POST","https://example.com/upload",b"test")

    def test_bad_grid_ids_and_unknown_selection_fail_before_spend(self):
        data=G.read(self.plan)
        data["grid"]={"rows":1,"columns":1}
        G.save(self.plan,data)
        with self.assertRaisesRegex(ValueError,"fewer cells"):
            self.prepared("board")
        with self.assertRaisesRegex(ValueError,"Unknown selected"):
            self.prepared(selected=["missing"])

    def test_arbitrary_concept_counts_resolve_same_croppable_grid(self):
        template=G.read(self.plan)
        for count in (1,5,7,11,17):
            plan=copy.deepcopy(template)
            plan.pop("grid")
            plan["items"]=[{**template["items"][0],"id":f"concept-{i}"} for i in range(count)]
            G.save(self.plan,plan)
            requests,meta=self.prepared("board")
            self.assertEqual(len(requests),1)
            grid=meta["grid"]
            self.assertEqual(grid,S.resolve_grid(plan))
            self.assertGreaterEqual(grid["rows"]*grid["columns"],count)
            folder=self.root/f"tiles-{count}"
            result=S.split(self.root/"source.png",folder,grid["rows"],grid["columns"],[i["id"] for i in plan["items"]])
            self.assertEqual(len(result["tiles"]),count)
            self.assertEqual(result["unusedCells"],grid["rows"]*grid["columns"]-count)

    def test_rectangular_sheet_and_partial_last_row_crop_only_concepts(self):
        plan=G.read(self.plan)
        plan["items"]=plan["items"][:5]
        plan["grid"]={"rows":2,"columns":3,"aspectRatio":"16:9"}
        G.save(self.plan,plan)
        requests,meta=self.prepared("board")
        self.assertEqual(requests[0]["request"]["generationConfig"]["imageConfig"]["aspectRatio"],"16:9")
        self.assertIn("remaining 1 trailing cells empty",requests[0]["request"]["contents"][0]["parts"][0]["text"])
        result=subprocess.run([sys.executable,str(SKILLS/"marketing-image-board/scripts/split_board.py"),
            str(self.root/"source.png"),"--plan",str(self.plan),"--out",str(self.root/"partial")],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        tiles=G.read(self.root/"partial/tiles.json")["tiles"]
        self.assertEqual(len(tiles),5)
        self.assertEqual(tiles[-1]["box"],[30,45,60,90])
        self.assertFalse((self.root/"partial/tile-06.png").exists())

    def test_brief_only_generation_and_tile_only_final(self):
        plan=G.read(self.plan)
        plan.pop("reference")
        G.save(self.plan,plan)
        requests,meta=self.prepared("board")
        self.assertEqual(len(requests[0]["request"]["contents"][0]["parts"]),1)
        self.assertEqual(meta["references"],[])
        requests,_=self.prepared(selected=["demo"])
        self.assertEqual(len(requests[0]["request"]["contents"][0]["parts"]),1)
        S.split(self.root/"source.png",self.root/"tiles",ids=[i["id"] for i in plan["items"]])
        requests,_=G.prepare(self.plan,"final",selected=["demo"],tiles_dir=self.root/"tiles")
        parts=requests[0]["request"]["contents"][0]["parts"]
        self.assertEqual(len(parts),2)
        self.assertIn("Image 1 is the selected",parts[0]["text"])

    def test_multiple_reference_roles_and_selected_tile_image_number(self):
        plan=G.read(self.plan)
        plan.pop("reference")
        (self.root/"look.png").write_bytes(png(color="blue"))
        plan["references"]=[{"path":"source.png","role":"product"},{"path":"look.png","role":"style"}]
        G.save(self.plan,plan)
        requests,meta=self.prepared("board")
        self.assertEqual([r["role"] for r in meta["references"]],["product","style"])
        self.assertEqual(len(requests[0]["request"]["contents"][0]["parts"]),3)
        S.split(self.root/"source.png",self.root/"tiles",ids=[i["id"] for i in plan["items"]])
        requests,_=G.prepare(self.plan,"final",selected=["demo"],tiles_dir=self.root/"tiles")
        parts=requests[0]["request"]["contents"][0]["parts"]
        self.assertEqual(len(parts),4)
        self.assertIn("Image 3 is the selected",parts[0]["text"])
        self.assertEqual(parts[2]["inlineData"]["data"],base64.b64encode((self.root/"look.png").read_bytes()).decode())

    def test_repeated_cli_references_override_plan(self):
        plan=G.read(self.plan)
        plan["reference"]="missing.png"
        G.save(self.plan,plan)
        result=subprocess.run([sys.executable,str(SKILLS/"marketing-image-producer/scripts/gemini_images.py"),
            "board",str(self.plan),"--reference",str(self.root/"source.png"),"--reference",str(self.root/"source.png"),
            "--out",str(self.root/"dry-cli"),"--dry-run"],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(len(json.loads(result.stdout)["references"]),2)
        self.assertFalse((self.root/"dry-cli").exists())

    def test_reference_limits_include_selected_tile(self):
        plan=G.read(self.plan)
        plan.pop("reference")
        plan["references"]=["source.png"]*15
        G.save(self.plan,plan)
        with self.assertRaisesRegex(ValueError,"fourteen reference"):
            self.prepared("board")
        plan["references"].pop()
        G.save(self.plan,plan)
        self.prepared("board")
        S.split(self.root/"source.png",self.root/"tiles",ids=[i["id"] for i in plan["items"]])
        with self.assertRaisesRegex(ValueError,"plus references"):
            G.prepare(self.plan,"final",selected=["demo"],tiles_dir=self.root/"tiles")

    def test_extended_image_ratios_and_constrained_auto_grid(self):
        plan=G.read(self.plan)
        plan["grid"]={"aspectRatio":"21:9"}
        plan["items"]=plan["items"][:4]
        for item,ratio in zip(plan["items"],("2:3","3:4","4:3","21:9")):
            item["aspectRatio"]=ratio
        G.save(self.plan,plan)
        _,meta=self.prepared("board")
        self.assertEqual(meta["grid"]["aspectRatio"],"21:9")
        requests,_=self.prepared()
        self.assertEqual([r["request"]["generationConfig"]["imageConfig"]["aspectRatio"] for r in requests],
            ["2:3","3:4","4:3","21:9"])


if __name__=="__main__":
    unittest.main()
