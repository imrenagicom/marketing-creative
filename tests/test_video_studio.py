import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "plugins/video-studio/skills"
PRODUCER = SKILLS / "studio-producer/scripts"
EXAMPLE = SKILLS / "studio-producer/assets/example-project"
sys.path.insert(0, str(PRODUCER))
import ledger  # noqa: E402
import studio  # noqa: E402


class ProjectFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "project"
        shutil.copytree(EXAMPLE, self.root)

    def read(self, key):
        return json.loads(studio.path_of(self.root, key).read_text())

    def put(self, key, document):
        studio.path_of(self.root, key).write_text(json.dumps(document))

    def run_script(self, script, *args):
        return subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True)


class StudioContractTests(ProjectFixture):
    def test_example_project_validates_and_reports_next_stage(self):
        report = studio.validate(self.root)
        self.assertEqual(report["missing"], [])
        self.assertEqual(report["next"]["skill"], "motion-designer")

    def test_init_refuses_to_overwrite_and_leaves_language_open(self):
        target = Path(self.temp.name) / "fresh"
        result = self.run_script(PRODUCER / "studio.py", "init", target, "--title", "Onboarding explainer",
                                 "--formats", "9x16,16x9")
        self.assertEqual(result.returncode, 0, result.stderr)
        project = json.loads((target / "project.json").read_text())
        self.assertIsNone(project["language"])
        self.assertEqual([f["id"] for f in project["formats"]], ["9x16", "16x9"])
        report = studio.validate(target)
        self.assertEqual(report["next"]["skill"], "director")
        again = self.run_script(PRODUCER / "studio.py", "init", target, "--title", "Again")
        self.assertEqual(again.returncode, 1)
        self.assertIn("already exists", again.stderr)

    def test_script_is_blocked_until_language_is_chosen(self):
        project = self.read("project")
        project["language"] = None
        self.put("project", project)
        studio.path_of(self.root, "script").unlink()
        studio.path_of(self.root, "words").unlink()
        studio.path_of(self.root, "shots").unlink()
        report = studio.validate(self.root)
        self.assertEqual(report["next"]["stage"], "script")
        self.assertIn("language", report["next"]["blocked"])

    def test_unapproved_lock_is_rejected(self):
        lock = self.read("lock")
        del lock["approved"]
        self.put("lock", lock)
        with self.assertRaisesRegex(studio.ContractError, "not approved"):
            studio.validate(self.root)

    def test_script_language_and_register_follow_the_project(self):
        script = self.read("script")
        script["language"] = "id"
        self.put("script", script)
        with self.assertRaisesRegex(studio.ContractError, "differs from project.language"):
            studio.validate(self.root)
        project = self.read("project")
        project["language"] = "id"
        self.put("project", project)
        with self.assertRaisesRegex(studio.ContractError, "register"):
            studio.validate(self.root)

    def test_keywords_must_be_spoken(self):
        script = self.read("script")
        script["lines"][0]["keywords"] = ["never said"]
        self.put("script", script)
        with self.assertRaisesRegex(studio.ContractError, "not in its text"):
            studio.validate(self.root)

    def test_shots_cannot_reuse_a_line_or_leave_gaps(self):
        shots = self.read("shots")
        shots["shots"][1]["lines"] = ["L01"]
        self.put("shots", shots)
        with self.assertRaisesRegex(studio.ContractError, "more than one shot"):
            studio.validate(self.root)
        shots = self.read("shots")
        shots["shots"][1]["lines"] = ["L02"]
        for index, shot in enumerate(shots["shots"]):
            shot["start"], shot["end"] = index * 5.0, index * 5.0 + 4.0
        self.put("shots", shots)
        with self.assertRaisesRegex(studio.ContractError, "Gap or overlap"):
            studio.validate(self.root)

    def test_write_keeps_previous_version(self):
        project = self.read("project")
        project["title"] = "Renamed"
        studio.write(self.root, "project", project)
        history = list((self.root / ".history").iterdir())
        self.assertEqual(len(history), 1)
        self.assertEqual(json.loads(history[0].read_text())["title"], "Jotly capture habit")


class LedgerTests(ProjectFixture):
    def setUp(self):
        super().setUp()
        studio.write(self.root, "ledger", ledger.empty())

    def test_capped_calls_need_an_approved_cap(self):
        decision = ledger.check(ledger.read(self.root), "elevenlabs", 100)
        self.assertFalse(decision["allowed"])
        self.assertIn("No approved", decision["reason"])
        result = self.run_script(PRODUCER / "ledger.py", "check", self.root, "--provider", "elevenlabs", "--estimate", 1)
        self.assertEqual(result.returncode, 2)

    def test_per_request_providers_cannot_use_a_cap(self):
        with self.assertRaises(studio.ContractError):
            ledger.check(ledger.read(self.root), "higgsfield-video", 10)
        with self.assertRaises(studio.ContractError):
            ledger.set_cap(self.root, "higgsfield-video", 100, "basis")

    def test_cap_refuses_overspend_and_warns_near_limit(self):
        ledger.set_cap(self.root, "elevenlabs", 1000, "300 chars x 3 takes")
        entry = ledger.record(self.root, "elevenlabs", "tts", 700, {"text": "a"})
        ledger.update(self.root, entry["id"], status="succeeded", actual=750)
        near = ledger.check(ledger.read(self.root), "elevenlabs", 100)
        self.assertTrue(near["allowed"])
        self.assertIn("85%", near["warning"])
        over = ledger.check(ledger.read(self.root), "elevenlabs", 300)
        self.assertFalse(over["allowed"])

    def test_failed_calls_do_not_count_but_unknown_calls_do(self):
        ledger.set_cap(self.root, "elevenlabs", 1000, "basis")
        failed = ledger.record(self.root, "elevenlabs", "tts", 600, {"text": "a"})
        ledger.update(self.root, failed["id"], status="failed")
        self.assertEqual(ledger.spent(ledger.read(self.root), "elevenlabs"), 0)
        unknown = ledger.record(self.root, "elevenlabs", "tts", 600, {"text": "b"})
        ledger.update(self.root, unknown["id"], status="unknown")
        self.assertEqual(ledger.spent(ledger.read(self.root), "elevenlabs"), 600)
        shown = json.loads(self.run_script(PRODUCER / "ledger.py", "show", self.root).stdout)
        self.assertEqual(shown["unresolved"], [unknown["id"]])

    def test_request_fingerprint_is_order_independent(self):
        self.assertEqual(ledger.request_sha256({"a": 1, "b": 2}), ledger.request_sha256({"b": 2, "a": 1}))
        self.assertNotEqual(ledger.request_sha256({"a": 1}), ledger.request_sha256({"a": 2}))


if __name__ == "__main__":
    unittest.main()
