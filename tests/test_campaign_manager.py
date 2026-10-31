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
        self.assertEqual(result["links"][0]["platform"], "meta-ads")
        self.assertEqual(result["links"][0]["platform_campaign"], "taskapp-activation-sales")
        self.assertEqual(result["links"][0]["adset"], "id-18-45-design-teams")
        self.assertEqual(result["links"][0]["ad"], "reels-demo-v1")
        self.assertEqual(result["links"][1]["platform"], "linkedin")
        self.assertEqual(result["links"][1]["post"], "founder-workflow-breakdown")
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
        missing_post = copy.deepcopy(self.plan)
        missing_post["links"][1].pop("post")
        with self.assertRaisesRegex(ValueError, "with social platform 'linkedin' must specify post"):
            UTM.build_plan(missing_post)
        unknown_platform = copy.deepcopy(self.plan)
        unknown_platform["links"][1]["platform"] = "myspace"
        with self.assertRaisesRegex(ValueError, "platform 'myspace' is unsupported"):
            UTM.build_plan(unknown_platform)

    def _write_valid_meta_tree(self):
        ad_dir = (
            self.root
            / "meta-ads/campaigns/taskapp-activation-sales"
            / "adsets/id-18-45-design-teams"
            / "ads/reels-demo-v1"
        )
        ad_dir.mkdir(parents=True, exist_ok=True)
        campaign_dir = self.root / "meta-ads/campaigns/taskapp-activation-sales"
        adset_dir = campaign_dir / "adsets/id-18-45-design-teams"
        (campaign_dir / "campaign.json").write_text(json.dumps({
            "schema_version": 1,
            "platform": "meta-ads",
            "campaign_slug": "taskapp-activation-sales",
            "name": "TaskApp Activation - Sales",
            "objective": "OUTCOME_SALES",
            "buying_type": "AUCTION",
            "budget": {
                "mode": "advantage_plus",
                "currency": "USD",
                "daily_budget": 150.0,
                "lifetime_budget": None,
                "spend_cap": 4500.0,
                "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
                "is_adset_budget_sharing_enabled": False,
            },
            "special_ad_categories": [],
            "status": "paused",
        }))
        (adset_dir / "adset.json").write_text(json.dumps({
            "schema_version": 1,
            "adset_slug": "id-18-45-design-teams",
            "name": "ID 18-45 Design Teams - Advantage+ Placements",
            "optimization_goal": "OFFSITE_CONVERSIONS",
            "billing_event": "IMPRESSIONS",
            "conversion": {"dataset_or_pixel_id": "123456789012345", "custom_event_type": "START_TRIAL"},
            "budget": {"mode": "advantage_plus", "inherited_from_campaign": True, "daily_budget": None, "lifetime_budget": None},
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
                "mode": "advantage_plus",
                "placement_soft_opt_out": False,
                "required_ratios": ["9:16", "4:5", "1:1"],
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
            "approved_copy_revision": "copy/approved/v001",
            "approved_assets_revision": "assets/approved/v001",
        }))
        return campaign_dir, adset_dir, ad_dir

    def _write_valid_social_trees(self):
        built_links = UTM.build_plan(self.plan)["links"]
        linkedin_row = built_links[1]
        linkedin_utm = {k: linkedin_row[k] for k in UTM.UTM_KEYS if linkedin_row[k]}
        linkedin_post = self.root / "linkedin/posts/founder-workflow-breakdown"
        linkedin_post.mkdir(parents=True, exist_ok=True)
        (linkedin_post / "post.json").write_text(json.dumps({
            "schema_version": 1,
            "platform": "linkedin",
            "post_slug": "founder-workflow-breakdown",
            "name": "Founder Workflow Breakdown Carousel",
            "status": "planned",
            "format": "carousel",
            "link_id": linkedin_row["link_id"],
            "destination_url": linkedin_row["destination_url"],
            "utm": linkedin_utm,
            "url": linkedin_row["url"],
            "approved_copy_revision": "copy/approved/v001",
            "approved_assets_revision": "assets/approved/v001",
        }))
        twitter_post = self.root / "twitter/posts/launch-thread"
        twitter_post.mkdir(parents=True, exist_ok=True)
        (twitter_post / "post.json").write_text(json.dumps({
            "schema_version": 1,
            "platform": "twitter",
            "post_slug": "launch-thread",
            "name": "Product Launch Thread",
            "status": "planned",
            "format": "thread",
            "approved_copy_revision": "copy/approved/v001",
        }))
        instagram_post = self.root / "instagram/posts/behind-the-scenes-reel"
        instagram_post.mkdir(parents=True, exist_ok=True)
        (instagram_post / "post.json").write_text(json.dumps({
            "schema_version": 1,
            "platform": "instagram",
            "post_slug": "behind-the-scenes-reel",
            "name": "Behind the Scenes Reel",
            "status": "planned",
            "format": "reel",
            "approved_copy_revision": "copy/approved/v001",
            "approved_assets_revision": "assets/approved/v001",
        }))
        return linkedin_post, twitter_post, instagram_post

    def test_validates_meta_campaign_adset_and_ad_hierarchy_against_plan(self):
        campaign_dir, adset_dir, ad_dir = self._write_valid_meta_tree()
        result = self.cli("--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(len(payload["meta_ads"]), 1)
        self.assertEqual(payload["meta_ads"][0]["ad"], "reels-demo-v1")
        self.assertEqual(payload["meta_ads"][0]["budget_mode"], "advantage_plus")
        self.assertEqual(payload["meta_ads"][0]["placements_mode"], "advantage_plus")

        # Reject manual publisher_platforms when placements.mode is advantage_plus
        adset_spec = json.loads((adset_dir / "adset.json").read_text())
        adset_spec["placements"]["publisher_platforms"] = ["instagram"]
        (adset_dir / "adset.json").write_text(json.dumps(adset_spec))
        bad_placements = self.cli("--dry-run")
        self.assertNotEqual(bad_placements.returncode, 0)
        self.assertIn("publisher_platforms must be omitted or empty when placements.mode is 'advantage_plus'", bad_placements.stderr)

        # Reject adset daily_budget when campaign budget mode is advantage_plus
        adset_spec["placements"].pop("publisher_platforms")
        adset_spec["budget"]["daily_budget"] = 50.0
        (adset_dir / "adset.json").write_text(json.dumps(adset_spec))
        bad_budget = self.cli("--dry-run")
        self.assertNotEqual(bad_budget.returncode, 0)
        self.assertIn("cannot set daily_budget or lifetime_budget when campaign budget mode is 'advantage_plus'", bad_budget.stderr)
        adset_spec["budget"]["daily_budget"] = None
        (adset_dir / "adset.json").write_text(json.dumps(adset_spec))

        ad_spec = json.loads((ad_dir / "ad.json").read_text())
        ad_spec["url_tags"] = "utm_source=wrong"
        (ad_dir / "ad.json").write_text(json.dumps(ad_spec))
        bad = self.cli("--dry-run")
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("url_tags does not match", bad.stderr)

    def test_adset_audience_slugs_resolve_to_account_level_records(self):
        _, adset_dir, _ = self._write_valid_meta_tree()
        audiences = self.root / "audiences" / "meta-ads"
        audiences.mkdir(parents=True)
        record = {
            "schema_version": 1,
            "platform": "meta-ads",
            "audience_slug": "web-all-visitors-180d",
            "name": "Example | Web | All visitors | 180d",
            "ad_account_id": "act_123",
            "kind": "website",
            "roles": ["retargeting", "exclusion"],
            "retention_days": 180,
            "status": "planned",
            "remote_audience_id": None,
            "payload": {
                "name": "Example | Web | All visitors | 180d",
                "prefill": True,
                "retention_days": 180,
                "rule": {"inclusions": {"operator": "or", "rules": [
                    {"event_sources": [{"id": "1855259662305866", "type": "pixel"}], "retention_seconds": 15552000}]}},
            },
        }
        (audiences / "web-all-visitors-180d.json").write_text(json.dumps(record))
        adset_spec = json.loads((adset_dir / "adset.json").read_text())
        adset_spec["targeting"]["excluded_custom_audiences"] = [
            {"audience_slug": "web-all-visitors-180d", "id": None, "name": record["name"]}]
        (adset_dir / "adset.json").write_text(json.dumps(adset_spec))
        ok = self.cli("--dry-run", "--audiences-dir", audiences)
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertEqual(json.loads(ok.stdout)["meta_ads"][0]["audiences"], ["web-all-visitors-180d"])

        adset_spec["targeting"]["excluded_custom_audiences"][0]["id"] = "999"
        (adset_dir / "adset.json").write_text(json.dumps(adset_spec))
        mismatch = self.cli("--dry-run", "--audiences-dir", audiences)
        self.assertNotEqual(mismatch.returncode, 0)
        self.assertIn("does not match audience 'web-all-visitors-180d' remote_audience_id", mismatch.stderr)

        record["status"] = "created"
        record["remote_audience_id"] = "999"
        record["payload"]["customer_file_source"] = "USER_PROVIDED_ONLY"
        (audiences / "web-all-visitors-180d.json").write_text(json.dumps(record))
        pii = self.cli("--dry-run", "--audiences-dir", audiences)
        self.assertNotEqual(pii.returncode, 0)
        self.assertIn("must not contain customer-file field", pii.stderr)

        record["payload"].pop("customer_file_source")
        record["payload"]["name"] = "Renamed"
        (audiences / "web-all-visitors-180d.json").write_text(json.dumps(record))
        renamed = self.cli("--dry-run", "--audiences-dir", audiences)
        self.assertIn("payload.name must equal name", renamed.stderr)

        adset_spec["targeting"]["excluded_custom_audiences"][0]["audience_slug"] = "missing-audience"
        (adset_dir / "adset.json").write_text(json.dumps(adset_spec))
        missing = self.cli("--dry-run", "--audiences-dir", audiences)
        self.assertIn("Audience record not found: audiences/meta-ads/missing-audience.json", missing.stderr)

    def test_validates_social_media_campaign_trees_for_instagram_linkedin_and_twitter(self):
        linkedin_post, _, _ = self._write_valid_social_trees()
        result = self.cli("--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            [(item["platform"], item["post"]) for item in payload["social_posts"]],
            [
                ("instagram", "behind-the-scenes-reel"),
                ("linkedin", "founder-workflow-breakdown"),
                ("twitter", "launch-thread"),
            ],
        )

        post_spec = json.loads((linkedin_post / "post.json").read_text())
        post_spec["url"] = "https://example.com/wrong"
        (linkedin_post / "post.json").write_text(json.dumps(post_spec))
        bad = self.cli("--dry-run")
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("url does not match", bad.stderr)

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
        self.assertIn("is missing its meta-ads/campaigns/", result.stderr)

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
        ga4_skill = extracted / "skills/google-analytics-analyst"
        ga4_dry = subprocess.run(
            [
                sys.executable,
                str(ga4_skill / "scripts/ga4_report.py"),
                "preset",
                "--property",
                "properties/521389584",
                "--preset",
                "funnel",
                "--campaign",
                "gochi_web_subscriptions_20261018",
                "--start-date",
                "2026-10-16",
                "--end-date",
                "today",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(ga4_dry.returncode, 0, ga4_dry.stderr)
        ga4_payload = json.loads(ga4_dry.stdout)
        self.assertTrue(ga4_payload["dry_run"])
        self.assertEqual(ga4_payload["property_id"], "521389584")
        self.assertEqual(ga4_payload["method"], "runReport")
        self.assertFalse((extracted / "skills/creative-ideation").exists())

    def test_ga4_report_helper_presets_custom_queries_and_formatting(self):
        ga4_tool = ROOT / "plugins/marketing-performance/skills/google-analytics-analyst/scripts/ga4_report.py"
        ga4_spec = importlib.util.spec_from_file_location("ga4_report", ga4_tool)
        ga4_mod = importlib.util.module_from_spec(ga4_spec)
        ga4_spec.loader.exec_module(ga4_mod)

        self.assertEqual(ga4_mod.normalize_property_id("properties/521389584"), "521389584")
        with self.assertRaises(ValueError):
            ga4_mod.normalize_property_id("not-a-number")

        for preset in ga4_mod.PRESETS:
            method, body = ga4_mod.build_preset_spec(
                preset,
                start_date="2026-10-16",
                end_date="2026-10-19",
                campaign="test_campaign",
                ad_content="variant_a",
            )
            self.assertIn(method, {"runReport", "runRealtimeReport"})
            self.assertTrue(len(body["dimensions"]) >= 1)
            self.assertTrue(len(body["metrics"]) >= 1)

        formatted = ga4_mod.format_report_response(
            {
                "dimensionHeaders": [{"name": "sessionManualAdContent"}, {"name": "eventName"}],
                "metricHeaders": [{"name": "eventCount"}, {"name": "engagementRate"}],
                "rowCount": 1,
                "rows": [
                    {
                        "dimensionValues": [{"value": "ipad_demo_exciting_v2_lp_app"}, {"value": "learning_session_started"}],
                        "metricValues": [{"value": "32"}, {"value": "0.596491"}],
                    }
                ],
                "metadata": {"currencyCode": "IDR", "timeZone": "Asia/Jakarta"},
            },
            "521389584",
            "runReport",
        )
        self.assertTrue(formatted["ok"])
        self.assertEqual(formatted["rows"][0]["sessionManualAdContent"], "ipad_demo_exciting_v2_lp_app")
        self.assertEqual(formatted["rows"][0]["eventCount"], 32)
        self.assertAlmostEqual(formatted["rows"][0]["engagementRate"], 0.5965)


if __name__ == "__main__":
    unittest.main()
