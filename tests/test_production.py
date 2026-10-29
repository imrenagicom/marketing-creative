"""Behavioral regressions for timing, safe revisions, composition and packaging."""
import array
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "plugins/marketing-creative/skills"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


P = module("project", SKILLS / "motion-video-producer/scripts/project.py")
V = module("voice", SKILLS / "motion-voice/scripts/voice.py")
Q = module("qa", SKILLS / "motion-video-qa/scripts/check.py")
PACKAGE = module("package", ROOT / "scripts/validate_package.py")


class ProductionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        P.init(self.root, "example", list(P.PRESETS), 8)

    def compose(self):
        return subprocess.run(["node", str(SKILLS / "motion-composer/scripts/compose.mjs"), str(self.root)], capture_output=True, text=True)

    def aligned(self, text="One two three", tokens=None):
        words = tokens or ["One", "two", "three"]
        P.write(self.root / "script.json", {"schemaVersion": 1, "segments": [{"id": "line", "text": text}]})
        rate = 44100
        data = array.array("h", [0]) * (rate * 3)
        aligned = []
        for i, token in enumerate(words):
            start, end = .2 + .8 * i, .5 + .8 * i
            for frame in range(round(start * rate), round(end * rate)):
                data[frame] = 1000 if frame % 2 else -1000
            aligned.append({"id": f"w{i}", "segment": "line", "text": token, "start": start, "end": end})
        project = P.read(self.root / "project.json")
        V.commit(self.root, data, rate, {"words": aligned}, P.read(self.root / "script.json"), project)
        return data, rate

    def voice(self, *args):
        return subprocess.run([sys.executable, str(SKILLS / "motion-voice/scripts/voice.py"), *args], capture_output=True, text=True)

    def test_all_ratios_build_and_check(self):
        self.assertEqual(self.compose().returncode, 0)
        report = Q.check(self.root)
        self.assertEqual(len(report["variants"]), 4)
        for variant in P.read(self.root / "project.json")["variants"]:
            page = Q.Page()
            page.feed((self.root / "variants" / variant["id"] / "index.html").read_text())
            self.assertEqual(int(page.roots[0]["data-width"]), variant["width"])
            self.assertEqual(int(page.roots[0]["data-height"]), variant["height"])

    def test_variant_recomposition_and_overrides(self):
        board = P.read(self.root / "storyboard.json")
        board["variants"] = {"ratio-1x1": [{"id": "square", "start": {"seconds": 0}, "end": {"seconds": 8},
                                                    "visual": {"mode": "type", "text": "Square copy"}}]}
        P.write(self.root / "storyboard.json", board)
        resolved = P.resolve(self.root)
        self.assertEqual(resolved["variants"][-1]["beats"][0]["visual"]["text"], "Square copy")
        self.assertEqual(self.compose().returncode, 0)
        landscape = (self.root / "variants/ratio-16x9/index.html").read_text()
        portrait = (self.root / "variants/ratio-9x16/index.html").read_text()
        self.assertIn("grid-template-columns", landscape)
        self.assertIn("grid-template-rows", portrait)

    def test_cues_unicode_and_ambiguity(self):
        words = [{"segment": "a", "text": t, "start": i, "end": i+.5} for i, t in enumerate(["你好", "世界", "你好"])]
        self.assertEqual(P.phrase_span(words, "a", "你好世界"), (0, 1))
        with self.assertRaisesRegex(ValueError, "Ambiguous"):
            P.phrase_span(words, "a", "你好")
        self.assertEqual(P.phrase_span(words, "a", "你好", 2), (2, 2))
        with self.assertRaisesRegex(ValueError, "not found"):
            P.phrase_span([{"segment": "a", "text": "someone"}], "a", "one")

    def test_audio_word_cues_retime(self):
        self.aligned()
        board = {"schemaVersion": 1, "beats": [
            {"id": "first", "start": {"seconds": 0}, "end": {"segment": "line", "quote": "two"}, "visual": {"mode": "type", "text": "First"}},
            {"id": "next", "start": {"segment": "line", "quote": "two"}, "end": {"seconds": 8}, "visual": {"mode": "type", "text": "Next"}}]}
        P.write(self.root / "storyboard.json", board)
        old = P.resolve(self.root)["variants"][0]["beats"][1]["start"]
        result = self.voice("trim", str(self.root), "--cap", ".24")
        self.assertEqual(result.returncode, 0, result.stderr)
        new = P.resolve(self.root)["variants"][0]["beats"][1]["start"]
        self.assertLess(new, old)

    def test_audio_hash_and_script_changes_rejected(self):
        self.aligned()
        file = self.root / "audio/vo.wav"
        file.write_bytes(file.read_bytes() + b"change")
        with self.assertRaisesRegex(ValueError, "Audio changed"):
            P.resolve(self.root)

    def test_script_alignment_drift_rejected(self):
        self.aligned()
        script = P.read(self.root / "script.json")
        script["segments"][0]["text"] = "Different words"
        P.write(self.root / "script.json", script)
        with self.assertRaisesRegex(ValueError, "Script/alignment"):
            P.resolve(self.root)

    def test_stale_build_and_manual_edit_preserved(self):
        self.assertEqual(self.compose().returncode, 0)
        html = self.root / "variants/ratio-16x9/index.html"
        html.write_text(html.read_text().replace("One useful idea", "Manual change"))
        with self.assertRaisesRegex(ValueError, "Edited/missing"):
            Q.check(self.root)
        result = self.compose()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Manual change", html.read_text())

    def test_changed_storyboard_requires_resolution(self):
        self.assertEqual(self.compose().returncode, 0)
        board = P.read(self.root / "storyboard.json")
        board["beats"][0]["visual"]["text"] = "New source"
        P.write(self.root / "storyboard.json", board)
        with self.assertRaisesRegex(ValueError, "Stale"):
            Q.check(self.root)
        self.assertNotEqual(self.compose().returncode, 0)
        P.resolve(self.root)
        self.assertEqual(self.compose().returncode, 0)

    def test_gaps_and_intentional_blank(self):
        board = P.read(self.root / "storyboard.json")
        board["beats"][0]["end"]["seconds"] = 1
        P.write(self.root / "storyboard.json", board)
        with self.assertRaisesRegex(ValueError, "Gap/overlap"):
            P.resolve(self.root)
        board["beats"].insert(1, {"id": "blank", "start": {"seconds": 1}, "end": {"seconds": 1.6}, "intentionalBlank": True})
        P.write(self.root / "storyboard.json", board)
        P.resolve(self.root)
        self.assertEqual(self.compose().returncode, 0)

    def test_ratio_dimensions_and_safe_area(self):
        project = P.read(self.root / "project.json")
        project["variants"][0]["width"] = 1080
        P.write(self.root / "project.json", project)
        with self.assertRaisesRegex(ValueError, "Canvas does not match"):
            P.resolve(self.root)

    def test_changed_asset_and_path_escape(self):
        asset = self.root / "assets/item.svg"
        asset.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
        P.write(self.root / "assets/manifest.json", {"schemaVersion": 1, "assets": [{"id": "item", "path": "assets/item.svg", "source": "original", "sha256": P.digest(asset)}]})
        P.resolve(self.root)
        asset.write_text("changed")
        with self.assertRaisesRegex(ValueError, "Changed asset"):
            P.resolve(self.root)
        with self.assertRaisesRegex(ValueError, "escapes"):
            P.local(self.root, "../outside")

    def test_custom_visual_and_text_free_capture(self):
        asset = self.root / "assets/item.svg"
        asset.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400"/>')
        P.write(self.root / "assets/manifest.json", {"schemaVersion": 1, "assets": [{"id": "capture", "path": "assets/item.svg", "kind": "image", "source": "original test", "sha256": P.digest(asset)}]})
        P.write(self.root / "storyboard.json", {"schemaVersion": 1, "beats": [{"id": "proof", "start": {"seconds": 0}, "end": {"seconds": 8}, "visual": {"mode": "image", "asset": "capture"}}]})
        P.resolve(self.root)
        composed = self.compose()
        self.assertEqual(composed.returncode, 0, composed.stderr)
        Q.check(self.root)
        board = P.read(self.root / "storyboard.json")
        board["beats"][0]["visual"] = {"mode": "custom:real-demo", "asset": "capture"}
        P.write(self.root / "storyboard.json", board)
        with self.assertRaisesRegex(ValueError, "requires project.generator"):
            P.resolve(self.root)
        (self.root / "build.mjs").write_text("// Project-owned custom generator\n")
        project = P.read(self.root / "project.json")
        project["generator"] = "build.mjs"
        P.write(self.root / "project.json", project)
        P.resolve(self.root)
        self.assertIn("build.mjs", P.input_hashes(self.root))
        self.assertNotEqual(self.compose().returncode, 0)

    def test_footage_cannot_run_out_mid_beat(self):
        asset = self.root / "assets/clip.mp4"
        asset.write_bytes(b"test fixture")
        P.write(self.root / "assets/manifest.json", {"schemaVersion": 1, "assets": [{"id": "capture", "path": "assets/clip.mp4", "kind": "video", "duration": 7, "source": "original test", "sha256": P.digest(asset)}]})
        P.write(self.root / "storyboard.json", {"schemaVersion": 1, "beats": [{"id": "proof", "start": {"seconds": 0}, "end": {"seconds": 8}, "visual": {"mode": "footage", "asset": "capture"}}]})
        with self.assertRaisesRegex(ValueError, "runs out"):
            P.resolve(self.root)

    def test_trim_is_sample_exact_and_backed_up(self):
        original, rate = self.aligned()
        before = P.read(self.root / "audio/alignment.json")
        dry = self.voice("trim", str(self.root), "--cap", ".24", "--dry-run")
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertEqual(P.read(self.root / "audio/alignment.json"), before)
        result = self.voice("trim", str(self.root), "--cap", ".24")
        self.assertEqual(result.returncode, 0, result.stderr)
        actual, _ = V.pcm_read(self.root / "audio/vo.wav")
        self.assertEqual(len(original)-len(actual), round(.52*rate))
        after = P.read(self.root / "audio/alignment.json")
        self.assertAlmostEqual(after["words"][-1]["end"], before["words"][-1]["end"]-.52)
        self.assertTrue(any((self.root / "audio/backups").glob("take-*/vo.wav")))

    def test_trim_refuses_speech_at_boundary(self):
        self.aligned()
        data, rate = V.pcm_read(self.root / "audio/vo.wav")
        for i in range(round(.6*rate), round(.75*rate)):
            data[i] = 3000
        V.pcm_write(self.root / "audio/vo.wav", data, rate)
        alignment = P.read(self.root / "audio/alignment.json")
        alignment["audioSha256"] = P.digest(self.root / "audio/vo.wav")
        P.write(self.root / "audio/alignment.json", alignment)
        result = self.voice("trim", str(self.root), "--cap", ".24")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("contains signal", result.stderr)

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required for supplied replacement conversion")
    def test_replace_first_last_and_whole_take(self):
        for phrase in ("One", "three", "One two three"):
            with self.subTest(phrase=phrase):
                self.aligned()
                replacement = Path(self.temp.name) / "replacement.wav"
                V.pcm_write(replacement, array.array("h", [1000, -1000]) * 11025, 44100)
                meta = Path(self.temp.name) / "replacement.json"
                P.write(meta, {"words": [{"segment": "line", "text": "New", "start": .04, "end": .45}]})
                result = self.voice("replace", str(self.root), "--segment", "line", "--find", phrase,
                                    "--replacement", str(replacement), "--replacement-alignment", str(meta))
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                P.validate_alignment(self.root, P.read(self.root / "project.json"), P.read(self.root / "script.json"))
                self.assertIn("New", P.read(self.root / "script.json")["segments"][0]["text"])

    def test_tts_dry_run_never_requires_credentials(self):
        P.write(self.root / "script.json", {"schemaVersion": 1, "segments": [{"id": "cta", "text": "Try one task"}]})
        config = Path(self.temp.name) / "voice.json"
        P.write(config, {"voiceId": "selected", "modelId": "selected", "language": "en", "voiceSettings": {}})
        result = self.voice("generate", str(self.root), "--config", str(config), "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.root / "audio/vo.wav").exists())

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg/FFprobe required")
    def test_encoded_export_dimensions_duration_and_audio(self):
        project = P.read(self.root / "project.json")
        variant = project["variants"][0]
        variant.update({"width": 320, "height": 180})
        project["variants"] = [variant]
        P.write(self.root / "project.json", project)
        P.resolve(self.root)
        self.assertEqual(self.compose().returncode, 0)
        renders = self.root / "renders"
        renders.mkdir()
        export = renders / f"{variant['id']}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=320x180:r=30:d=8",
                        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(export)], check=True)
        result = Q.verify_export(self.root, variant, project)
        self.assertEqual((result["width"], result["height"]), (320, 180))
        wrong = {**variant, "width": 1920, "height": 1080}
        with self.assertRaisesRegex(ValueError, "Wrong export dimensions"):
            Q.verify_export(self.root, wrong, project)
        with self.assertRaisesRegex(ValueError, "no audio stream"):
            Q.verify_export(self.root, variant, {**project, "voice": {"audio": "required"}})
        with self.assertRaisesRegex(ValueError, "no audio stream"):
            Q.verify_export(self.root, {**variant, "audioRequired": True}, project)
        with self.assertRaisesRegex(ValueError, "duration differs"):
            Q.verify_export(self.root, {**variant, "duration": 7}, project)
        limited = {**variant, "placement": {**variant["placement"], "maxFileBytes": 1}}
        with self.assertRaisesRegex(ValueError, "file-size"):
            Q.verify_export(self.root, limited, project)

    def test_declared_missing_animation_target(self):
        self.assertEqual(self.compose().returncode, 0)
        dest = self.root / "variants/ratio-16x9"
        html = (dest / "index.html").read_text().replace('id="b0-art"', 'id="removed-art"')
        (dest / "index.html").write_text(html)
        build = P.read(dest / "build.json")
        build["generatedHashes"]["index.html"] = P.digest(dest / "index.html")
        P.write(dest / "build.json", build)
        with self.assertRaisesRegex(ValueError, "Missing declared animation target"):
            Q.check(self.root)

    def test_composer_rejects_symlink_outputs_even_when_forced(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (outside / "index.html").write_text("preserve this external file")
        (self.root / "variants").mkdir()
        (self.root / "variants/ratio-16x9").symlink_to(outside, target_is_directory=True)
        result = subprocess.run(["node", str(SKILLS / "motion-composer/scripts/compose.mjs"), str(self.root), "--force"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Symlink", result.stderr)
        self.assertEqual((outside / "index.html").read_text(), "preserve this external file")

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required")
    def test_accented_original_replacement_preserves_word_spaces(self):
        self.aligned("Café sekarang", ["Café", "sekarang"])
        replacement = Path(self.temp.name) / "replacement.wav"
        V.pcm_write(replacement, array.array("h", [1000, -1000]) * 22050, 44100)
        meta = Path(self.temp.name) / "replacement.json"
        P.write(meta, {"words": [{"segment": "line", "text": "Mulai", "start": .04, "end": .4},
                                {"segment": "line", "text": "tugas", "start": .5, "end": .9}]})
        result = self.voice("replace", str(self.root), "--segment", "line", "--find", "Café sekarang",
                            "--replacement", str(replacement), "--replacement-alignment", str(meta))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(P.read(self.root / "script.json")["segments"][0]["text"], "Mulai tugas")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
    def test_footage_audio_is_required_in_encoded_export(self):
        variant = {**P.read(self.root / "project.json")["variants"][0], "width": 320, "height": 180,
                   "beats": [{"visual": {"mode": "footage", "hasAudio": True}}]}
        renders = self.root / "renders"
        renders.mkdir()
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=320x180:r=30:d=8",
                        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(renders / f"{variant['id']}.mp4")], check=True)
        with self.assertRaisesRegex(ValueError, "no audio stream"):
            Q.verify_export(self.root, variant, P.read(self.root / "project.json"))

    def test_package_rejects_symlinked_manifest_parent(self):
        copied = Path(self.temp.name) / "plugin-copy"
        shutil.copytree(PACKAGE.PLUGIN, copied, ignore=shutil.ignore_patterns("__pycache__"))
        outside = Path(self.temp.name) / "manifest-outside"
        shutil.move(copied / ".codex-plugin", outside)
        (copied / ".codex-plugin").symlink_to(outside, target_is_directory=True)
        original = PACKAGE.PLUGIN
        try:
            PACKAGE.PLUGIN = copied
            with self.assertRaisesRegex(ValueError, "escapes|Symlinked"):
                PACKAGE.package_files()
        finally:
            PACKAGE.PLUGIN = original

    def test_package_all_skills_and_notices(self):
        files = PACKAGE.validate()
        self.assertEqual(len([p for p in files if p.name == "SKILL.md"]),
                         sum(len(skills) for skills in PACKAGE.PLUGINS.values()))
        self.assertEqual(len(PACKAGE.PLUGINS["marketing-creative"]) + len(PACKAGE.PLUGINS["marketing-performance"]), 15)
        self.assertEqual(PACKAGE.PLUGINS["marketing-images"], {"marketing-image-board", "marketing-image-producer"})
        self.assertEqual(len([p for p in files if p.suffix == ".LICENSE"]), 2)
        self.assertTrue(any(p.name == "voice.py" for p in files))
        self.assertFalse(any("local-docs" in p.parts or "samples" in p.parts for p in files))


if __name__ == "__main__":
    unittest.main()
