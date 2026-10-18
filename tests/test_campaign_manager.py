import copy
import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import parse_qsl, urlsplit
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/marketing-performance/skills/campaign-manager"
TOOL = SKILL / "scripts/build_utm.py"
spec = importlib.util.spec_from_file_location("build_utm", TOOL)
UTM = importlib.util.module_from_spec(spec)
spec.loader.exec_module(UTM)
sys.path.insert(0, str(ROOT / "scripts"))
from build_plugin import build


class CampaignManagerTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((SKILL / "assets/campaign.example.json").read_text())
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / "campaign.json"
        self.source.write_text(json.dumps(self.plan, ensure_ascii=False))

    def cli(self, *args):
        return subprocess.run([sys.executable, str(TOOL), str(self.source), *map(str, args)],
                              capture_output=True, text=True)

    def test_preserves_raw_query_bytes_repeated_values_and_fragment(self):
        self.plan["links"][0]["destination_url"] = "https://example.com/start?x=a%20b&x=c%2fd&gclid=ABC%2B12&blank=#demo"
        url = UTM.build_plan(self.plan)["links"][0]["url"]
        self.assertTrue(url.startswith("https://example.com/start?x=a%20b&x=c%2fd&gclid=ABC%2B12&blank=&utm_source="))
        self.assertEqual(urlsplit(url).fragment, "demo")
        self.assertEqual(dict(parse_qsl(urlsplit(url).query))["gclid"], "ABC+12")

    def test_unicode_spacing_case_and_delimiters_round_trip_once(self):
        self.plan["links"][0]["utm"]["utm_content"] = "中文 Café + A&B / 50%"
        url = UTM.build_plan(self.plan)["links"][0]["url"]
        self.assertEqual(dict(parse_qsl(urlsplit(url).query))["utm_content"], "中文 Café + A&B / 50%")
        self.assertNotIn("utm_term=", url)

    def test_defaults_and_exact_existing_taxonomy_are_preserved(self):
        self.plan["defaults"]["utm_campaign"] = "Legacy_Campaign"
        self.plan["defaults"]["utm_source"] = "Legacy_Source"
        self.plan["defaults"]["utm_medium"] = "Legacy_Medium"
        self.plan["links"][0]["utm"] = {}
        row = UTM.build_plan(self.plan)["links"][0]
        self.assertEqual(row["utm_source"], "Legacy_Source")
        self.assertEqual(row["utm_campaign"], "Legacy_Campaign")
        self.assertEqual(row["utm_term"], "")

    def test_invalid_plans_fail_before_any_export(self):
        variants = []
        for key, value in [("schema_version", True), ("links", []), ("campaign_id", "../escape")]:
            plan = copy.deepcopy(self.plan)
            plan[key] = value
            variants.append(plan)
        for values in ({"utm_source": ""}, {"utm_medium": 42}, {"utm_source": " instagram "},
                       {"utm_term": "line\nbreak"}, {"utm_campaign": "different-campaign"},
                       {"utm_id": "fabricated-platform-id"}, {"utm_soruce": "typo"},
                       {"utm_content": "{{ad.id}}"}, {"utm_content": "%7Bcampaign%7D"}):
            plan = copy.deepcopy(self.plan)
            plan["links"][0]["utm"].update(values)
            variants.append(plan)
        missing = copy.deepcopy(self.plan)
        missing["links"][0]["utm"].pop("utm_medium")
        variants.append(missing)
        for plan in variants:
            with self.subTest(plan=plan):
                self.source.write_text(json.dumps(plan))
                out = self.root / "tracking/v001"
                result = self.cli("--out", out)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(out.exists())

    def test_rejects_existing_utm_keys_even_blank_encoded_or_mixed_case(self):
        for query in ("utm_source=old", "utm_content=", "UTM_SOURCE=old", "%75tm_campaign=old", "utm_custom=old"):
            with self.subTest(query=query), self.assertRaisesRegex(ValueError, "already contains UTM"):
                UTM.tagged_url("https://example.com/?" + query, {"utm_source": "email"})

    def test_rejects_invalid_destinations_credentials_and_macros(self):
        for url in ("/relative", "javascript:alert(1)", "https://user:pass@example.com/",
                    "https://example.com/a b", "https://example.com/%ZZ", "https://example.com/%0A",
                    "https://example.com/?ad={{ad.id}}", "https://example.com:99999/", "https://"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                UTM.tagged_url(url, {"utm_source": "email"})

    def test_duplicate_ids_fail_and_identical_urls_warn(self):
        self.plan["links"][1] = copy.deepcopy(self.plan["links"][0])
        with self.assertRaisesRegex(ValueError, "Duplicate link_id"):
            UTM.build_plan(self.plan)
        self.plan["links"][1]["link_id"] = "second-placement"
        result = UTM.build_plan(self.plan)
        self.assertEqual(len(result["warnings"]), 1)
        self.assertEqual(len(result["links"]), 2)

    def test_status_and_metadata_do_not_become_tracking_parameters(self):
        self.plan["links"][0]["status"] = "published"
        row = UTM.build_plan(self.plan)["links"][0]
        self.assertEqual(row["status"], "published")
        self.assertNotIn("creative_id", dict(parse_qsl(urlsplit(row["url"]).query)))
        self.plan["links"][0]["status"] = "retired"
        self.assertEqual(UTM.build_plan(self.plan)["links"][0]["url"], row["url"])
        self.plan["links"][0]["status"] = "launched-maybe"
        with self.assertRaisesRegex(ValueError, "invalid status"):
            UTM.build_plan(self.plan)

    def test_dry_run_previews_and_creates_no_files(self):
        before = set(self.root.rglob("*"))
        result = self.cli("--dry-run", "--out", self.root / "tracking/v001")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(json.loads(result.stdout)["links"]), 2)
        self.assertEqual(set(self.root.rglob("*")), before)

    def test_exports_exact_input_snapshot_csv_and_readable_plan(self):
        out = self.root / "tracking/v001"
        result = self.cli("--out", out)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((out / "campaign.json").read_bytes(), self.source.read_bytes())
        with (out / "utm-links.csv").open(newline="") as file:
            rows = list(csv.DictReader(file))
        self.assertEqual(rows, UTM.build_plan(self.plan)["links"])
        self.assertIn(rows[0]["url"], (out / "UTM_PLAN.md").read_text())

    def test_existing_revision_is_never_overwritten(self):
        out = self.root / "v001"
        self.assertEqual(self.cli("--out", out).returncode, 0)
        original = {p.name: p.read_bytes() for p in out.iterdir()}
        self.plan["links"][0]["utm"]["utm_content"] = "demo-v2"
        self.source.write_text(json.dumps(self.plan))
        result = self.cli("--out", out)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual({p.name: p.read_bytes() for p in out.iterdir()}, original)
        self.assertEqual(self.cli("--out", self.root / "v002").returncode, 0)
        empty = self.root / "incomplete"
        empty.mkdir()
        self.assertNotEqual(self.cli("--out", empty).returncode, 0)
        self.assertEqual(list(empty.iterdir()), [])

    def test_symlinked_output_parent_is_rejected(self):
        actual = self.root / "actual"
        actual.mkdir()
        linked = self.root / "linked"
        linked.symlink_to(actual, target_is_directory=True)
        result = self.cli("--out", linked / "v001")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(actual.iterdir()), [])

    def test_duplicate_json_keys_fail_before_export(self):
        self.source.write_text('{"schema_version":1,"schema_version":2}')
        result = self.cli("--out", self.root / "v001")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Duplicate JSON", result.stderr)
        self.assertFalse((self.root / "v001").exists())

    def test_example_plan_uses_dated_campaign_directory_slug(self):
        self.assertRegex(self.plan["campaign_id"], r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")
        result = UTM.build_plan(self.plan)
        self.assertEqual(result["campaign_id"], self.plan["campaign_id"])

    def test_packaged_helper_runs_without_creative_plugin_and_build_is_deterministic(self):
        first, second = self.root / "one.zip", self.root / "two.zip"
        build(first, "marketing-performance")
        build(second, "marketing-performance")
        self.assertEqual(first.read_bytes(), second.read_bytes())
        extracted = self.root / "installed"
        with zipfile.ZipFile(first) as archive:
            archive.extractall(extracted)
        skill = extracted / "skills/campaign-manager"
        result = subprocess.run([sys.executable, str(skill / "scripts/build_utm.py"),
                                 str(skill / "assets/campaign.example.json"), "--dry-run"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(json.loads(result.stdout)["links"]), 2)
        self.assertFalse((extracted / "skills/creative-ideation").exists())


if __name__ == "__main__":
    unittest.main()
