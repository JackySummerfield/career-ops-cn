"""
gen_dashboard.py — Generate a Markdown or HTML dashboard from tracker.csv + job directories.

Usage:
    python util/gen_dashboard.py --user <username>
    python util/gen_dashboard.py --user <username> --format html
    python util/gen_dashboard.py --user <username> --output dashboard.html --vscode

Zero dependencies beyond Python stdlib.
"""

import argparse
import csv
import html
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

SKILL_ROOT = Path(__file__).resolve().parent.parent
USERS_DIR = SKILL_ROOT / "users"


class DashboardError(ValueError):
    """Raised when a user's dashboard input is incomplete or invalid."""

ACTIVE_STATUSES = {"evaluating", "applied", "interviewing"}
HISTORY_STATUSES = {"offer", "rejected", "withdrawn"}

STAGE_ORDER = {"evaluating": 0, "applied": 1, "interviewing": 2}

STATUS_EMOJI = {
    "evaluating": "🔍",
    "applied": "📨",
    "interviewing": "🎭",
    "offer": "🎉",
    "rejected": "❌",
    "withdrawn": "🚫",
}

CSS = """\
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
       max-width: 1200px; margin: 0 auto; padding: 24px; background: #f8f9fa; color: #1a1a1a; }
h1 { margin-bottom: 8px; }
.meta { color: #666; margin-bottom: 24px; font-size: 0.9em; }
.assets { margin-bottom: 24px; padding: 12px 16px; background: #fff; border-radius: 8px;
          border: 1px solid #e0e0e0; }
.assets a { margin-right: 16px; text-decoration: none; color: #0366d6; }
.assets a:hover { text-decoration: underline; }
.section-title { margin: 24px 0 12px; font-size: 1.2em; font-weight: 600; }
.counts { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.count-badge { padding: 4px 12px; border-radius: 16px; font-size: 0.85em; font-weight: 500; }
.count-active { background: #e3f2fd; color: #1565c0; }
.count-evaluating { background: #fff3e0; color: #e65100; }
.count-applied { background: #e8f5e9; color: #2e7d32; }
.count-interviewing { background: #f3e5f5; color: #7b1fa2; }
.count-offer { background: #e8f5e9; color: #1b5e20; }
table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px;
        overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 24px; }
th { background: #f5f5f5; text-align: left; padding: 10px 12px; font-size: 0.85em;
     font-weight: 600; color: #555; border-bottom: 2px solid #e0e0e0; }
td { padding: 10px 12px; border-bottom: 1px solid #f0f0f0; font-size: 0.9em; }
tr:hover td { background: #fafafa; }
.score { font-weight: 700; }
.score-high { color: #2e7d32; }
.score-mid { color: #f57c00; }
.score-low { color: #c62828; }
a { color: #0366d6; text-decoration: none; }
a:hover { text-decoration: underline; }
.status { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; }
.status-evaluating { background: #fff3e0; color: #e65100; }
.status-applied { background: #e8f5e9; color: #2e7d32; }
.status-interviewing { background: #f3e5f5; color: #7b1fa2; }
.status-offer { background: #e8f5e9; color: #1b5e20; font-weight: 700; }
.status-rejected { background: #ffebee; color: #c62828; }
.status-withdrawn { background: #f5f5f5; color: #757575; }
details { margin-bottom: 8px; }
summary { cursor: pointer; color: #0366d6; font-size: 0.85em; }
.notes { color: #666; font-size: 0.85em; max-width: 300px; }
footer { margin-top: 32px; padding-top: 16px; border-top: 1px solid #e0e0e0;
         color: #999; font-size: 0.8em; }
"""


def load_tracker(user_dir: Path) -> list[dict]:
    tracker_path = user_dir / "tracker.csv"
    if not tracker_path.exists():
        raise DashboardError(
            f"tracker.csv not found in {user_dir}. Initialize the user workspace first."
        )
    with open(tracker_path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def find_job_dir(user_dir: Path, tid: int) -> Path | None:
    """Find job directory by ID prefix."""
    jobs_dir = user_dir / "jobs"
    if not jobs_dir.exists():
        return None
    prefix = f"{tid:03d}_"
    for d in jobs_dir.iterdir():
        if d.is_dir() and d.name.startswith(prefix):
            return d
    return None


def list_job_files(job_dir: Path) -> list[str]:
    """List notable files in a job directory."""
    if not job_dir or not job_dir.exists():
        return []
    notable = []
    for f in sorted(job_dir.iterdir()):
        if f.is_file() and not f.name.startswith("."):
            notable.append(f.name)
    return notable


def score_class(score: float) -> str:
    if score >= 4.0:
        return "score-high"
    elif score >= 3.5:
        return "score-mid"
    return "score-low"


def markdown_cell(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\r\n", "<br>").replace("\n", "<br>")


def markdown_path(path: Path, base_dir: Path) -> str:
    relative_path = path.relative_to(base_dir).as_posix()
    return quote(relative_path, safe="/._-~")


def markdown_link(label: str, path: Path, base_dir: Path) -> str:
    safe_label = markdown_cell(label).replace("[", "\\[").replace("]", "\\]")
    return f"[{safe_label}]({markdown_path(path, base_dir)})"


def external_markdown_link(label: str, url: str) -> str:
    safe_label = markdown_cell(label).replace("[", "\\[").replace("]", "\\]")
    safe_url = url.replace(")", "\\)")
    return f"[{safe_label}]({safe_url})"


def dashboard_rows(user_dir: Path) -> tuple[list[dict], list[dict]]:
    rows = load_tracker(user_dir)

    active = [r for r in rows if r.get("status") in ACTIVE_STATUSES]
    history = [r for r in rows if r.get("status") in HISTORY_STATUSES]

    def active_sort_key(r):
        try:
            score = -float(r.get("score", 0))
        except (ValueError, TypeError):
            score = 0
        stage = STAGE_ORDER.get(r.get("status", ""), 0)
        return (score, -stage, r.get("last_updated", "") or "")

    active.sort(key=active_sort_key)
    history.sort(key=lambda r: r.get("last_updated", "") or "", reverse=True)
    return active, history


def render_row(row: dict, job_dir: Path | None, user_dir: Path, use_vscode: bool) -> str:
    tid = int(row["id"])
    company = html.escape(row.get("company", ""))
    role = html.escape(row.get("role", ""))
    score_val = row.get("score", "")
    status = row.get("status", "")
    last_updated = html.escape(row.get("last_updated", "—"))
    notes = html.escape(row.get("notes", ""))
    url = row.get("url", "")

    # Score cell
    try:
        score_f = float(score_val)
        score_html = f'<span class="score {score_class(score_f)}">{score_f:.1f}</span>'
    except (ValueError, TypeError):
        score_html = "—"

    # Status cell
    emoji = STATUS_EMOJI.get(status, "")
    status_html = f'<span class="status status-{status}">{emoji} {status}</span>'

    # Company/role with link
    if url:
        company_html = f'<a href="{html.escape(url)}" title="Open JD">{company}</a>'
    else:
        company_html = company

    # Job dir link
    dir_link = ""
    if job_dir and job_dir.exists():
        file_uri = job_dir.as_uri()
        dir_link = f' <a href="{file_uri}" title="Open folder">📁</a>'
        if use_vscode:
            vscode_uri = f"vscode://file/{job_dir.as_posix()}"
            dir_link += f' <a href="{vscode_uri}" title="Open in VS Code">📝</a>'

    # Files detail
    files = list_job_files(job_dir)
    files_html = ""
    if files:
        file_list = ", ".join(files[:6])
        if len(files) > 6:
            file_list += f" (+{len(files)-6})"
        files_html = f'<details><summary>{len(files)} files</summary>{html.escape(file_list)}</details>'

    return f"""<tr>
  <td>{tid}</td>
  <td>{company_html}{dir_link}</td>
  <td>{role}</td>
  <td>{score_html}</td>
  <td>{status_html}</td>
  <td>{last_updated}</td>
  <td class="notes">{notes}</td>
  <td>{files_html}</td>
</tr>"""


def render_table(rows: list[dict], user_dir: Path, use_vscode: bool) -> str:
    if not rows:
        return "<p>No jobs in this category.</p>"

    header = """<table>
<thead><tr>
  <th>#</th><th>Company</th><th>Role</th><th>Score</th><th>Status</th><th>Updated</th><th>Notes</th><th>Files</th>
</tr></thead>
<tbody>"""
    body = ""
    for row in rows:
        tid = int(row["id"])
        job_dir = find_job_dir(user_dir, tid)
        body += render_row(row, job_dir, user_dir, use_vscode)
    return header + body + "\n</tbody></table>"


def render_markdown_row(row: dict, job_dir: Path | None, user_dir: Path) -> str:
    tid = int(row["id"])
    company = markdown_cell(row.get("company", ""))
    role = markdown_cell(row.get("role", ""))
    score_val = row.get("score", "")
    status = row.get("status", "")
    last_updated = markdown_cell(row.get("last_updated", "—"))
    notes = markdown_cell(row.get("notes", ""))
    url = row.get("url", "")

    try:
        score_cell = f"{float(score_val):.1f}"
    except (ValueError, TypeError):
        score_cell = "—"

    company_cell = external_markdown_link(company, url) if url else company
    files = list_job_files(job_dir)
    file_links = []
    if job_dir and job_dir.exists():
        for filename in files:
            file_links.append(markdown_link(filename, job_dir / filename, user_dir))
    files_cell = "<br>".join(file_links) if file_links else "—"

    return f"| {tid} | {company_cell} | {role} | {score_cell} | {markdown_cell(status)} | {last_updated} | {notes or '—'} | {files_cell} |"


def render_markdown_table(rows: list[dict], user_dir: Path) -> str:
    if not rows:
        return "_No jobs in this category._"

    lines = [
        "| # | Company | Role | Score | Status | Updated | Notes | Files |",
        "|---:|---|---|---:|---|---|---|---|",
    ]
    for row in rows:
        job_dir = find_job_dir(user_dir, int(row["id"]))
        lines.append(render_markdown_row(row, job_dir, user_dir))
    return "\n".join(lines)


def render_assets(user_dir: Path, use_vscode: bool) -> str:
    """Render links to global resume assets."""
    resume_dir = user_dir / "resume"
    links = []

    assets = [
        ("cv_master.md", "📚 母版简历"),
        ("direction_diagnosis.md", "🎯 方向诊断"),
        ("interview_playbook.md", "🎭 面试手册"),
    ]

    for filename, label in assets:
        path = resume_dir / filename
        if path.exists():
            links.append(f'<a href="{path.as_uri()}">{label}</a>')

    # Stable versions
    versions_dir = resume_dir / "versions"
    if versions_dir.exists():
        for v in sorted(versions_dir.iterdir()):
            if v.suffix == ".md":
                name = v.stem.replace("_", " ").title()
                links.append(f'<a href="{v.as_uri()}">📄 {html.escape(name)}</a>')

    if not links:
        return ""
    return f'<div class="assets">{"  ".join(links)}</div>'


def render_markdown_assets(user_dir: Path) -> str:
    resume_dir = user_dir / "resume"
    links = []

    assets = [
        ("cv_master.md", "📚 母版简历"),
        ("direction_diagnosis.md", "🎯 方向诊断"),
        ("interview_playbook.md", "🎭 面试手册"),
    ]

    for filename, label in assets:
        path = resume_dir / filename
        if path.exists():
            links.append(markdown_link(label, path, user_dir))

    versions_dir = resume_dir / "versions"
    if versions_dir.exists():
        for version in sorted(versions_dir.iterdir()):
            if version.suffix == ".md":
                name = version.stem.replace("_", " ").title()
                links.append(markdown_link(f"📄 {name}", version, user_dir))

    return "\n".join(f"- {link}" for link in links) if links else "_No resume assets found._"


def generate_dashboard_markdown(user_dir: Path) -> str:
    active, history = dashboard_rows(user_dir)

    n_active = len(active)
    n_evaluating = sum(1 for r in active if r["status"] == "evaluating")
    n_applied = sum(1 for r in active if r["status"] == "applied")
    n_interviewing = sum(1 for r in active if r["status"] == "interviewing")
    n_offer = sum(1 for r in history if r["status"] == "offer")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"""# Career Dashboard

Generated: {now}\\
User: `{markdown_cell(user_dir.name)}`

## Summary

| Metric | Count |
|---|---:|
| Active | {n_active} |
| Evaluating | {n_evaluating} |
| Applied | {n_applied} |
| Interviewing | {n_interviewing} |
| Offer | {n_offer} |

## Resume Assets

{render_markdown_assets(user_dir)}

## Active Applications

{render_markdown_table(active, user_dir)}

## History

{render_markdown_table(history, user_dir)}

---

Generated by `career-ops-cn/util/gen_dashboard.py`.\\
Data source: [tracker.csv](tracker.csv)
"""


def generate_dashboard(user_dir: Path, use_vscode: bool) -> str:
    active, history = dashboard_rows(user_dir)

    # Counts
    n_active = len(active)
    n_evaluating = sum(1 for r in active if r["status"] == "evaluating")
    n_applied = sum(1 for r in active if r["status"] == "applied")
    n_interviewing = sum(1 for r in active if r["status"] == "interviewing")
    n_offer = sum(1 for r in history if r["status"] == "offer")

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Career Dashboard — {html.escape(user_dir.name)}</title>
<style>{CSS}</style>
</head>
<body>
<h1>💼 Career Dashboard</h1>
<p class="meta">Generated: {now} · User: {html.escape(user_dir.name)}</p>

{render_assets(user_dir, use_vscode)}

<div class="counts">
  <span class="count-badge count-active">Active: {n_active}</span>
  <span class="count-badge count-evaluating">🔍 Evaluating: {n_evaluating}</span>
  <span class="count-badge count-applied">📨 Applied: {n_applied}</span>
  <span class="count-badge count-interviewing">🎭 Interviewing: {n_interviewing}</span>
  <span class="count-badge count-offer">🎉 Offer: {n_offer}</span>
</div>

<h2 class="section-title">Active Applications</h2>
{render_table(active, user_dir, use_vscode)}

<h2 class="section-title">History</h2>
{render_table(history, user_dir, use_vscode)}

<footer>
  Generated by <code>career-ops-cn/util/gen_dashboard.py</code> ·
  Data source: <code>tracker.csv</code> ·
  <a href="https://github.com/JackySummerfield/career-ops-cn">GitHub</a>
</footer>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Generate a Markdown or HTML career dashboard")
    parser.add_argument("--user", required=True, help="Username under users/")
    parser.add_argument("--output", default=None, help="Output path (default: users/<user>/dashboard.md)")
    parser.add_argument("--format", choices=("markdown", "html"), default=None, help="Output format (default: markdown)")
    parser.add_argument("--vscode", action="store_true", help="Include VS Code file URIs in HTML output")
    args = parser.parse_args()

    user_dir = USERS_DIR / args.user
    if not user_dir.exists():
        print(f"ERROR: User directory not found: {user_dir}")
        sys.exit(1)

    if args.output:
        output_path = Path(args.output)
        output_format = args.format or ("html" if output_path.suffix.lower() in {".htm", ".html"} else "markdown")
    else:
        output_format = args.format or "markdown"
        output_path = user_dir / ("dashboard.html" if output_format == "html" else "dashboard.md")

    try:
        dashboard = generate_dashboard(user_dir, args.vscode) if output_format == "html" else generate_dashboard_markdown(user_dir)
        output_path.write_text(dashboard, encoding="utf-8")
    except (DashboardError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"✅ {output_format.title()} dashboard generated: {output_path}")


if __name__ == "__main__":
    main()
