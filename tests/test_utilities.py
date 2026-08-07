import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from util import gen_dashboard, render_markdown


class UtilityTests(unittest.TestCase):
    def create_user(self, root: Path) -> Path:
        user_dir = root / "demo_user"
        jobs_dir = user_dir / "jobs"
        tracker_dir = user_dir / "tracker"
        resume_dir = user_dir / "resumes"
        jobs_dir.mkdir(parents=True)
        tracker_dir.mkdir()
        resume_dir.mkdir()
        (resume_dir / "cv_master.md").write_text("# Master Resume\n", encoding="utf-8")

        job_dir = jobs_dir / "001_acme_ai"
        job_dir.mkdir()
        (job_dir / "eval.md").write_text("# Evaluation\n", encoding="utf-8")

        (tracker_dir / "tracker.csv").write_text(
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
            self.assertIn("[tracker.csv](tracker/tracker.csv)", dashboard)
            self.assertNotIn("file:///", dashboard)

    def test_missing_tracker_is_actionable(self):
        with tempfile.TemporaryDirectory() as directory:
            user_dir = Path(directory) / "demo_user"
            user_dir.mkdir()

            with self.assertRaises(gen_dashboard.DashboardError) as context:
                gen_dashboard.dashboard_rows(user_dir)

            self.assertIn("tracker.csv", str(context.exception))

    def test_closed_status_is_in_history(self):
        with tempfile.TemporaryDirectory() as directory:
            user_dir = self.create_user(Path(directory))
            tracker_path = user_dir / "tracker" / "tracker.csv"
            tracker_path.write_text(
                "id,company,role,url,score,status,last_updated,notes\n"
                "1,Acme,AI Product Manager,https://example.com/1,4.5,closed,2026-07-21,Job closed\n",
                encoding="utf-8",
            )

            active, offers, history = gen_dashboard.dashboard_rows(user_dir)

            self.assertEqual(active, [])
            self.assertEqual(offers, [])
            self.assertEqual([row["status"] for row in history], ["closed"])

    def test_offer_status_is_separate_from_history(self):
        with tempfile.TemporaryDirectory() as directory:
            user_dir = self.create_user(Path(directory))
            tracker_path = user_dir / "tracker" / "tracker.csv"
            tracker_path.write_text(
                "id,company,role,url,score,status,last_updated,notes\n"
                "1,Acme,AI Product Manager,https://example.com/1,4.5,offer,2026-07-21,Offer received\n"
                "2,Closed Co,AI Engineer,https://example.com/2,4.0,closed,2026-07-20,Job closed\n",
                encoding="utf-8",
            )

            active, offers, history = gen_dashboard.dashboard_rows(user_dir)

            self.assertEqual(active, [])
            self.assertEqual([row["status"] for row in offers], ["offer"])
            self.assertEqual([row["status"] for row in history], ["closed"])

    def test_offers_are_rendered_before_active_applications(self):
        with tempfile.TemporaryDirectory() as directory:
            user_dir = self.create_user(Path(directory))
            tracker_path = user_dir / "tracker" / "tracker.csv"
            tracker_path.write_text(
                "id,company,role,url,score,status,last_updated,notes\n"
                "1,Acme,AI Product Manager,https://example.com/1,4.5,offer,2026-07-21,Offer received\n"
                "2,Active Co,AI Engineer,https://example.com/2,4.0,applied,2026-07-20,Application sent\n"
                "3,Closed Co,Data Analyst,https://example.com/3,3.5,closed,2026-07-19,Job closed\n",
                encoding="utf-8",
            )

            markdown = gen_dashboard.generate_dashboard_markdown(user_dir)
            html = gen_dashboard.generate_dashboard(user_dir, use_vscode=False)

            self.assertLess(markdown.index("## Offers"), markdown.index("## Active Applications"))
            self.assertLess(markdown.index("## Active Applications"), markdown.index("## History"))
            self.assertLess(
                html.index('<h2 class="section-title">Offers</h2>'),
                html.index('<h2 class="section-title">Active Applications</h2>'),
            )
            self.assertLess(
                html.index('<h2 class="section-title">Active Applications</h2>'),
                html.index('<h2 class="section-title">History</h2>'),
            )

    def test_markdown_renderer_produces_standalone_html(self):
        rendered = render_markdown.render_markdown_to_html(
            "# Interview Prep\n\n- **Strength**: clear\n\n[JD](jobs/001_acme_ai/eval.md)\n"
        )

        self.assertIn("<!DOCTYPE html>", rendered)
        self.assertIn("<strong>Strength</strong>", rendered)
        self.assertIn('href="jobs/001_acme_ai/eval.md"', rendered)


if __name__ == "__main__":
    unittest.main()
