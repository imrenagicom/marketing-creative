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
        self.assertEqual(result["links"][0]["platform"], "meta")
        self.assertEqual(result["links"][0]["platform_campaign"], "taskapp-activation-sales")
        self.assertEqual(result["links"][0]["adset"], "id-18-45-design-teams")
        self.assertEqual(result["links"][0]["ad"], "reels-demo-v1")
        self.assertEqual(
            dict(parse_qsl(result["links"][0]["url_tags"])),
            {
                "utm_source": "instagram",
                "utm_medium": "paid_social",
                "utm_campaign": "taskapp-activation-id-2026q4",
                "utm_content": "demo-v1-reels",
                "utm_id": "2026-10-18-example-taskapp-activation",
            },
        )

    def test_partial_or_invalid_platform_hierarchy_fails(self):
        partial = copy.deepcopy(self.plan)
        partial["links"][0].pop("adset")
        with self.assertRaisesRegex(ValueError, "must specify platform, platform_campaign, adset and ad together"):
            UTM.build_plan(partial)
        bad_slug = copy.deepcopy(self.plan)
        bad_slug["links"][0]["ad"] = "../bad-ad"
        with self.assertRaisesRegex(ValueError, "must be a lowercase slug"):
            UTM.build_plan(bad_slug)

    def _write_valid_meta_tree(self):
        ad_dir = (
            self.root
            / "meta/campaigns/taskapp-activation-sales"
            / "adsets/id-18-45-design-teams"
            / "ads/reels-demo-v1"
        )
        ad_dir.mkdir(parents=True, exist_ok=True)
        campaign_dir = self.root / "meta/campaigns/taskapp-activation-sales"
        adset_dir = campaign_dir / "adsets/id-18-45-design-teams"
        (campaign_dir / "campaign.json").write_text(json.dumps({
            "schema_version": 1,
            "platform": "meta",
            "campaign_slug": "taskapp-activation-sales",
            "name": "TaskApp Activation - Sales",
            "objective": "OUTCOME_SALES",
            "buying_type": "AUCTION",
            "budget": {
                "mode": "cbo",
                "currency": "USD",
                "daily_budget": 150.0,
                "lifetime_budget": None,
                "spend_cap": 4500.0,
                "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            },
            "special_ad_categories": [],
            "status": "paused",
        }))
        (adset_dir / "adset.json").write_text(json.dumps({
            "schema_version": 1,
            "adset_slug": "id-18-45-design-teams",
            "name": "ID 18-45 Design Teams - Reels 9x16",
            "optimization_goal": "OFFSITE_CONVERSIONS",
            "billing_event": "IMPRESSIONS",
            "conversion": {"dataset_or_pixel_id": "123456789012345", "custom_event_type": "START_TRIAL"},
            "budget": {"daily_budget": None, "lifetime_budget": None},
            "schedule": {"start_time": "2026-10-18T00:00:00+07:00", "end_time": None},
            "targeting": {
                "geo_locations": {"countries": ["ID"]},
                "age_min": 18,
                "age_max": 45,
                "genders": ["all"],
                "locales": ["id_ID", "en_US"],
                "interests": ["Design", "Productivity"],
                "custom_audiences": [],
                "excluded_custom_audiences": ["existing_active_subscribers_180d"],
            },
            "placements": {
                "mode": "manual",
                "publisher_platforms": ["instagram", "facebook"],
                "instagram_positions": ["reels", "story"],
                "facebook_positions": ["facebook_reels"],
                "aspect_ratios": ["9:16"],
            },
            "status": "paused",
        }))
        built_row = UTM.build_plan(self.plan)["links"][0]
        expected_utm = {k: built_row[k] for k in UTM.UTM_KEYS if built_row[k]}
        (ad_dir / "ad.json").write_text(json.dumps({
            "schema_version": 1,
            "ad_slug": "reels-demo-v1",
            "name": "Reels Demo v1 - 9x16",
            "status": "paused",
            "format": "video",
            "call_to_action": "LEARN_MORE",
            "link_id": built_row["link_id"],
            "destination_url": built_row["destination_url"],
            "utm": expected_utm,
            "url_tags": built_row["url_tags"],
            "approved_copy_revision": "v001",
            "approved_assets_revision": "v001",
        }))
        return campaign_dir, adset_dir, ad_dir

    def test_validates_meta_campaign_adset_and_ad_hierarchy_against_plan(self):
        _, _, ad_dir = self._write_valid_meta_tree()
        result = self.cli("--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(len(payload["meta_ads"]), 1)
        self.assertEqual(payload["meta_ads"][0]["ad"], "reels-demo-v1")

        ad_spec = json.loads((ad_dir / "ad.json").read_text())
        ad_spec["url_tags"] = "utm_source=wrong"
        (ad_dir / "ad.json").write_text(json.dumps(ad_spec))
        bad = self.cli("--dry-run")
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("url_tags does not match", bad.stderr)

    def test_meta_tree_missing_referenced_ad_folder_fails(self):
        self._write_valid_meta_tree()
        second = copy.deepcopy(self.plan["links"][0])
        second["link_id"] = "ig-reels-second-ad"
        second["ad"] = "missing-ad-folder"
        second["utm"]["utm_content"] = "second-hook-9x16"
        self.plan["links"].append(second)
        self.source.write_text(json.dumps(self.plan))
        result = self.cli("--dry-run")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("is missing its meta/campaigns/", result.stderr)

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
