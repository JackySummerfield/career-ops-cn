import os
import tempfile
import unittest
import zipfile
from pathlib import Path

from util.build_public_bundle import (
    PUBLIC_DIRECTORIES,
    PUBLIC_FILES,
    BundleError,
    build_bundle,
    collect_public_files,
)


class PublicBundleTests(unittest.TestCase):
    def test_allowlist_excludes_migration_and_user_data(self):
        source_root = Path(__file__).resolve().parents[1]
        files = {path.relative_to(source_root).as_posix() for path in collect_public_files(source_root)}

        self.assertNotIn("MIGRATION_PLAN.md", files)
        self.assertFalse(any(path.startswith("users/") for path in files))
        self.assertIn("util/data_boundary.py", files)

    def test_bundle_contains_only_allowlisted_files(self):
        source_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "career-ops-cn.zip"
            count, digest = build_bundle(source_root, output)
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()

            self.assertEqual(count, len(names))
            self.assertEqual(len(digest), 64)
            self.assertNotIn("MIGRATION_PLAN.md", names)
            self.assertFalse(any(name.startswith("users/") for name in names))
            self.assertIn("agents/github-data-connector.md", names)

    def test_bundle_rejects_symlinks(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are not supported on this platform")

        with tempfile.TemporaryDirectory() as directory:
            source_root = Path(directory)
            for filename in PUBLIC_FILES:
                path = source_root / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("synthetic\n", encoding="utf-8")
            for directory_name in PUBLIC_DIRECTORIES:
                (source_root / directory_name).mkdir(parents=True, exist_ok=True)

            outside = source_root.parent / "outside-public-bundle.txt"
            outside.write_text("must not be bundled\n", encoding="utf-8")
            try:
                (source_root / "util" / "external.txt").symlink_to(outside)
                with self.assertRaises(BundleError):
                    collect_public_files(source_root)
            finally:
                outside.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
