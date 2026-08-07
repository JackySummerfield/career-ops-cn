# Client Metadata

`openai.yaml` contains display metadata for Codex-compatible clients: the agent name, short description, and default prompt. It is optional client metadata, not a second source of workflow instructions. The canonical workflow and routing instructions remain in `SKILL.md` and `workflows/`.

## Data connector contract

The agent wrapper does not bundle a data connector or private files. A client must choose one boundary
before a workflow starts:

- local: set `CAREER_OPS_DATA_ROOT` to an external private data repository;
- cloud: use the GitHub connector only with the repository configured as `CAREER_OPS_ALLOWED_DATA_REPOSITORY`.

Cloud writes follow the contract in [`../util/data_boundary.py`](../util/data_boundary.py): validate the
repository and path allowlists, read the current file and SHA, show a content preview, and write only when
the expected SHA still matches. Cloud dashboards are returned as conversation Markdown; local-only file and
VS Code URIs are never emitted by cloud output.
