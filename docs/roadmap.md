# Roadmap — Career Ops CN

**Status:** Core workflows usable · Dashboard generator planned · Last updated: 2026-07-21

This roadmap describes **what** lands **when**. For current workflow behavior and data conventions, see [`SKILL.md`](../SKILL.md) and [`workflows/`](../workflows/).

---

## Current foundation — Core career workflows

**Theme:** keep one private, file-based source of truth for the complete job-search lifecycle.

- [x] Bilingual master resume and stable direction-specific resume versions
- [x] Layered JD acquisition and 10-dimension evaluation
- [x] CSV application tracker with controlled statuses
- [x] Per-job evaluation and timeline assets
- [x] Resume tailoring, interview preparation, and interview debrief workflows
- [x] Multi-user isolation under gitignored `users/<username>/` directories

---

## Next milestone — Static HTML dashboard

**Theme:** provide a zero-dependency visual overview of career assets and application progress, generated from existing files, without introducing a server or runtime service.

### Rationale

- Users already work inside an AI assistant (Copilot / Codex / Claude Code) that can read and update `tracker.csv` on demand — a live server adds little over what the AI already provides.
- A generated static HTML file covers the core "glance at all jobs" need with zero startup friction (double-click to open).
- Status updates remain in the AI workflow (`加入tracker` / `更新状态`) where validation and timeline sync already work.
- If static HTML proves insufficient, upgrading to a localhost portal later is straightforward because the data layer doesn't change.

### Phase 1 — Normalize job assets

- [ ] Add a migration script (`util/migrate_jobs.py`) with `--dry-run` output before filesystem changes
- [ ] Back up `tracker.csv` and `jobs/` to a timestamped ZIP before migration
- [ ] Standardize job directory names as `{id:03d}_{company}_{role}`
- [ ] Preserve Tracker ID as the stable key; sanitize only Windows-invalid path characters
- [ ] Merge duplicate assets for any Tracker ID that maps to multiple directories
- [ ] Create standard directories for Tracker records that currently have none
- [ ] Generate only evidence-backed minimal `timeline.md` for missing records
- [ ] Validate every Tracker ID resolves to exactly one job directory after migration
- [ ] Update W2 so new jobs use the same naming rule

### Phase 2 — Build the dashboard generator

- [ ] Add `util/gen_dashboard.py` — reads `tracker.csv` + `jobs/` and writes `dashboard.html`
- [ ] Zero runtime dependencies (Python stdlib only: `csv`, `pathlib`, `html`, `datetime`)
- [ ] Split into Active (`evaluating`, `applied`, `interviewing`) and History (`offer`, `rejected`, `withdrawn`) tables
- [ ] Sort Active by score descending → stage progress → last update; History by most recent date
- [ ] Each row links to the job directory via `file:///` and optionally a VS Code URI (`vscode://file/...`)
- [ ] Show global asset links: master resume, direction diagnosis, stable resume versions
- [ ] Embed minimal CSS for readability; no JavaScript required for core viewing
- [ ] Optional: collapsible job detail (eval summary, timeline) via `<details>` tags

### Phase 3 — Integrate into workflow

- [ ] Add a `generate_dashboard` step at the end of W2 (after tracker update) to auto-regenerate
- [ ] Add Windows `gen-dashboard.cmd` one-click launcher
- [ ] Document in READMEs: what it generates, how to run, how to customize

### Acceptance criteria

1. `python util/gen_dashboard.py --user <name>` produces a self-contained `dashboard.html` without network requests.
2. Double-clicking the HTML shows Active/History tables with correct sorting and working file links.
3. The generator runs in < 1 second for typical tracker sizes (< 50 jobs).
4. No server, no Node.js, no frontend framework, no background process.

### Deliberate non-goals (for now)

- In-browser status editing (use AI workflow instead)
- Live/auto-refresh (regenerate when data changes)
- Markdown rendering inside the dashboard (link to source files)
- Charts, funnel analytics, or conversion-rate metrics
- A database, hosted service, or login system

---

## Later considerations

These items require evidence from real dashboard usage before entering a committed milestone:

- **Upgrade to localhost portal** — if "regenerate after every change" becomes too much friction AND in-browser status update is genuinely needed, introduce a minimal Python HTTP server
- Optional `next_action` and `next_action_date` Tracker fields if missed follow-ups become a recurring problem
- In-browser Markdown rendering for eval/timeline if linking to source files proves insufficient
- Saved filters or search if the two-table layout becomes inadequate at scale
