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


DIRECTOR = SKILLS / "director/scripts/direction.py"
SCRIPT_TOOL = SKILLS / "scriptwriter/scripts/script_tool.py"


def option(option_id, pattern, structure):
    return {
        "id": option_id, "title": f"Option {option_id}", "logline": "A coach shows a habit that stops ideas getting lost.",
        "hook": {"pattern": pattern, "opening": "Chat bubbles pile up while the narrator asks a question."},
        "structure": structure,
        "beats": [{"id": "B1", "purpose": "hook", "summary": "Name the pain.", "seconds": 3},
                  {"id": "B2", "purpose": "cta", "summary": "Save it.", "seconds": 3}],
        "characters": [{"id": "narrator", "role": "coach", "acting_baseline": "Warm, quick, never salesy."}],
        "visual_plan": "Keywords land on the spoken word; one accent colour.",
        "audio_policy": {"voice": "narrator", "music": "none", "sfx": "none"},
        "risks": ["Generic pain question."],
    }


class DirectorTests(ProjectFixture):
    def write_options(self, options):
        path = self.root / "direction/options.json"
        path.write_text(json.dumps({"schema": "video-studio/direction-options@1", "options": options}))

    def test_options_must_be_genuinely_different(self):
        self.write_options([option("A", "pain-question", "steps"), option("B", "pain-question", "steps")])
        result = self.run_script(DIRECTOR, "check", self.root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("genuinely different", result.stdout)

    def test_check_flags_vague_words_and_missing_baselines(self):
        vague = option("A", "pain-question", "steps")
        vague["visual_plan"] = "A cinematic, engaging look."
        vague["characters"][0]["acting_baseline"] = ""
        self.write_options([vague, option("B", "result-first", "before-after")])
        report = json.loads(self.run_script(DIRECTOR, "check", self.root).stdout)
        self.assertTrue(any("acting_baseline" in error for error in report["errors"]))
        self.assertTrue(any("cinematic" in warning and "engaging" in warning for warning in report["warnings"]))

    def test_lock_records_user_approval_and_bumps_version(self):
        self.write_options([option("A", "pain-question", "steps"), option("B", "result-first", "before-after")])
        result = self.run_script(DIRECTOR, "lock", self.root, "--option", "B")
        self.assertEqual(result.returncode, 0, result.stderr)
        lock = self.read("lock")
        self.assertEqual((lock["version"], lock["source_option"], lock["hook"]["pattern"]), (2, "B", "result-first"))
        self.assertEqual(lock["approved"]["by"], "user")
        self.assertTrue((self.root / ".history").is_dir())
        missing = self.run_script(DIRECTOR, "lock", self.root, "--option", "Z")
        self.assertEqual(missing.returncode, 1)


class ScriptwriterTests(ProjectFixture):
    def estimate(self):
        result = self.run_script(SCRIPT_TOOL, "estimate", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_example_script_estimates_cleanly_without_counting_audio_tags(self):
        report = self.estimate()
        self.assertEqual(report["warnings"], [])
        self.assertAlmostEqual(report["beats"]["B1"]["planned"], round(8 / 2.6, 1))

    def test_flags_long_hook_vague_words_and_beat_order(self):
        script = self.read("script")
        script["lines"][0]["text"] = "Still losing your best ideas in random chats every single day while you scroll through endless amazing threads?"
        script["lines"][1], script["lines"][2] = script["lines"][2], script["lines"][1]
        self.put("script", script)
        warnings = " | ".join(self.estimate()["warnings"])
        self.assertIn("hook line", warnings)
        self.assertIn("amazing", warnings)
        self.assertIn("beat order", warnings)

    def test_indonesian_uses_slower_planning_pace(self):
        project = self.read("project")
        project["language"] = "id"
        self.put("project", project)
        script = self.read("script")
        script["language"], script["register"] = "id", "casual"
        script["lines"] = [{"id": "L01", "beat": "B1", "speaker": "narrator",
                            "text": "Masih sering lupa ide bagus yang nyelip di chat?", "keywords": ["ide bagus"]}]
        self.put("script", script)
        report = self.estimate()
        self.assertAlmostEqual(report["beats"]["B1"]["planned"], round(9 / 2.2, 1))
        self.assertTrue(any("Beats without lines" in warning for warning in report["warnings"]))


VOICE = SKILLS / "voice-director/scripts/voice.py"
sys.path.insert(0, str(VOICE.parent))
import voice  # noqa: E402

FAKE_ELEVENLABS = '''#!{python}
import base64, json, os, subprocess, sys, tempfile
log = os.environ["FAKE_LOG"]
with open(log, "a") as handle:
    handle.write(json.dumps(sys.argv[1:]) + "\\n")
if os.environ.get("FAKE_FAIL"):
    sys.stderr.write("quota exceeded")
    sys.exit(1)
body = json.loads(sys.stdin.read())
chars = list(body["text"])
starts = [round(i * 0.05, 3) for i in range(len(chars))]
ends = [round(s + 0.05, 3) for s in starts]
audio = b"not-audio"
if os.environ.get("FAKE_REAL_AUDIO"):
    with tempfile.TemporaryDirectory() as temp:
        out = os.path.join(temp, "a.mp3")
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=f=220:d=%.2f" % ends[-1], out], check=True)
        audio = open(out, "rb").read()
print(json.dumps({{"audio_base64": base64.b64encode(audio).decode(),
                  "alignment": {{"characters": chars, "character_start_times_seconds": starts,
                                "character_end_times_seconds": ends}}}}))
'''


class VoiceDirectorTests(ProjectFixture):
    def setUp(self):
        super().setUp()
        for key in ("words", "shots"):
            studio.path_of(self.root, key).unlink()
        studio.write(self.root, "ledger", ledger.empty())
        config = json.loads((SKILLS / "voice-director/assets/voice-config.example.json").read_text())
        config["voices"]["narrator"]["voice_id"] = "voice123"
        studio.write(self.root, "voice_config", config)
        bin_dir = Path(self.temp.name) / "bin"
        bin_dir.mkdir()
        fake = bin_dir / "elevenlabs"
        fake.write_text(FAKE_ELEVENLABS.format(python=sys.executable))
        fake.chmod(0o755)
        self.log = Path(self.temp.name) / "calls.log"
        self.env = {"VIDEO_STUDIO_ELEVENLABS_BIN": str(fake), "FAKE_LOG": str(self.log)}
        self.patch_env(self.env)

    def patch_env(self, values):
        import os
        saved = {key: os.environ.get(key) for key in values}
        os.environ.update(values)

        def restore():
            for key, value in saved.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        self.addCleanup(restore)

    def calls(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def chars(self):
        return sum(len(line["text"]) for line in self.read("script")["lines"]) + 2 * 5

    def test_char_alignment_drops_audio_tags_and_whitespace(self):
        text = "[warm voice] Hi there"
        alignment = {"characters": list(text), "character_start_times_seconds": [i / 10 for i in range(len(text))],
                     "character_end_times_seconds": [i / 10 + 0.1 for i in range(len(text))]}
        words = voice.char_words(alignment)
        self.assertEqual([w["text"] for w in words], ["Hi", "there"])
        self.assertAlmostEqual(words[0]["start"], 1.3)

    def test_plan_is_a_dry_run_with_estimate(self):
        result = self.run_script(VOICE, "plan", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertEqual(plan["characters"], self.chars())
        self.assertEqual(plan["requests"][0]["body"]["language_code"], "en")
        self.assertNotIn("output_format", plan["requests"][0]["body"])
        self.assertFalse(plan["cap"]["allowed"])
        self.assertEqual(self.calls(), [])

    def test_generate_refuses_without_cap_and_sends_nothing(self):
        result = self.run_script(VOICE, "generate", self.root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("No approved", result.stderr)
        self.assertEqual(self.calls(), [])
        self.assertEqual(ledger.read(self.root)["entries"], [])

    def test_generate_writes_timed_words_and_ledger(self):
        ledger.set_cap(self.root, "elevenlabs", 5000, "test cap")
        result = self.run_script(VOICE, "generate", self.root, "--note", "first")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.calls()), 1)
        args = json.loads(self.calls()[0])
        self.assertIn("--no-extract", args)
        self.assertEqual(args[args.index("--output-format") + 1], "mp3_44100_128")
        words = self.read("words")
        self.assertNotIn("[curious]", [w["text"] for w in words["words"]])
        self.assertEqual(words["words"][0]["line"], "L01")
        self.assertEqual(words["words"][-1]["line"], "L06")
        entry = ledger.read(self.root)["entries"][0]
        self.assertEqual((entry["status"], entry["estimate"]), ("succeeded", float(self.chars())))
        studio.validate(self.root)

    def test_provider_refusal_is_recorded_as_failed(self):
        ledger.set_cap(self.root, "elevenlabs", 5000, "test cap")
        self.patch_env({"FAKE_FAIL": "1"})
        result = self.run_script(VOICE, "generate", self.root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("quota exceeded", result.stderr)
        self.assertEqual(ledger.read(self.root)["entries"][0]["status"], "failed")
        self.assertIsNone(studio.load(self.root, "words", required=False))

    def test_alignment_word_count_mismatch_is_refused(self):
        with self.assertRaisesRegex(studio.ContractError, "inspect the take"):
            voice.assign_lines([{"text": "Hi", "start": 0, "end": 0.1}], self.read("script"), ["L01"])

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg needed for lines mode")
    def test_lines_mode_joins_takes_with_gaps(self):
        ledger.set_cap(self.root, "elevenlabs", 5000, "test cap")
        config = self.read("voice_config")
        config["mode"], config["line_gap"] = "lines", 0.5
        self.put("voice_config", config)
        self.patch_env({"FAKE_REAL_AUDIO": "1"})
        result = self.run_script(VOICE, "generate", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.calls()), 6)
        words = self.read("words")
        l02 = next(w for w in words["words"] if w["line"] == "L02")
        last_l01 = [w for w in words["words"] if w["line"] == "L01"][-1]
        self.assertGreater(l02["start"] - last_l01["end"], 0.45)
        self.assertGreater(words["duration"], words["words"][-1]["end"] - 0.1)


SHOTS = SKILLS / "shot-designer/scripts/shots.py"


class ShotDesignerTests(ProjectFixture):
    def lint(self):
        result = self.run_script(SHOTS, "lint", self.root)
        return result.returncode, json.loads(result.stdout)

    def test_time_cuts_before_first_word_and_holds_the_end(self):
        result = self.run_script(SHOTS, "time", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        shots, words = self.read("shots")["shots"], self.read("words")
        self.assertEqual(shots[0]["start"], 0.0)
        first_l02 = next(w["start"] for w in words["words"] if w["line"] == "L02")
        self.assertAlmostEqual(shots[1]["start"], round(first_l02 - 0.15, 3))
        self.assertAlmostEqual(shots[-1]["end"], round(words["duration"] + 0.8, 3))
        for before, after in zip(shots, shots[1:]):
            self.assertEqual(before["end"], after["start"])
        code, report = self.lint()
        self.assertEqual((code, report["errors"]), (0, []))
        self.assertEqual(report["warnings"], [])

    def test_lint_requires_a_picture_for_every_line_and_motivation(self):
        shots = self.read("shots")
        shots["shots"][2]["lines"] = ["L03", "L04"]
        shots["shots"][2]["visual"]["items"] = shots["shots"][2]["visual"]["items"][:2]
        shots["shots"][0]["motivation"] = ""
        self.put("shots", shots)
        code, report = self.lint()
        self.assertEqual(code, 1)
        joined = " | ".join(report["errors"])
        self.assertIn("L05", joined)
        self.assertIn("S01 needs a motivation", joined)

    def test_lint_flags_vague_camera_shots_and_mode_fields(self):
        shots = self.read("shots")
        shots["shots"][0] = {"id": "S01", "kind": "camera", "beat": "B1", "lines": ["L01"],
                             "motivation": "Make it cinematic", "framing": "MCU", "movement": "smooth and epic",
                             "action": "", "light_source": "window left", "sound": "room tone"}
        shots["shots"][1]["visual"] = {"mode": "stat", "label": "faster"}
        self.put("shots", shots)
        code, report = self.lint()
        self.assertEqual(code, 1)
        self.assertTrue(any("needs action" in e for e in report["errors"]))
        self.assertTrue(any("needs value" in e for e in report["errors"]))
        self.assertTrue(any("cinematic" in w for w in report["warnings"]))
        self.assertTrue(any("no direction" in w for w in report["warnings"]))

    def test_steps_must_reveal_on_their_own_lines(self):
        shots = self.read("shots")
        shots["shots"][2]["visual"]["items"][0]["line"] = "L01"
        self.put("shots", shots)
        code, report = self.lint()
        self.assertTrue(any("own lines" in e for e in report["errors"]))

    def test_long_shot_without_visible_changes_warns(self):
        self.run_script(SHOTS, "time", self.root)
        shots = self.read("shots")
        merged = shots["shots"][0]
        merged["lines"] = ["L01", "L02", "L03", "L04", "L05"]
        merged["visual"] = {"mode": "title", "title": "One long title", "keywords": False}
        merged["end"] = shots["shots"][3]["start"]
        shots["shots"] = [merged, shots["shots"][3]]
        self.put("shots", shots)
        code, report = self.lint()
        self.assertTrue(any("visible change" in w for w in report["warnings"]))

    def test_time_needs_narration(self):
        studio.path_of(self.root, "words").unlink()
        result = self.run_script(SHOTS, "time", self.root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("voice/words.json", result.stderr)


COMPOSE = SKILLS / "motion-designer/scripts/compose.mjs"


def node_ok():
    if not shutil.which("node"):
        return False
    version = subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip().lstrip("v")
    return int(version.split(".")[0]) >= 20


@unittest.skipUnless(node_ok(), "Node.js 20+ needed for the composition generator")
class MotionDesignerTests(ProjectFixture):
    def setUp(self):
        super().setUp()
        self.assertEqual(self.run_script(SHOTS, "time", self.root).returncode, 0)

    def compose(self, *args):
        return subprocess.run(["node", str(COMPOSE), str(self.root), *args], capture_output=True, text=True)

    def html(self, canvas):
        return (self.root / "compositions" / canvas / "index.html").read_text()

    def test_builds_each_canvas_with_contract_and_word_cues(self):
        result = self.compose()
        self.assertEqual(result.returncode, 0, result.stderr)
        built = json.loads(result.stdout)
        self.assertEqual([b["canvas"] for b in built], ["9x16", "16x9"])
        shots, words = self.read("shots")["shots"], self.read("words")
        vertical, wide = self.html("9x16"), self.html("16x9")
        self.assertIn(f'data-duration="{shots[-1]["end"]}"', vertical)
        self.assertIn('data-width="1080" data-height="1920"', vertical)
        self.assertIn('data-width="1920" data-height="1080"', wide)
        self.assertIn('window.__timelines["main"] = tl;', vertical)
        self.assertIn("text-align:center", vertical)
        self.assertIn("text-align:left", wide)
        best = next(w for w in words["words"] if w["text"] == "best")
        self.assertIn(f'class="word key">best</span>', vertical)
        cue = round(best["start"] - 0.05, 3)
        self.assertIn(f"{cue});", vertical)
        three = next(w for w in words["words"] if w["text"] == "three-step")
        self.assertIn(">three-step</span>", vertical)
        self.assertIn(f"{round(three['start'] - 0.05, 3)});", vertical)
        self.assertIn("cdn.jsdelivr.net/npm/gsap@3.14.2", vertical)
        manifest = json.loads((self.root / "compositions/9x16/build.json").read_text())
        self.assertFalse(manifest["localGsap"])
        self.assertIsNone(manifest["narration"])
        self.assertNotIn("<audio", vertical)

    def test_copies_narration_and_local_gsap(self):
        audio = self.root / self.read("words")["audio"]
        audio.parent.mkdir(parents=True, exist_ok=True)
        audio.write_bytes(b"fake-mp3")
        gsap = Path(self.temp.name) / "gsap.min.js"
        gsap.write_text("window.gsap={};")
        result = self.compose("--gsap", gsap, "--only", "9x16")
        self.assertEqual(result.returncode, 0, result.stderr)
        html = self.html("9x16")
        self.assertIn('src="assets/runtime/gsap.min.js"', html)
        self.assertIn('<audio id="narration" src="assets/voice/takes/T1/narration.mp3"', html)
        self.assertTrue((self.root / "compositions/9x16/assets/voice/takes/T1/narration.mp3").is_file())
        self.assertFalse((self.root / "compositions/16x9").exists())

    def test_refuses_to_overwrite_hand_edits_without_force(self):
        self.assertEqual(self.compose().returncode, 0)
        page = self.root / "compositions/9x16/index.html"
        page.write_text(page.read_text().replace("Save this", "Save this now"))
        refused = self.compose()
        self.assertEqual(refused.returncode, 1)
        self.assertIn("edited after generation", refused.stderr)
        self.assertIn("Save this now", page.read_text())
        self.assertEqual(self.compose("--force").returncode, 0)
        self.assertNotIn("Save this now", page.read_text())

    def test_refuses_untimed_or_stale_shots(self):
        words = self.read("words")
        words["duration"] = round(words["duration"] + 0.5, 3)
        self.put("words", words)
        stale = self.compose()
        self.assertEqual(stale.returncode, 1)
        self.assertIn("different narration take", stale.stderr)
        shots = self.read("shots")
        for shot in shots["shots"]:
            shot.pop("start"), shot.pop("end")
        self.put("shots", shots)
        untimed = self.compose()
        self.assertEqual(untimed.returncode, 1)
        self.assertIn("not timed", untimed.stderr)

    def test_keyword_must_be_in_the_line_timings(self):
        words = self.read("words")
        for word in words["words"]:
            if word["text"] == "best":
                word["text"] = "worst"
        self.put("words", words)
        result = self.compose()
        self.assertEqual(result.returncode, 1)
        self.assertIn('Keyword "best ideas"', result.stderr)


EDIT = SKILLS / "editor/scripts/edit.py"
QC = SKILLS / "qc-reviewer/scripts/qc.py"
sys.path.insert(0, str(EDIT.parent))
import edit  # noqa: E402

FAKE_HYPERFRAMES = '''#!{python}
import json, subprocess, sys
out = sys.argv[sys.argv.index("-o") + 1]
build = json.load(open("build.json"))
size = "%dx%d" % (build["width"], build["height"])
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x1A1D24:s=%s:r=30:d=%s" % (size, build["duration"]),
                "-f", "lavfi", "-i", "sine=f=330:d=%s" % build["duration"], "-af", "volume=-12dB",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", out], check=True)
'''


class CaptionTests(unittest.TestCase):
    def words(self):
        return json.loads((EXAMPLE / "voice/words.json").read_text())["words"]

    def test_cues_follow_lines_and_wrap_to_two_lines(self):
        cues = edit.cues(self.words(), "en")
        self.assertEqual(len(cues), 6)
        self.assertEqual(cues[0]["text"], "Still losing your best\nideas in random chats?")
        for cue in cues:
            self.assertLessEqual(len(cue["text"].split("\n")), 2)
            self.assertTrue(all(len(part) <= 42 for part in cue["text"].split("\n")))
        for before, after in zip(cues, cues[1:]):
            self.assertLessEqual(before["end"], after["start"])

    def test_indonesian_lines_are_shorter_and_stamps_are_formatted(self):
        words = [{"text": t, "start": i * 0.4, "end": i * 0.4 + 0.3, "line": "L01"}
                 for i, t in enumerate("Simpan video ini supaya kamu nggak lupa langkah pentingnya nanti".split())]
        cue = edit.cues(words, "id")[0]
        self.assertTrue(all(len(part) <= 38 for part in cue["text"].split("\n")))
        self.assertEqual(edit.stamp(3725.5, ","), "01:02:05,500")


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg needed for render and QC tests")
class EditorAndQcTests(ProjectFixture):
    def setUp(self):
        super().setUp()
        self.assertEqual(self.run_script(SHOTS, "time", self.root).returncode, 0)
        shots = self.read("shots")["shots"]
        project = self.read("project")
        for fmt in project["formats"]:
            folder = self.root / "compositions" / fmt["id"]
            folder.mkdir(parents=True)
            (folder / "index.html").write_text("<!doctype html>")
            (folder / "build.json").write_text(json.dumps({"width": fmt["width"], "height": fmt["height"],
                                                           "duration": shots[-1]["end"], "inputHashes": {}, "localGsap": True}))
        fake = Path(self.temp.name) / "hyperframes"
        fake.write_text(FAKE_HYPERFRAMES.format(python=sys.executable))
        fake.chmod(0o755)
        import os
        previous = os.environ.get("VIDEO_STUDIO_HYPERFRAMES")
        os.environ["VIDEO_STUDIO_HYPERFRAMES"] = str(fake)
        self.addCleanup(lambda: os.environ.pop("VIDEO_STUDIO_HYPERFRAMES") if previous is None
                        else os.environ.__setitem__("VIDEO_STUDIO_HYPERFRAMES", previous))

    def test_renders_are_versioned_and_never_overwritten(self):
        first = self.run_script(EDIT, "render", self.root, "--canvas", "9x16")
        self.assertEqual(first.returncode, 0, first.stderr)
        second = self.run_script(EDIT, "render", self.root, "--canvas", "9x16")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertTrue((self.root / "renders/v1/9x16.mp4").is_file())
        manifest = json.loads((self.root / "renders/v2/manifest.json").read_text())
        self.assertEqual([r["canvas"] for r in manifest["renders"]], ["9x16"])
        self.assertEqual(len(manifest["renders"][0]["sha256"]), 64)

    def test_finish_normalizes_and_qc_passes_then_catches_problems(self):
        self.assertEqual(self.run_script(EDIT, "render", self.root).returncode, 0)
        self.assertEqual(self.run_script(EDIT, "captions", self.root).returncode, 0)
        finished = self.run_script(EDIT, "finish", self.root)
        self.assertEqual(finished.returncode, 0, finished.stderr)
        for item in json.loads(finished.stdout):
            self.assertAlmostEqual(item["measured_lufs"], -14.0, delta=1.0)
        result = self.run_script(QC, "final", self.root)
        report = json.loads(result.stdout)
        self.assertEqual((result.returncode, report["failed"], report["warnings"]), (0, 0, 0), result.stdout)
        self.assertTrue((self.root / "qc/frames/v1/9x16/S04.png").is_file())
        self.assertIn("Watch every canvas start to finish with sound", report["manual_checks_remaining"])
        project = self.read("project")
        project["formats"][0]["height"] = 1350
        self.put("project", project)
        (self.root / "captions/en.srt").unlink()
        broken = json.loads(self.run_script(QC, "final", self.root).stdout)
        statuses = {(c["canvas"], c["check"]): c["status"] for c in broken["checks"]}
        self.assertEqual(statuses[("9x16", "dimensions")], "fail")
        self.assertEqual(statuses[("all", "captions")], "warn")

    def test_burn_in_requires_captions_and_render_requires_builds(self):
        self.assertEqual(self.run_script(EDIT, "render", self.root, "--canvas", "1x1").returncode, 1)
        self.assertEqual(self.run_script(EDIT, "render", self.root, "--canvas", "16x9").returncode, 0)
        burned = self.run_script(EDIT, "finish", self.root, "--burn-captions")
        self.assertEqual(burned.returncode, 1)
        self.assertIn("captions", burned.stderr)
        shutil.rmtree(self.root / "compositions/9x16")
        missing = self.run_script(EDIT, "render", self.root, "--canvas", "9x16")
        self.assertEqual(missing.returncode, 1)
        self.assertIn("has not been built", missing.stderr)



CINEMATIC = SKILLS / "studio-producer/assets/example-cinematic"


class CinematicFixture(ProjectFixture):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "film"
        shutil.copytree(CINEMATIC, self.root)
        studio.write(self.root, "ledger", ledger.empty())


class CinematicContractTests(CinematicFixture):
    def test_status_follows_the_cinematic_recipe_without_a_script(self):
        report = studio.validate(self.root)
        self.assertIn("bible/bible.json", report["valid"])
        self.assertEqual(report["next"], {"stage": "takes", "skill": "ai-video-generator"})

    def test_bible_needs_preserve_lists_and_environment_light(self):
        bible = self.read("bible")
        bible["references"][1]["light_sources"] = []
        self.put("bible", bible)
        with self.assertRaisesRegex(studio.ContractError, "light source"):
            studio.validate(self.root)
        bible["references"][1]["light_sources"] = ["sun"]
        bible["references"][0]["preserve"] = []
        self.put("bible", bible)
        with self.assertRaisesRegex(studio.ContractError, "preserve"):
            studio.validate(self.root)

    def test_shots_must_use_known_refs_and_consecutive_takes(self):
        shots = self.read("shots")
        shots["shots"][0]["refs"] = ["ghost"]
        self.put("shots", shots)
        with self.assertRaisesRegex(studio.ContractError, "unknown bible entry"):
            studio.validate(self.root)
        shots["shots"][0]["refs"] = ["courier"]
        shots["shots"][2]["take"] = "T1"
        shots["shots"][1]["take"] = "T2"
        self.put("shots", shots)
        with self.assertRaisesRegex(studio.ContractError, "not consecutive"):
            studio.validate(self.root)

    def test_time_uses_durations_without_narration(self):
        result = self.run_script(SHOTS, "time", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        shots = self.read("shots")["shots"]
        self.assertEqual([(s["start"], s["end"]) for s in shots], [(0.0, 3.0), (3.0, 6.0), (6.0, 9.5), (9.5, 13.0)])
        report = json.loads(self.run_script(SHOTS, "lint", self.root).stdout)
        self.assertEqual(report["errors"], [])

    def test_lint_flags_long_takes_flips_and_missing_environment(self):
        shots = self.read("shots")
        shots["max_take_seconds"] = 5
        shots["shots"][1]["screen_direction"] = "right-to-left"
        shots["shots"][1]["refs"] = ["courier", "drone"]
        del shots["shots"][3]["duration"]
        self.put("shots", shots)
        report = json.loads(self.run_script(SHOTS, "lint", self.root).stdout)
        errors, warnings = " | ".join(report["errors"]), " | ".join(report["warnings"])
        self.assertIn("Take T1 runs 6.0s", errors)
        self.assertIn("S04 needs a duration", errors)
        self.assertIn("Screen direction flips between S01 and S02", warnings)
        self.assertIn("S02 has no environment reference", warnings)


class RequestApprovalTests(CinematicFixture):
    request = {"model": "seedance_2_5", "prompt": "A courier sprints", "duration": 6, "aspect_ratio": "16:9"}

    def test_submission_needs_an_approval_of_the_exact_request(self):
        with self.assertRaisesRegex(studio.ContractError, "No approval matches"):
            ledger.consume_approval(self.root, "higgsfield-video", self.request)
        ledger.approve(self.root, "higgsfield-video", "generate_video", self.request, 120)
        changed = dict(self.request, duration=8)
        with self.assertRaisesRegex(studio.ContractError, "No approval matches"):
            ledger.consume_approval(self.root, "higgsfield-video", changed)
        entry = ledger.consume_approval(self.root, "higgsfield-video", self.request)
        self.assertEqual(entry["status"], "submitted")
        self.assertEqual(ledger.spent(ledger.read(self.root), "higgsfield-video"), 120)
        with self.assertRaisesRegex(studio.ContractError, "No approval matches"):
            ledger.consume_approval(self.root, "higgsfield-video", self.request)

    def test_per_request_and_capped_providers_stay_separate(self):
        with self.assertRaises(studio.ContractError):
            ledger.approve(self.root, "elevenlabs", "tts", self.request, 10)
        request_file = Path(self.temp.name) / "request.json"
        request_file.write_text(json.dumps(self.request))
        result = self.run_script(PRODUCER / "ledger.py", "approve", self.root, "--provider", "higgsfield-video",
                                 "--operation", "generate_video", "--request", request_file, "--estimate", 90)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIsNotNone(ledger.find_approval(ledger.read(self.root), "higgsfield-video", self.request))



ANALYZE = SKILLS / "reference-analyst/scripts/analyze.py"
sys.path.insert(0, str(ANALYZE.parent))
import analyze  # noqa: E402


class ReferenceShotTests(unittest.TestCase):
    def test_short_segments_merge_into_neighbours(self):
        shots = analyze.shots_from([2.0, 2.1, 5.0], 8.0)
        self.assertEqual([(s["start"], s["end"]) for s in shots], [(0.0, 2.1), (2.1, 5.0), (5.0, 8.0)])


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg needed for reference analysis")
class ReferenceAnalystTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        self.video = self.dir / "ref.mp4"
        colors = ["black", "white", "black"]
        inputs = []
        for color in colors:
            inputs += ["-f", "lavfi", "-i", f"color=c={color}:s=360x640:r=30:d=2"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-f", "lavfi", "-i", "sine=f=440:d=6",
                        "-filter_complex", "[0][1][2]concat=n=3:v=1:a=0[v]", "-map", "[v]", "-map", "3",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(self.video)], check=True)

    def test_detects_cuts_frames_and_audio(self):
        out = self.dir / "analysis"
        result = subprocess.run([sys.executable, str(ANALYZE), str(self.video), "--out", str(out)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads((out / "analysis.json").read_text())
        self.assertEqual(data["metadata"]["orientation"], "vertical")
        self.assertEqual(data["pacing"]["shots"], 3)
        self.assertAlmostEqual(data["shots"][1]["start"], 2.0, delta=0.1)
        self.assertTrue((out / "contact-sheet.png").is_file())
        self.assertTrue((out / data["shots"][0]["frame"]).is_file())
        self.assertIsNotNone(data["audio"]["integrated_lufs"])
        again = subprocess.run([sys.executable, str(ANALYZE), str(self.video), "--out", str(out)], capture_output=True, text=True)
        self.assertEqual(again.returncode, 1)
        self.assertIn("new directory", again.stderr)

    def test_transcription_requires_an_approved_cap(self):
        project = self.dir / "project"
        shutil.copytree(EXAMPLE, project)
        studio.write(project, "ledger", ledger.empty())
        result = subprocess.run([sys.executable, str(ANALYZE), str(self.video), "--out", str(self.dir / "a2"),
                                 "--transcribe-estimate", "50", "--project", str(project)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("No approved", result.stderr)



BIBLE = SKILLS / "continuity-bible/scripts/bible.py"
KEYFRAMES = SKILLS / "keyframe-generator/scripts/keyframes.py"


class BibleAndKeyframeTests(CinematicFixture):
    def png(self, name="out.png"):
        path = Path(self.temp.name) / name
        path.write_bytes(b"\x89PNG\r\n\x1a\nfake")
        return path

    def test_check_and_negatives(self):
        report = json.loads(self.run_script(BIBLE, "check", self.root).stdout)
        self.assertTrue(any("courier has no reference image" in w for w in report["warnings"]))
        self.assertEqual(self.run_script(BIBLE, "negatives", self.root).returncode, 0)
        negatives = self.read("bible")["negatives"]
        self.assertTrue(any("teal waterproof jacket" in n for n in negatives))
        self.assertIn("no added text, subtitles, logos or watermarks", negatives)

    def test_reference_images_run_under_the_image_cap(self):
        self.assertEqual(self.run_script(BIBLE, "sheets", self.root).returncode, 0)
        refused = self.run_script(BIBLE, "reserve", self.root, "--ref", "courier", "--estimate", 4)
        self.assertEqual(refused.returncode, 1)
        self.assertIn("No approved higgsfield-image cap", refused.stderr)
        ledger.set_cap(self.root, "higgsfield-image", 40, "12 images x ~3 credits")
        entry = json.loads(self.run_script(BIBLE, "reserve", self.root, "--ref", "courier", "--estimate", 4).stdout)
        result = self.run_script(BIBLE, "add-image", self.root, "--ref", "courier", "--entry", entry["id"],
                                 "--file", self.png(), "--job-id", "job-1")
        self.assertEqual(result.returncode, 0, result.stderr)
        image = self.read("bible")["references"][0]["images"][0]
        self.assertEqual(image, "bible/images/courier-v1.png")
        self.assertTrue((self.root / (image + ".json")).is_file())
        status = ledger.read(self.root)["entries"][-1]
        self.assertEqual((status["status"], status["job_id"]), ("succeeded", "job-1"))
        self.assertEqual(self.run_script(BIBLE, "link", self.root, "--ref", "courier", "--element",
                                         "11111111-2222-4333-8444-555555555555").returncode, 0)

    def test_keyframe_prompts_use_elements_only_on_element_models(self):
        bible = self.read("bible")
        bible["references"][0]["higgsfield_element_id"] = "11111111-2222-4333-8444-555555555555"
        bible["references"][0]["images"] = ["bible/images/courier.png"]
        self.put("bible", bible)
        self.assertEqual(self.run_script(KEYFRAMES, "plan", self.root, "--canvas", "16x9").returncode, 0)
        requests = json.loads((self.root / "keyframes/requests-16x9.json").read_text())["requests"]
        self.assertEqual(len(requests), 4)
        self.assertIn("<<<11111111-2222-4333-8444-555555555555>>>", requests[0]["prompt"])
        self.assertIn("low sun frame left", requests[0]["prompt"])
        self.assertEqual(requests[0]["aspect_ratio"], "16:9")
        self.assertEqual(self.run_script(KEYFRAMES, "plan", self.root, "--canvas", "9x16", "--model", "gpt_image_2_5",
                                         "--ends", "--shot", "S01").returncode, 0)
        other = json.loads((self.root / "keyframes/requests-9x16.json").read_text())["requests"]
        self.assertEqual([(r["shot"], r["frame"]) for r in other], [("S01", "start"), ("S01", "end")])
        self.assertNotIn("<<<", other[0]["prompt"])
        self.assertEqual(other[0]["medias"], [{"role": "image", "ref": "courier", "asset": "bible/images/courier.png"}])

    def test_record_versions_keyframes_and_failures_stay_counted(self):
        ledger.set_cap(self.root, "higgsfield-image", 40, "basis")
        self.run_script(KEYFRAMES, "plan", self.root, "--canvas", "16x9")
        paths = []
        for n in range(2):
            entry = json.loads(self.run_script(KEYFRAMES, "reserve", self.root, "--canvas", "16x9", "--shot", "S01",
                                               "--estimate", 3).stdout)
            result = self.run_script(KEYFRAMES, "record", self.root, "--canvas", "16x9", "--shot", "S01",
                                     "--entry", entry["id"], "--file", self.png(f"k{n}.png"))
            self.assertEqual(result.returncode, 0, result.stderr)
            paths.append(json.loads(result.stdout)["keyframe"])
        self.assertEqual(paths, ["keyframes/16x9/S01-start-v1.png", "keyframes/16x9/S01-start-v2.png"])
        self.assertEqual(self.read("shots")["shots"][0]["keyframes"]["16x9"]["start"], paths[1])
        entry = json.loads(self.run_script(KEYFRAMES, "reserve", self.root, "--canvas", "16x9", "--shot", "S02",
                                           "--estimate", 3).stdout)
        self.run_script(KEYFRAMES, "fail", self.root, "--entry", entry["id"], "--uncertain")
        self.assertEqual(ledger.spent(ledger.read(self.root), "higgsfield-image"), 9)



TAKES = SKILLS / "ai-video-generator/scripts/takes.py"


def solid_video(path, colors, seconds, size="640x360"):
    inputs = []
    for color in colors:
        inputs += ["-f", "lavfi", "-i", f"color=c={color}:s={size}:r=24:d={seconds}"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex",
                    "".join(f"[{i}]" for i in range(len(colors))) + f"concat=n={len(colors)}:v=1:a=0[v]",
                    "-map", "[v]", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)], check=True)
    return path


class TakePlanTests(CinematicFixture):
    def setUp(self):
        super().setUp()
        self.assertEqual(self.run_script(SHOTS, "time", self.root).returncode, 0)
        self.assertEqual(self.run_script(BIBLE, "negatives", self.root).returncode, 0)

    def takes(self, *args):
        result = self.run_script(TAKES, *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_plan_compiles_timed_multi_shot_prompts(self):
        planned = self.takes("plan", self.root, "--canvas", "16x9")
        self.assertEqual(planned["planned"], ["T1-16x9", "T2-16x9"])
        request = self.takes("show", self.root, "--take", "T2-16x9")
        self.assertEqual((request["duration"], request["aspect_ratio"], request["model"]), (7, "16:9", "seedance_2_5"))
        prompt = request["prompt"]
        for fragment in ("REFERENCE ROLES:", "00:00–00:03.50 — S03", "00:03.50–00:07 — S04", "slow crane up following the drone",
                         "PERFORMANCE:", "AUDIO: music: none", "AVOID:"):
            self.assertIn(fragment, prompt)
        self.assertNotIn("Maintain screen direction", prompt)  # both T2 shots are neutral

    def test_replanning_a_draft_updates_it_and_keyframes_become_start_images(self):
        self.takes("plan", self.root, "--canvas", "16x9")
        shots = self.read("shots")
        shots["shots"][0]["keyframes"] = {"16x9": {"start": "keyframes/16x9/S01-start-v1.png"}}
        self.put("shots", shots)
        self.takes("plan", self.root, "--canvas", "16x9", "--take", "T1")
        takes = self.read("takes")["takes"]
        self.assertEqual([t["id"] for t in takes], ["T1-16x9", "T2-16x9"])
        self.assertEqual(takes[0]["request"]["medias"][0], {"role": "start_image", "asset": "keyframes/16x9/S01-start-v1.png"})

    def test_submission_requires_approval_of_the_unchanged_request(self):
        self.takes("plan", self.root, "--canvas", "16x9")
        refused = self.run_script(TAKES, "submit", self.root, "--take", "T1-16x9")
        self.assertEqual(refused.returncode, 1)
        self.assertIn("not approved", refused.stderr)
        self.takes("approve", self.root, "--take", "T1-16x9", "--estimate", 60)
        takes = self.read("takes")
        takes["takes"][0]["request"]["duration"] = 8
        self.put("takes", takes)
        changed = self.run_script(TAKES, "submit", self.root, "--take", "T1-16x9")
        self.assertEqual(changed.returncode, 1)
        self.assertIn("changed after approval", changed.stderr)
        takes["takes"][0]["request"]["duration"] = 6
        self.put("takes", takes)
        request = self.takes("submit", self.root, "--take", "T1-16x9")
        self.assertEqual(request["duration"], 6)
        self.takes("job", self.root, "--take", "T1-16x9", "--job-id", "job-42")
        entry = next(e for e in ledger.read(self.root)["entries"] if e["provider"] == "higgsfield-video")
        self.assertEqual((entry["status"], entry["job_id"], entry["estimate"]), ("submitted", "job-42", 60))
        again = self.run_script(TAKES, "submit", self.root, "--take", "T1-16x9")
        self.assertEqual(again.returncode, 1)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg needed to split takes")
    def test_ingest_splits_on_matching_cuts_and_flags_mismatches(self):
        self.takes("plan", self.root, "--canvas", "16x9")
        for take in ("T1-16x9", "T2-16x9"):
            self.takes("approve", self.root, "--take", take, "--estimate", 50)
            self.takes("submit", self.root, "--take", take)
        good = solid_video(Path(self.temp.name) / "t1.mp4", ["black", "white"], 3)
        result = self.takes("ingest", self.root, "--take", "T1-16x9", "--file", good)
        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(sorted(result["clips"]), ["S01", "S02"])
        self.assertTrue((self.root / result["clips"]["S02"]).is_file())
        bad = solid_video(Path(self.temp.name) / "t2.mp4", ["black"], 7)
        flagged = self.takes("ingest", self.root, "--take", "T2-16x9", "--file", bad)
        self.assertEqual(flagged["status"], "needs-split")
        self.assertIsNone(flagged["clips"])
        fixed = self.takes("split", self.root, "--take", "T2-16x9", "--at", "3.5")
        self.assertEqual(fixed["status"], "succeeded")
        blocked = self.run_script(TAKES, "select", self.root, "--take", "T1-16x9")
        self.assertEqual(blocked.returncode, 1)
        self.assertIn("has not passed dailies", blocked.stderr)
        review = json.loads(self.run_script(QC, "dailies", self.root, "--take", "T1-16x9").stdout)
        self.assertTrue(review["shots"]["S01"]["checks"]["duration"])
        self.assertTrue((self.root / "qc/dailies/T1-16x9/sheet.png").is_file())
        self.assertEqual(review["shots"]["S02"]["pillars"]["outfit"]["status"], "unreviewed")
        no_note = self.run_script(QC, "verdict", self.root, "--take", "T1-16x9", "--shot", "S02", "--pillar", "outfit", "--fail")
        self.assertEqual(no_note.returncode, 1)
        self.run_script(QC, "verdict", self.root, "--take", "T1-16x9", "--shot", "S02", "--pillar", "outfit", "--fail",
                        "--note", "bag moved to the right shoulder")
        todo = json.loads(self.run_script(QC, "retakes", self.root).stdout)
        self.assertEqual([(t["shot"], t["failed"]) for t in todo], [("S02", ["outfit"])])
        for shot in ("S01", "S02"):
            self.run_script(QC, "verdict", self.root, "--take", "T1-16x9", "--shot", shot, "--pillar", "all", "--pass")
        self.assertEqual(json.loads(self.run_script(QC, "retakes", self.root).stdout), [])
        self.takes("select", self.root, "--take", "T1-16x9")
        self.takes("select", self.root, "--take", "T2-16x9", "--skip-dailies", "test fixture")
        self.assertEqual(self.read("takes")["takes"][1]["dailies_skipped"][0]["reason"], "test fixture")
        studio.validate(self.root)
        retake = self.takes("retake", self.root, "--canvas", "16x9", "--shot", "S03", "--with-end")["planned"]
        take = next(t for t in self.read("takes")["takes"] if t["id"] == retake)
        roles = [m["role"] for m in take["request"]["medias"]]
        self.assertEqual((roles[0], roles[-1], take["duration"], take["retake_of"]), ("start_image", "end_image", 4, "T2-16x9"))
        self.assertTrue((self.root / take["request"]["medias"][0]["asset"]).is_file())
        self.assertIn("CONTINUITY", take["request"]["prompt"])
        sel = self.run_script(TAKES, "select", self.root, "--take", retake)
        self.assertEqual(sel.returncode, 1)
        self.assertIn("no clips", sel.stderr)



FAKE_GEMINI_CLI = """#!{python}
import json, os, shutil, sys, time
args = sys.argv[1:]
with open(os.environ["FAKE_LOG"], "a") as handle:
    handle.write(json.dumps(args) + "\\n")
if "--dry-run" in args:
    sys.stderr.write("[DRY-RUN] POST /v1beta/interactions")
    sys.exit(0)
failure = os.environ.get("FAKE_FAIL")
if failure == "refuse":
    sys.stderr.write("invalid argument")
    sys.exit(2)
if failure == "crash":
    sys.stderr.write("connection reset")
    sys.exit(1)
out = args[args.index("--out") + 1] if "--out" in args else None
if args[0] == "image":
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "gemini-image-1.png")
    open(path, "wb").write(b"\\x89PNG\\r\\n\\x1a\\nfake")
    print(json.dumps({{"kind": "image", "path": path, "status": "completed", "response_id": "resp-img"}}))
elif "--resume" in args:
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "gemini-video-1.mp4")
    shutil.copy(os.environ["FAKE_VIDEO"], path)
    print(json.dumps({{"kind": "video", "path": path, "status": "completed"}}))
else:
    print(json.dumps({{"id": "int-vid", "status": "in_progress"}}))
"""


class GeminiFixture(CinematicFixture):
    def setUp(self):
        super().setUp()
        import os
        fake = Path(self.temp.name) / "gemini-api"
        fake.write_text(FAKE_GEMINI_CLI.format(python=sys.executable))
        fake.chmod(0o755)
        self.log = Path(self.temp.name) / "gemini.log"
        keys = ("VIDEO_STUDIO_GEMINI_BIN", "FAKE_LOG", "FAKE_FAIL", "FAKE_VIDEO")
        saved = {k: os.environ.get(k) for k in keys}
        os.environ.update({"VIDEO_STUDIO_GEMINI_BIN": str(fake), "FAKE_LOG": str(self.log)})
        os.environ.pop("FAKE_FAIL", None)

        def restore():
            for key, value in saved.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        self.addCleanup(restore)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def fail_with(self, mode):
        import os
        os.environ["FAKE_FAIL"] = mode
        self.addCleanup(os.environ.pop, "FAKE_FAIL", None)

    def ok(self, script, *args):
        result = self.run_script(script, *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)


class GeminiKeyframeTests(GeminiFixture):
    def setUp(self):
        super().setUp()
        bible = self.read("bible")
        bible["references"][0]["higgsfield_element_id"] = "11111111-2222-4333-8444-555555555555"
        bible["references"][0]["images"] = ["bible/images/courier.png"]
        self.put("bible", bible)
        (self.root / "bible/images").mkdir(parents=True, exist_ok=True)
        (self.root / "bible/images/courier.png").write_bytes(b"\x89PNG\r\n\x1a\nref")

    def test_plan_attaches_reference_images_and_preview_stays_offline(self):
        self.ok(KEYFRAMES, "plan", self.root, "--canvas", "16x9", "--provider", "gemini", "--shot", "S01")
        request = json.loads((self.root / "keyframes/requests-16x9.json").read_text())["requests"][0]
        self.assertEqual((request["provider"], request["model"], request["image_size"]), ("gemini", "gemini-nano-banana-2.1", "2K"))
        self.assertEqual(request["inputs"], ["bible/images/courier.png"])
        self.assertNotIn("<<<", request["prompt"])
        preview = self.ok(KEYFRAMES, "preview", self.root, "--canvas", "16x9", "--shot", "S01")
        self.assertEqual((preview["estimate_usd"], preview["problems"], preview["missing_inputs"]), (0.0504, [], []))
        self.assertIn("--dry-run", self.calls()[-1])
        self.assertEqual(ledger.read(self.root)["entries"], [])

    def test_generate_runs_under_the_cap_and_records_failures(self):
        self.ok(KEYFRAMES, "plan", self.root, "--canvas", "16x9", "--provider", "gemini")
        refused = self.run_script(KEYFRAMES, "generate", self.root, "--canvas", "16x9", "--shot", "S01")
        self.assertEqual(refused.returncode, 1)
        self.assertIn("No approved gemini-image cap", refused.stderr)
        self.assertEqual(self.calls(), [])
        ledger.set_cap(self.root, "gemini-image", 1.0, "8 keyframes x $0.0504 plus retries")
        made = self.ok(KEYFRAMES, "generate", self.root, "--canvas", "16x9", "--shot", "S01")
        self.assertEqual(made["keyframe"], "keyframes/16x9/S01-start-v1.png")
        self.assertTrue((self.root / made["keyframe"]).is_file())
        self.assertFalse((self.root / ".gemini-incoming").exists() and any((self.root / ".gemini-incoming").iterdir()))
        args = self.calls()[-1]
        self.assertEqual(args[0], "image")
        self.assertEqual(args[args.index("-i") + 1], str(self.root / "bible/images/courier.png"))
        self.assertEqual(json.loads(args[args.index("--body") + 1])["response_format"]["image_size"], "2K")
        entry = ledger.read(self.root)["entries"][-1]
        self.assertEqual((entry["provider"], entry["status"], entry["job_id"]), ("gemini-image", "succeeded", "resp-img"))
        self.fail_with("refuse")
        self.assertEqual(self.run_script(KEYFRAMES, "generate", self.root, "--canvas", "16x9", "--shot", "S02").returncode, 1)
        self.fail_with("crash")
        crashed = self.run_script(KEYFRAMES, "generate", self.root, "--canvas", "16x9", "--shot", "S03")
        self.assertIn("unknown", crashed.stderr)
        statuses = [e["status"] for e in ledger.read(self.root)["entries"]]
        self.assertEqual(statuses, ["succeeded", "failed", "unknown"])
        self.assertAlmostEqual(ledger.spent(ledger.read(self.root), "gemini-image"), 0.1008)

    def test_bible_sheets_generate_through_gemini(self):
        self.ok(BIBLE, "sheets", self.root, "--provider", "gemini")
        ledger.set_cap(self.root, "gemini-image", 1.0, "basis")
        made = self.ok(BIBLE, "generate", self.root, "--ref", "rooftop")
        self.assertEqual(made["image"], "bible/images/rooftop-v1.png")
        self.assertEqual(self.read("bible")["references"][1]["images"], ["bible/images/rooftop-v1.png"])
        self.assertNotIn("-i", self.calls()[-1])


class GeminiTakeTests(GeminiFixture):
    def setUp(self):
        super().setUp()
        self.assertEqual(self.run_script(SHOTS, "time", self.root).returncode, 0)
        self.assertEqual(self.run_script(BIBLE, "negatives", self.root).returncode, 0)

    def test_plan_checks_native_limits_and_binds_the_first_frame(self):
        project = self.read("project")
        project["formats"].append(dict(project["formats"][0], id="4x5", width=1080, height=1350))
        self.put("project", project)
        refused = self.run_script(TAKES, "plan", self.root, "--canvas", "4x5", "--provider", "gemini")
        self.assertEqual(refused.returncode, 1)
        self.assertIn("16:9 and 9:16 only", refused.stderr)
        shots = self.read("shots")
        shots["shots"][0]["keyframes"] = {"16x9": {"start": "keyframes/16x9/S01-start-v1.png"}}
        self.put("shots", shots)
        self.ok(TAKES, "plan", self.root, "--canvas", "16x9", "--provider", "gemini")
        takes = self.read("takes")["takes"]
        first, second = takes[0], takes[1]
        self.assertEqual((first["provider"], first["estimate_usd"], second["estimate_usd"]), ("gemini", 0.6, 0.7))
        self.assertEqual((first["request"]["task"], first["request"]["inputs"]),
                         ("image_to_video", ["keyframes/16x9/S01-start-v1.png"]))
        self.assertEqual(second["request"]["task"], "text_to_video")
        preview = self.ok(TAKES, "preview", self.root, "--take", "T1-16x9")
        self.assertEqual(preview["missing_inputs"], ["keyframes/16x9/S01-start-v1.png"])
        body = json.loads(preview["command"][preview["command"].index("--body") + 1])
        self.assertEqual(body["response_format"]["duration"], "6s")
        self.assertEqual(body["generation_config"]["video_config"]["task"], "image_to_video")

    def test_submit_needs_approval_records_the_interaction_and_never_resubmits(self):
        self.ok(TAKES, "plan", self.root, "--canvas", "16x9", "--provider", "gemini")
        blocked = self.run_script(TAKES, "submit", self.root, "--take", "T1-16x9")
        self.assertIn("not approved", blocked.stderr)
        self.assertEqual(self.calls(), [])
        self.ok(TAKES, "approve", self.root, "--take", "T1-16x9", "--estimate", 0.6)
        sent = self.ok(TAKES, "submit", self.root, "--take", "T1-16x9")
        self.assertEqual(sent["interaction_id"], "int-vid")
        self.assertIn("--async", self.calls()[-1])
        take = self.read("takes")["takes"][0]
        self.assertEqual((take["status"], take["job_id"]), ("submitted", "int-vid"))
        entry = next(e for e in ledger.read(self.root)["entries"] if e["provider"] == "gemini-video")
        self.assertEqual((entry["status"], entry["job_id"], entry["estimate"]), ("submitted", "int-vid", 0.6))
        self.assertEqual(self.run_script(TAKES, "submit", self.root, "--take", "T1-16x9").returncode, 1)
        self.assertEqual(len(self.calls()), 1)
        self.ok(TAKES, "approve", self.root, "--take", "T2-16x9", "--estimate", 0.7)
        self.fail_with("crash")
        lost = self.run_script(TAKES, "submit", self.root, "--take", "T2-16x9")
        self.assertIn("unknown", lost.stderr)
        self.assertEqual(self.read("takes")["takes"][1]["status"], "unknown")
        self.assertEqual(self.run_script(TAKES, "submit", self.root, "--take", "T2-16x9").returncode, 1)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg needed to split takes")
    def test_fetch_downloads_by_interaction_and_splits(self):
        import os
        os.environ["FAKE_VIDEO"] = str(solid_video(Path(self.temp.name) / "t1.mp4", ["black", "white"], 3))
        self.ok(TAKES, "plan", self.root, "--canvas", "16x9", "--provider", "gemini", "--take", "T1")
        self.ok(TAKES, "approve", self.root, "--take", "T1-16x9", "--estimate", 0.6)
        self.ok(TAKES, "submit", self.root, "--take", "T1-16x9")
        fetched = self.ok(TAKES, "fetch", self.root, "--take", "T1-16x9")
        self.assertEqual((fetched["status"], sorted(fetched["clips"])), ("succeeded", ["S01", "S02"]))
        self.assertEqual(self.calls()[-1][:3], ["video", "--resume", "int-vid"])
        self.assertFalse((self.root / "takes/T1-16x9/incoming").exists())
        entry = next(e for e in ledger.read(self.root)["entries"] if e["provider"] == "gemini-video")
        self.assertEqual(entry["status"], "succeeded")


SOUND = SKILLS / "sound-designer/scripts/sound.py"
FAKE_SOUND_CLI = '''#!{python}
import json, os, subprocess, sys
args = sys.argv[1:]
with open(os.environ["FAKE_LOG"], "a") as handle:
    handle.write(json.dumps(args) + "\\n")
body = json.loads(sys.stdin.read())
if os.environ.get("FAKE_FAIL"):
    sys.stderr.write("insufficient credits")
    sys.exit(1)
out = args[args.index("-o") + 1]
seconds = body.get("duration_seconds") or body.get("music_length_ms", 1000) / 1000
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anoisesrc=d=%.2f:a=0.1" % seconds, out], check=True)
'''


@unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg needed for sound tests")
class SoundDesignerTests(CinematicFixture):
    def setUp(self):
        super().setUp()
        self.assertEqual(self.run_script(SHOTS, "time", self.root).returncode, 0)
        config = json.loads((SKILLS / "sound-designer/assets/sound-config.example.json").read_text())
        (self.root / "sound").mkdir()
        studio.write(self.root, "sound_config", config)
        fake = Path(self.temp.name) / "elevenlabs"
        fake.write_text(FAKE_SOUND_CLI.format(python=sys.executable))
        fake.chmod(0o755)
        self.log = Path(self.temp.name) / "sound.log"
        import os
        saved = {k: os.environ.get(k) for k in ("VIDEO_STUDIO_ELEVENLABS_BIN", "FAKE_LOG", "FAKE_FAIL")}
        os.environ.update({"VIDEO_STUDIO_ELEVENLABS_BIN": str(fake), "FAKE_LOG": str(self.log)})
        os.environ.pop("FAKE_FAIL", None)

        def restore():
            for key, value in saved.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        self.addCleanup(restore)

    def test_plan_follows_shots_and_audio_policy(self):
        result = self.run_script(SOUND, "plan", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertEqual([c["id"] for c in plan["cues"]], ["sfx-S01", "sfx-S02", "sfx-S03", "sfx-S04", "amb-rooftop"])
        self.assertFalse(plan["cap"]["allowed"])
        self.assertFalse(self.log.exists())
        bible = self.read("bible")
        bible["audio_policy"]["music"] = "sparse low synth pulse"
        self.put("bible", bible)
        cues = json.loads(self.run_script(SOUND, "plan", self.root).stdout)["cues"]
        music = next(c for c in cues if c["id"] == "music")
        self.assertEqual(music["duration"], 13.0)

    def test_generate_places_cues_under_the_cap_and_records_failures(self):
        self.run_script(SOUND, "plan", self.root)
        refused = self.run_script(SOUND, "generate", self.root)
        self.assertEqual(refused.returncode, 1)
        self.assertIn("No approved", refused.stderr)
        ledger.set_cap(self.root, "elevenlabs", 500, "sound for 13 s film")
        result = self.run_script(SOUND, "generate", self.root, "--cue", "sfx-S03", "--cue", "amb-rooftop")
        self.assertEqual(result.returncode, 0, result.stderr)
        placed = self.read("sound")["cues"]
        self.assertEqual([(c["id"], c["start"], c["loop"]) for c in placed], [("amb-rooftop", 0.0, True), ("sfx-S03", 6.0, False)])
        self.assertTrue((self.root / placed[1]["file"]).is_file())
        calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual(calls[0][:2], ["text-to-sound-effects", "convert"])
        import os
        os.environ["FAKE_FAIL"] = "1"
        failed = self.run_script(SOUND, "generate", self.root, "--cue", "sfx-S01")
        self.assertEqual(failed.returncode, 1)
        self.assertIn("insufficient credits", failed.stderr)
        self.assertEqual(ledger.read(self.root)["entries"][-1]["status"], "failed")



@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg needed for footage assembly")
class FootageAssemblyTests(CinematicFixture):
    def setUp(self):
        super().setUp()
        for args in (("time",), ):
            self.assertEqual(self.run_script(SHOTS, *args, self.root).returncode, 0)
        self.run_script(BIBLE, "negatives", self.root)
        self.run_script(TAKES, "plan", self.root, "--canvas", "16x9")
        clips = {"T1-16x9": ["0x303030", "white"], "T2-16x9": ["white", "0x303030"]}  # not black: QC flags black frames
        lengths = {"T1-16x9": 3, "T2-16x9": 3.5}
        for take, colors in clips.items():
            self.run_script(TAKES, "approve", self.root, "--take", take, "--estimate", 40)
            self.run_script(TAKES, "submit", self.root, "--take", take)
            raw = solid_video(Path(self.temp.name) / f"{take}.mp4", colors, lengths[take], size="1280x720")
            result = self.run_script(TAKES, "ingest", self.root, "--take", take, "--file", raw)
            self.assertEqual(json.loads(result.stdout)["status"], "succeeded", result.stdout)
            self.run_script(TAKES, "select", self.root, "--take", take, "--skip-dailies", "synthetic fixture")
        bed = self.root / "sound/ambience/amb-rooftop-v1.mp3"
        bed.parent.mkdir(parents=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anoisesrc=d=5:a=0.2", str(bed)], check=True)
        hit = self.root / "sound/sfx/sfx-S03-v1.mp3"
        hit.parent.mkdir(parents=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=f=880:d=0.5", str(hit)], check=True)
        studio.write(self.root, "sound", {"schema": "video-studio/sound@1", "ducking": True, "use_take_audio": False, "cues": [
            {"id": "amb-rooftop", "kind": "ambience", "start": 0.0, "duration": 13.0, "loop": True, "gain_db": -18,
             "file": "sound/ambience/amb-rooftop-v1.mp3"},
            {"id": "sfx-S03", "kind": "sfx", "start": 6.0, "duration": 0.5, "loop": False, "gain_db": -6,
             "file": "sound/sfx/sfx-S03-v1.mp3"}]})

    def test_assemble_finish_and_qc_a_silent_film(self):
        missing = self.run_script(EDIT, "assemble", self.root, "--canvas", "9x16")
        self.assertEqual(missing.returncode, 1)
        self.assertIn("No selected clip for S01 on 9x16", missing.stderr)
        result = self.run_script(EDIT, "assemble", self.root, "--canvas", "16x9")
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads(result.stdout)
        render = self.root / "renders" / f"v{manifest['version']}" / "16x9.mp4"
        info = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height:format=duration",
                               "-of", "json", str(render)], capture_output=True, text=True)
        data = json.loads(info.stdout)
        video = next(s for s in data["streams"] if s["codec_type"] == "video")
        self.assertEqual((video["width"], video["height"]), (1920, 1080))
        self.assertTrue(any(s["codec_type"] == "audio" for s in data["streams"]))
        self.assertAlmostEqual(float(data["format"]["duration"]), 13.0, delta=0.1)
        timeline = json.loads((self.root / "timeline.json").read_text())["canvases"]["16x9"]
        self.assertEqual([e["shot"] for e in timeline], ["S01", "S02", "S03", "S04"])
        self.assertEqual(manifest["renders"][0]["audio"], {"narration": False, "cues": 2, "take_audio": False})
        finished = self.run_script(EDIT, "finish", self.root)
        self.assertEqual(finished.returncode, 0, finished.stderr)
        report = json.loads(self.run_script(QC, "final", self.root).stdout)
        failures = [c for c in report["checks"] if c["status"] == "fail"]
        self.assertEqual(failures, [])
        self.assertTrue((self.root / f"qc/frames/v{manifest['version']}/16x9/S04.png").is_file())


    def test_dialogue_is_mixed_over_ducked_beds(self):
        project = self.read("project")
        project["language"] = "en"
        self.put("project", project)
        studio.write(self.root, "script", {"schema": "video-studio/script@1", "language": "en", "register": "casual",
                                           "lines": [{"id": "L01", "beat": "B2", "speaker": "courier", "text": "Got it.",
                                                      "keywords": ["Got it"]}]})
        voice_file = self.root / "voice/takes/T1/narration.mp3"
        voice_file.parent.mkdir(parents=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=f=220:d=2", str(voice_file)], check=True)
        studio.write(self.root, "words", {"schema": "video-studio/words@1", "audio": "voice/takes/T1/narration.mp3",
                                          "duration": 2.0, "language": "en", "source": "elevenlabs-tts",
                                          "words": [{"text": "Got", "start": 0.2, "end": 0.5, "line": "L01"},
                                                    {"text": "it.", "start": 0.55, "end": 0.9, "line": "L01"}]})
        shots = self.read("shots")
        shots["shots"][2]["lines"] = ["L01"]
        self.put("shots", shots)
        result = self.run_script(EDIT, "assemble", self.root, "--canvas", "16x9")
        self.assertEqual(result.returncode, 0, result.stderr)
        log = next((self.root / "renders").glob("v*/16x9.assemble.log")).read_text()
        self.assertIn("sidechaincompress", log)
        self.assertTrue(json.loads(result.stdout)["renders"][0]["audio"]["narration"])


if __name__ == "__main__":
    unittest.main()
