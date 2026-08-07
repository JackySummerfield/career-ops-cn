"""Data-boundary and optimistic-concurrency primitives for Career Ops.

The public skill never discovers a user's data by walking its own repository.
Local runs receive an explicit data-repository root. Cloud runs receive an
explicit GitHub repository name from the GitHub connector. This module keeps
that policy small, dependency-free, and testable without private data.
"""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Mapping


LOCAL_MODE = "local"
CLOUD_MODE = "cloud"

ALLOWED_DATA_ROOTS = frozenset({"profile", "tracker", "jobs", "resumes"})
ALLOWED_TEXT_SUFFIXES = frozenset({".csv", ".json", ".md", ".txt", ".yaml", ".yml"})
MAX_TEXT_BYTES = 4 * 1024 * 1024

_CREDENTIAL_PATTERNS = (
    re.compile(r"(?:ghp_|github_pat_|xox[baprs]-)[A-Za-z0-9_-]{12,}"),
    re.compile(r"-----BEGIN (?:OPENSSH|RSA|EC|DSA|PRIVATE) KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b(?:sk|rk)-[A-Za-z0-9_-]{16,}\b"),
)


class DataBoundaryError(ValueError):
    """Raised when an operation would cross the configured data boundary."""


class ConcurrentWriteError(DataBoundaryError):
    """Raised when a write was based on a stale file revision."""


def normalize_repo_path(path: str | Path) -> str:
    """Return a safe POSIX repository path or raise on traversal attempts."""

    raw = str(path).replace("\\", "/")
    if not raw or raw.startswith("/") or "\x00" in raw:
        raise DataBoundaryError(f"Repository path must be relative: {path!r}")

    parts = PurePosixPath(raw).parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise DataBoundaryError(f"Repository path contains an unsafe segment: {path!r}")
    return "/".join(parts)


def validate_data_path(path: str | Path, *, writable: bool = True) -> str:
    """Validate a path against the migrated private-repository layout."""

    normalized = normalize_repo_path(path)
    parts = normalized.split("/")
    if parts[0] not in ALLOWED_DATA_ROOTS:
        raise DataBoundaryError(
            f"Path {normalized!r} is outside the data allowlist: {sorted(ALLOWED_DATA_ROOTS)}"
        )
    if parts[0] == "tracker" and normalized != "tracker/tracker.csv":
        raise DataBoundaryError("Only tracker/tracker.csv is allowed under tracker/")

    suffix = Path(parts[-1]).suffix.lower()
    if suffix not in ALLOWED_TEXT_SUFFIXES:
        action = "written" if writable else "read"
        raise DataBoundaryError(
            f"Only text result files may be {action}; unsupported suffix: {suffix or '<none>'}"
        )
    return normalized


def validate_text_payload(content: str) -> str:
    """Validate UTF-8 text and reject obvious credential material."""

    if not isinstance(content, str):
        raise DataBoundaryError("Data writes must contain a string payload")
    if "\x00" in content:
        raise DataBoundaryError("Binary/NUL content is not allowed in text data")
    try:
        content.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise DataBoundaryError("Payload must be valid UTF-8 text") from exc
    if len(content.encode("utf-8")) > MAX_TEXT_BYTES:
        raise DataBoundaryError(f"Payload exceeds the {MAX_TEXT_BYTES} byte limit")
    for pattern in _CREDENTIAL_PATTERNS:
        if pattern.search(content):
            raise DataBoundaryError("Credential-like content cannot be written by this adapter")
    return content


def validate_cloud_repository(repository: str, allowed_repository: str | None) -> str:
    """Allow cloud access only to the repository injected by private configuration."""

    if not repository or not allowed_repository:
        raise DataBoundaryError(
            "Cloud mode requires both the current and explicitly allowed private repository"
        )
    if repository != allowed_repository:
        raise DataBoundaryError("Cloud repository is outside the configured private-data boundary")
    return repository


def sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def assert_expected_sha(expected_sha: str | None, actual_sha: str | None) -> None:
    """Require the caller's read revision to match the current revision."""

    if expected_sha != actual_sha:
        raise ConcurrentWriteError(
            "Data changed after it was read; reload the file and regenerate the preview"
        )


@dataclass(frozen=True)
class DataPaths:
    """Canonical paths inside a local private data repository."""

    root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", Path(self.root).expanduser().resolve())

    @property
    def profile(self) -> Path:
        return self.root / "profile"

    @property
    def tracker(self) -> Path:
        return self.root / "tracker" / "tracker.csv"

    @property
    def jobs(self) -> Path:
        return self.root / "jobs"

    @property
    def resumes(self) -> Path:
        return self.root / "resumes"

    def local_path(self, repository_path: str | Path, *, writable: bool = True) -> Path:
        relative = validate_data_path(repository_path, writable=writable)
        candidate = (self.root / relative).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise DataBoundaryError("Resolved path escaped the configured data root")
        return candidate


@dataclass(frozen=True)
class RuntimeConfig:
    """Explicit local/cloud runtime configuration."""

    mode: str
    data_root: Path | None = None
    repository: str | None = None
    allowed_repository: str | None = None

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "RuntimeConfig":
        env = os.environ if environ is None else environ
        mode = env.get("CAREER_OPS_MODE", LOCAL_MODE).strip().lower()
        if mode == LOCAL_MODE:
            raw_root = env.get("CAREER_OPS_DATA_ROOT", "").strip()
            if not raw_root:
                raise DataBoundaryError(
                    "Set CAREER_OPS_DATA_ROOT to an external private data repository"
                )
            root = Path(raw_root).expanduser().resolve()
            if not root.is_dir():
                raise DataBoundaryError(f"CAREER_OPS_DATA_ROOT is not a directory: {root}")
            return cls(mode=LOCAL_MODE, data_root=root)
        if mode == CLOUD_MODE:
            repository = env.get("CAREER_OPS_GITHUB_REPO", "").strip()
            allowed_repository = env.get("CAREER_OPS_ALLOWED_DATA_REPOSITORY", "").strip()
            validate_cloud_repository(repository, allowed_repository)
            return cls(
                mode=CLOUD_MODE,
                repository=repository,
                allowed_repository=allowed_repository,
            )
        raise DataBoundaryError("CAREER_OPS_MODE must be 'local' or 'cloud'")


@dataclass(frozen=True)
class WriteIntent:
    """A previewable cloud/local text write with an optimistic lock."""

    repository: str
    path: str
    content: str
    expected_sha: str | None
    allowed_repository: str | None = None

    def validated(self) -> "WriteIntent":
        validate_cloud_repository(self.repository, self.allowed_repository)
        normalized = validate_data_path(self.path, writable=True)
        validate_text_payload(self.content)
        return WriteIntent(
            self.repository,
            normalized,
            self.content,
            self.expected_sha,
            self.allowed_repository,
        )

    def summary(self, actual_sha: str | None = None) -> dict[str, str | None]:
        intent = self.validated()
        return {
            "operation": "write_text",
            "repository": intent.repository,
            "path": intent.path,
            "expected_sha": intent.expected_sha,
            "actual_sha": actual_sha,
            "new_sha": sha256_text(intent.content),
        }


class LocalDataAdapter:
    """Small local adapter used by desktop clients and tests."""

    def __init__(self, root: Path) -> None:
        self.paths = DataPaths(root)

    def read(self, repository_path: str | Path) -> tuple[str, str]:
        path = self.paths.local_path(repository_path, writable=False)
        content = path.read_text(encoding="utf-8")
        return content, sha256_text(content)

    def write(
        self,
        repository_path: str | Path,
        content: str,
        *,
        expected_sha: str | None,
    ) -> str:
        path = self.paths.local_path(repository_path, writable=True)
        validate_text_payload(content)
        current_content = path.read_text(encoding="utf-8") if path.exists() else None
        current_sha = sha256_text(current_content) if current_content is not None else None
        assert_expected_sha(expected_sha, current_sha)

        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(content)
        os.replace(temporary_path, path)
        return sha256_text(content)


class CloudDataAdapter:
    """Policy adapter for the GitHub plugin; network I/O stays in the connector."""

    def __init__(self, repository: str, allowed_repository: str) -> None:
        self.repository = validate_cloud_repository(repository, allowed_repository)
        self.allowed_repository = allowed_repository

    def prepare_write(
        self,
        repository_path: str | Path,
        content: str,
        *,
        expected_sha: str | None,
    ) -> WriteIntent:
        """Validate a plugin write before it calls GitHub's API."""
        return WriteIntent(
            repository=self.repository,
            path=str(repository_path),
            content=content,
            expected_sha=expected_sha,
            allowed_repository=self.allowed_repository,
        ).validated()

    def verify_revision(self, expected_sha: str | None, actual_sha: str | None) -> None:
        """Require a fresh read immediately before the plugin writes."""
        assert_expected_sha(expected_sha, actual_sha)
