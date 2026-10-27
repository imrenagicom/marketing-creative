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


if __name__ == "__main__":
    unittest.main()
