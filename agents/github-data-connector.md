# GitHub data connector contract

This is the V1 connector contract for a GitHub-plugin-backed Career Ops client. It is an instruction layer,
not a custom MCP implementation.

The public installation artifact must be built with `python util/build_public_bundle.py`; that builder uses a
whitelist and never includes private data repositories or migration notes.

## Allowed scope

- Repository: `<PRIVATE_DATA_REPOSITORY>` supplied by private runtime configuration
- Writable paths: `profile/**`, `tracker/tracker.csv`, `jobs/**`, `resumes/**`
- Writable file types: Markdown, CSV, TXT, JSON, YAML
- Forbidden repositories: the public program repository, every unapproved data repository, and every other repository
- Forbidden content: attachments, recordings, screenshots, office documents, credentials, and binary files

The private runtime supplies the current repository as `CAREER_OPS_GITHUB_REPO` and the approved target as
`CAREER_OPS_ALLOWED_DATA_REPOSITORY`. The public repository contains neither value.

## Read/preview/write sequence

1. Read the target file and record the current `main` SHA and file blob SHA.
2. Validate the normalized path and UTF-8 text payload with `util/data_boundary.py`.
3. Show the proposed diff or replacement preview to the user before writing.
4. Re-check `main` and the target file SHA immediately before the write.
5. If either SHA changed, stop and reload; never silently overwrite a concurrent change.
6. Commit the complete user operation as one atomic text-only commit to `main`.
7. Report only operation type, repository, path, SHA/result, and task status; never log document contents.

## Dashboard behavior

The connector reads the tracker and referenced Markdown files, then renders a Markdown dashboard in the
conversation. It must not create `file://`, `vscode://`, absolute local paths, HTML artifacts, or public
repository files.
