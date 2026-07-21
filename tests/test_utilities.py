import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from util import gen_dashboard, render_markdown


class UtilityTests(unittest.TestCase):
    def create_user(self, root: Path) -> Path:
        user_dir = root / "demo_user"
        jobs_dir = user_dir / "jobs"
        resume_dir = user_dir / "resume"
        jobs_dir.mkdir(parents=True)
        resume_dir.mkdir()
        (resume_dir / "cv_master.md").write_text("# Master Resume\n", encoding="utf-8")

        job_dir = jobs_dir / "001_acme_ai"
        job_dir.mkdir()
        (job_dir / "eval.md").write_text("# Evaluation\n", encoding="utf-8")

        (user_dir / "tracker.csv").write_text(
            "id,company,role,url,score,status,last_updated,notes\n"
            "1,Acme,AI Product Manager,https://example.com/1,4.5,evaluating,2026-07-21,Top\n",
            encoding="utf-8",
        )
        return user_dir

    def test_dashboard_uses_portable_relative_links(self):
        with tempfile.TemporaryDirectory() as directory:
            user_dir = self.create_user(Path(directory))

            dashboard = gen_dashboard.generate_dashboard_markdown(user_dir)

            self.assertIn("# Career Dashboard", dashboard)
            self.assertIn("[eval.md](jobs/001_acme_ai/eval.md)", dashboard)
            self.assertIn("[tracker.csv](tracker.csv)", dashboard)
            self.assertNotIn("file:///", dashboard)

    def test_missing_tracker_is_actionable(self):
        with tempfile.TemporaryDirectory() as directory:
            user_dir = Path(directory) / "demo_user"
            user_dir.mkdir()

            with self.assertRaises(gen_dashboard.DashboardError) as context:
                gen_dashboard.dashboard_rows(user_dir)

            self.assertIn("tracker.csv", str(context.exception))

    def test_markdown_renderer_produces_standalone_html(self):
        rendered = render_markdown.render_markdown_to_html(
            "# Interview Prep\n\n- **Strength**: clear\n\n[JD](jobs/001_acme_ai/eval.md)\n"
        )

        self.assertIn("<!DOCTYPE html>", rendered)
        self.assertIn("<strong>Strength</strong>", rendered)
        self.assertIn('href="jobs/001_acme_ai/eval.md"', rendered)


if __name__ == "__main__":
    unittest.main()
