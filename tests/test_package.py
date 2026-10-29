"""Packaging regressions: allowlist, symlink safety and suite inventory."""
import importlib.util
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("package", ROOT / "scripts/validate_package.py")
PACKAGE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(PACKAGE)


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def test_package_rejects_symlinked_manifest_parent(self):
        copied = Path(self.temp.name) / "video-studio"
        shutil.copytree(ROOT / "plugins/video-studio", copied, ignore=shutil.ignore_patterns("__pycache__"))
        outside = Path(self.temp.name) / "manifest-outside"
        shutil.move(copied / ".codex-plugin", outside)
        (copied / ".codex-plugin").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "escapes|Symlinked"):
            PACKAGE.package_files(copied)

    def test_package_all_skills_without_notices(self):
        files = PACKAGE.validate()
        self.assertEqual(set(PACKAGE.PLUGINS), {"marketing-images", "marketing-performance", "video-studio"})
        self.assertEqual(len([p for p in files if p.name == "SKILL.md"]),
                         sum(len(skills) for skills in PACKAGE.PLUGINS.values()))
        self.assertEqual(PACKAGE.PLUGINS["marketing-images"], {"marketing-image-board", "marketing-image-producer"})
        self.assertFalse(any(p.suffix == ".LICENSE" for p in files))
        self.assertTrue(any(p.name == "voice.py" for p in files))
        self.assertFalse(any("local-docs" in p.parts or "samples" in p.parts for p in files))
        self.assertFalse((ROOT / "plugins/marketing-creative").exists())


if __name__ == "__main__":
    unittest.main()
