import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prepare_release import VERSION_FILES, update_versions


class ReleaseTests(unittest.TestCase):
    def test_versions_and_archive_match_without_changing_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            for name in ("scripts", "plugins", ".agents", ".claude-plugin"):
                shutil.copytree(ROOT / name, root / name,
                                ignore=shutil.ignore_patterns("__pycache__"))
            for name in ("package.json", "package-lock.json"):
                shutil.copy2(ROOT / name, root / name)
            original_lock = json.loads((root / "package-lock.json").read_text())
            archive = Path(directory) / "release.zip"
            subprocess.run([sys.executable, str(root / "scripts/prepare_release.py"),
                            "0.2.3", "--output", str(archive)], check=True,
                           capture_output=True, text=True)
            for name in VERSION_FILES:
                self.assertEqual(json.loads((root / name).read_text())["version"], "0.2.3")
            lock = json.loads((root / "package-lock.json").read_text())
            self.assertEqual(lock["packages"][""]["version"], "0.2.3")
            self.assertEqual({k: v for k, v in lock["packages"].items() if k},
                             {k: v for k, v in original_lock["packages"].items() if k})
            with zipfile.ZipFile(archive) as package:
                for manifest in ("plugin.json", ".codex-plugin/plugin.json", ".claude-plugin/plugin.json"):
                    parsed = json.loads(package.read(manifest))
                    self.assertEqual(parsed["version"], "0.2.3")
                    self.assertEqual(parsed["name"], "marketing-creative")
                self.assertIn("skills/creative-ideation/SKILL.md", package.namelist())
                for resource in ("SKILL.md", "agents/openai.yaml"):
                    self.assertIn(f"skills/marketing-video/{resource}", package.namelist())
                self.assertIn("skills/motion-storyboard/references/beat-planning.md", package.namelist())
                self.assertIn("skills/motion-voice/references/loudness-and-pauses.md", package.namelist())
                self.assertNotIn("skills/marketing-brief/SKILL.md", package.namelist())
                self.assertNotIn("skills/marketing-copywriter/SKILL.md", package.namelist())
                self.assertNotIn("skills/google-analytics-analyst/SKILL.md", package.namelist())
                self.assertFalse(any("node_modules" in name for name in package.namelist()))

            with zipfile.ZipFile(Path(directory) / "marketing-performance-plugin.zip") as package:
                self.assertIn("skills/marketing-brief/SKILL.md", package.namelist())
                self.assertIn("skills/campaign-manager/scripts/build_utm.py", package.namelist())
                self.assertIn("skills/campaign-manager/references/meta-ads.md", package.namelist())
                self.assertIn("skills/campaign-manager/references/social-media.md", package.namelist())
                self.assertIn("skills/campaign-manager/references/reporting.md", package.namelist())
                for resource in (
                    "SKILL.md",
                    "agents/openai.yaml",
                    "scripts/ga4_report.py",
                    "references/setup-and-auth.md",
                    "references/metrics-and-dimensions.md",
                    "references/diagnostic-playbook.md",
                ):
                    self.assertIn(f"skills/google-analytics-analyst/{resource}", package.namelist())
                for resource in ("SKILL.md", "agents/openai.yaml", "references/channel-copy.md",
                                 "references/voice-and-style.md"):
                    self.assertIn(f"skills/marketing-copywriter/{resource}", package.namelist())
                self.assertNotIn("skills/creative-ideation/SKILL.md", package.namelist())
                self.assertNotIn("skills/marketing-video/SKILL.md", package.namelist())
                for manifest in ("plugin.json", ".codex-plugin/plugin.json", ".claude-plugin/plugin.json"):
                    parsed = json.loads(package.read(manifest))
                    self.assertEqual(parsed["version"], "0.2.3")
                    self.assertEqual(parsed["name"], "marketing-performance")

            with zipfile.ZipFile(Path(directory) / "video-studio-plugin.zip") as package:
                names = package.namelist()
                for resource in ("SKILL.md", "agents/openai.yaml", "scripts/studio.py", "scripts/ledger.py",
                                 "references/project-contract.md", "assets/example-project/project.json"):
                    self.assertIn(f"skills/studio-producer/{resource}", names)
                for skill in ("director", "scriptwriter", "voice-director", "shot-designer", "motion-designer",
                              "editor", "qc-reviewer", "reference-analyst", "continuity-bible", "keyframe-generator",
                              "ai-video-generator", "sound-designer"):
                    self.assertIn(f"skills/{skill}/SKILL.md", names)
                self.assertIn("skills/motion-designer/scripts/compose.mjs", names)
                self.assertIn("skills/voice-director/assets/voice-config.example.json", names)
                self.assertIn("skills/ai-video-generator/scripts/takes.py", names)
                self.assertIn("skills/studio-producer/assets/example-cinematic/bible/bible.json", names)
                self.assertNotIn("skills/marketing-video/SKILL.md", names)
                self.assertNotIn("skills/marketing-brief/SKILL.md", names)
                for manifest in ("plugin.json", ".codex-plugin/plugin.json", ".claude-plugin/plugin.json"):
                    parsed = json.loads(package.read(manifest))
                    self.assertEqual(parsed["version"], "0.2.3")
                    self.assertEqual(parsed["name"], "video-studio")

    def test_invalid_version_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            for version in ("v0.1.0", "01.2.3", "1.2.3-beta.1", "1.2.3; touch bad"):
                with self.subTest(version=version), self.assertRaises(ValueError):
                    update_versions(Path(directory), version)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_missing_metadata_does_not_partially_update(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "package.json"
            package.write_text('{"version":"0.1.0"}')
            before = package.read_bytes()
            with self.assertRaises(FileNotFoundError):
                update_versions(root, "0.2.0")
            self.assertEqual(package.read_bytes(), before)
