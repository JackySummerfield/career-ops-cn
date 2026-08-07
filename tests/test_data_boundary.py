import tempfile
import unittest
from pathlib import Path

from util.data_boundary import (
    CLOUD_MODE,
    LOCAL_MODE,
    ConcurrentWriteError,
    DataBoundaryError,
    CloudDataAdapter,
    LocalDataAdapter,
    RuntimeConfig,
    WriteIntent,
    sha256_text,
    validate_data_path,
)


class DataBoundaryTests(unittest.TestCase):
    CURRENT_REPOSITORY = "example-org/private-career-data"
    ALLOWED_REPOSITORY = "example-org/private-career-data"
    OTHER_REPOSITORY = "example-org/other-private-data"

    def test_only_migrated_text_paths_are_writable(self):
        self.assertEqual(validate_data_path("jobs/001_acme/eval.md"), "jobs/001_acme/eval.md")
        self.assertEqual(validate_data_path("tracker/tracker.csv"), "tracker/tracker.csv")

        for path in ("../secret.md", "/tmp/secret.md", "tracker/notes.md", "jobs/raw.pdf"):
            with self.assertRaises(DataBoundaryError):
                validate_data_path(path)
        with self.assertRaises(DataBoundaryError):
            validate_data_path("jobs/raw.pdf", writable=False)

    def test_cloud_scope_is_configured_only(self):
        intent = WriteIntent(
            self.CURRENT_REPOSITORY,
            "jobs/001_acme/eval.md",
            "# Synthetic evaluation\n",
            None,
            self.ALLOWED_REPOSITORY,
        ).validated()
        self.assertEqual(intent.path, "jobs/001_acme/eval.md")

        for repository in (self.OTHER_REPOSITORY, "example-org/career-ops-cn"):
            with self.assertRaises(DataBoundaryError):
                WriteIntent(
                    repository,
                    "jobs/001_acme/eval.md",
                    "text",
                    None,
                    self.ALLOWED_REPOSITORY,
                ).validated()

        adapter = CloudDataAdapter(self.CURRENT_REPOSITORY, self.ALLOWED_REPOSITORY)
        intent = adapter.prepare_write(
            "tracker/tracker.csv", "id,company,role\n", expected_sha=None
        )
        self.assertEqual(intent.repository, self.ALLOWED_REPOSITORY)
        with self.assertRaises(ConcurrentWriteError):
            adapter.verify_revision("old", "new")

    def test_runtime_config_requires_explicit_boundary(self):
        with self.assertRaises(DataBoundaryError):
            RuntimeConfig.from_env({"CAREER_OPS_MODE": LOCAL_MODE})

        with tempfile.TemporaryDirectory() as directory:
            config = RuntimeConfig.from_env(
                {"CAREER_OPS_MODE": LOCAL_MODE, "CAREER_OPS_DATA_ROOT": directory}
            )
            self.assertEqual(config.data_root, Path(directory).resolve())

        cloud = RuntimeConfig.from_env(
            {
                "CAREER_OPS_MODE": CLOUD_MODE,
                "CAREER_OPS_GITHUB_REPO": self.CURRENT_REPOSITORY,
                "CAREER_OPS_ALLOWED_DATA_REPOSITORY": self.ALLOWED_REPOSITORY,
            }
        )
        self.assertEqual(cloud.repository, self.ALLOWED_REPOSITORY)

        with self.assertRaises(DataBoundaryError):
            RuntimeConfig.from_env(
                {
                    "CAREER_OPS_MODE": CLOUD_MODE,
                    "CAREER_OPS_GITHUB_REPO": self.OTHER_REPOSITORY,
                    "CAREER_OPS_ALLOWED_DATA_REPOSITORY": self.ALLOWED_REPOSITORY,
                }
            )

    def test_local_adapter_uses_sha_and_atomic_text_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = LocalDataAdapter(Path(directory))
            path = "tracker/tracker.csv"
            initial = "id,company,role\n"
            first_sha = adapter.write(path, initial, expected_sha=None)
            self.assertEqual(first_sha, sha256_text(initial))
            content, read_sha = adapter.read(path)
            self.assertEqual((content, read_sha), (initial, first_sha))

            with self.assertRaises(ConcurrentWriteError):
                adapter.write(path, "changed\n", expected_sha="stale")

            final = "changed\n"
            final_sha = adapter.write(path, final, expected_sha=first_sha)
            self.assertEqual(final_sha, sha256_text(final))

    def test_credentials_are_rejected(self):
        with self.assertRaises(DataBoundaryError):
            synthetic_token = "ghp_" + "12345678901234567890"
            WriteIntent(
                self.CURRENT_REPOSITORY,
                "profile/notes.md",
                f"token={synthetic_token}\n",
                None,
                self.ALLOWED_REPOSITORY,
            ).validated()


if __name__ == "__main__":
    unittest.main()
