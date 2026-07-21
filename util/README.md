# Utility Scripts

These scripts are optional local helpers for a user workspace. They read and write files under `users/<username>/`; they do not make network requests unless `fetch_jd.py` is explicitly used.

## Requirements

- Python 3.10 or newer.
- `gen_dashboard.py` and `render_markdown.py` use only the Python standard library.
- `fetch_jd.py` is an optional fallback and requires Playwright:

  ```bash
  pip install playwright
  playwright install chromium
  ```

  Use the fallback only when the client has no supported browser-control capability. It opens a separate visible browser, does not read an existing browser profile, and does not bypass CAPTCHA, security challenges, or access controls.

## Commands

Run these commands from the skill root:

```bash
# Markdown-first dashboard (default)
python util/gen_dashboard.py --user <username>

# Optional standalone browser dashboard
python util/gen_dashboard.py --user <username> --format html

# Include VS Code file links in the HTML dashboard
python util/gen_dashboard.py --user <username> --format html --vscode

# Render interview_prep.md to a standalone HTML companion
python util/render_markdown.py \
  "users/<username>/jobs/{id:03d}_{company}_{role}/interview_prep.md" \
  --output "users/<username>/jobs/{id:03d}_{company}_{role}/interview_prep.html"

# Optional rendered-page fallback for clients without browser control
python util/fetch_jd.py "https://example.com/job"
```

## Output and privacy

- `dashboard.md` is the portable source for Obsidian, VS Code Markdown Preview, GitHub, and other standard Markdown readers.
- `dashboard.html` and `interview_prep.html` are local reading companions; they may contain machine-specific file links.
- Keep all generated dashboards, resumes, job records, transcripts, and fetched JDs inside the gitignored `users/` directory.
- Do not commit credentials, cookies, browser profiles, or private session data.
