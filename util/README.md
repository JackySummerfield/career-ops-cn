# Utility Scripts

These scripts are optional local helpers for an external private data repository. They require an explicit
`--data-root` (or `CAREER_OPS_DATA_ROOT`) and do not read from the public Skill repository. They do not make
network requests unless `fetch_jd.py` is explicitly used.

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
python util/gen_dashboard.py --data-root "$CAREER_OPS_DATA_ROOT"

# Optional standalone browser dashboard
python util/gen_dashboard.py --data-root "$CAREER_OPS_DATA_ROOT" --format html

# Include VS Code file links in the HTML dashboard
python util/gen_dashboard.py --data-root "$CAREER_OPS_DATA_ROOT" --format html --vscode

# Render interview_prep.md to a standalone HTML companion
python util/render_markdown.py \
  "$CAREER_OPS_DATA_ROOT/jobs/{id:03d}_{company}_{role}/interview_prep.md" \
  --output "$CAREER_OPS_DATA_ROOT/jobs/{id:03d}_{company}_{role}/interview_prep.html"

# Optional rendered-page fallback for clients without browser control
python util/fetch_jd.py "https://example.com/job"
```

## Output and privacy

- `dashboard.md` is the portable source for Obsidian, VS Code Markdown Preview, GitHub, and other standard Markdown readers.
- `dashboard.html` and `interview_prep.html` are local reading companions; they may contain machine-specific file links.
- Keep generated dashboards and local HTML companions outside the public Skill repository. Raw recordings,
  screenshots, PDFs, DOCX files, and credentials must never be written by these utilities into Git.
- Cloud mode is intentionally unsupported by the file-writing utilities: the GitHub plugin should render
  Markdown in the conversation and use the data-boundary/SHA checks before an atomic repository write.
- Do not commit credentials, cookies, browser profiles, or private session data.
