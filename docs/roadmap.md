# Roadmap — Career Ops CN

**Status:** Core workflows usable · Portable Markdown/HTML dashboard complete · Last updated: 2026-07-21

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

## Next milestone — Portable Markdown + HTML dashboards

**Theme:** provide portable Markdown navigation plus an optional zero-dependency HTML view of career assets and application progress, generated from existing files, without introducing a server or runtime service.

### Rationale

- Users already work inside an AI assistant (Copilot / Codex / Claude Code) that can read and update `tracker.csv` on demand — a live server adds little over what the AI already provides.
- A generated Markdown file works in Obsidian, VS Code Markdown Preview, GitHub, and other standard Markdown readers.
- An optional static HTML file covers the browser-only case with zero startup friction (double-click to open).
- Status updates remain in the AI workflow (`加入tracker` / `更新状态`) where validation and timeline sync already work.
- If static HTML proves insufficient, upgrading to a localhost portal later is straightforward because the data layer doesn't change.

### Completed maintenance — Normalize job assets

Job directories were normalized during private workspace maintenance. The public
skill keeps the `{id:03d}_{company}_{role}` naming rule for new records, but does
not ship a one-time migration or rename utility.

### Phase 2 — Build the dashboard generator

- [x] Add `util/gen_dashboard.py` — reads `tracker.csv` + `jobs/` and writes `dashboard.md` by default, with optional `dashboard.html`
- [x] Add `util/render_markdown.py` — render interview-prep Markdown as responsive standalone HTML with no external dependency
- [x] Zero runtime dependencies (Python stdlib only: `csv`, `pathlib`, `html`, `datetime`, `urllib.parse`)
- [x] Split into Active (`evaluating`, `applied`, `interviewing`) and History (`offer`, `rejected`, `withdrawn`) tables
- [x] Sort Active by score descending → stage progress → last update; History by most recent date
- [x] Markdown rows use relative links to actual job files so they work across standard Markdown readers
- [x] HTML rows retain local directory links and optionally a VS Code URI (`vscode://file/...`)
- [x] Show global asset links: master resume, direction diagnosis, stable resume versions
- [x] Embed minimal CSS for readability; no JavaScript required for core viewing
- [ ] Optional: collapsible job detail (eval summary, timeline) via `<details>` tags

### Phase 3 — Integrate into workflow

- [x] Add a `generate_dashboard` step at the end of W2 (after tracker update) to auto-regenerate
- [x] Add Windows `gen-dashboard.cmd` one-click launcher
- [x] Document in READMEs: what it generates, how to run, how to customize

### Acceptance criteria

1. `python util/gen_dashboard.py --user <name>` produces a standard `dashboard.md` without network requests.
2. `python util/gen_dashboard.py --user <name> --format html` produces a self-contained `dashboard.html` without network requests.
3. Markdown readers show Active/History tables with correct sorting and working relative file links.
4. Double-clicking the HTML shows Active/History tables with correct sorting and working local links.
5. The generator runs in < 1 second for typical tracker sizes (< 50 jobs).
6. No server, no Node.js, no frontend framework, no background process.

### Deliberate non-goals (for now)

- In-browser status editing (use AI workflow instead)
- Live/auto-refresh (regenerate when data changes)
- In-browser Markdown rendering inside the HTML dashboard (the Markdown dashboard links to source files)
- Charts, funnel analytics, or conversion-rate metrics
- A database, hosted service, or login system

---

## Later considerations

These items require evidence from real dashboard usage before entering a committed milestone:

- **Upgrade to localhost portal** — if "regenerate after every change" becomes too much friction AND in-browser status update is genuinely needed, introduce a minimal Python HTTP server
- Optional `next_action` and `next_action_date` Tracker fields if missed follow-ups become a recurring problem
- In-browser Markdown rendering for eval/timeline if linking to source files proves insufficient
- Saved filters or search if the two-table layout becomes inadequate at scale
