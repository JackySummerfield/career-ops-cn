"""Build a deterministic public Career Ops bundle from an explicit allowlist.

The builder intentionally knows nothing about private data repositories. It
packages only public program files, documentation, workflows, and synthetic
tests; migration notes and user data are excluded even when present beside
the source checkout.
"""

from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path


PUBLIC_FILES = frozenset({".gitignore", "LICENSE", "README.en.md", "README.md", "SKILL.md"})
PUBLIC_DIRECTORIES = frozenset({"agents", "docs", "references", "tests", "util", "workflows"})
FORBIDDEN_PARTS = frozenset({".git", "users", "backups", "dist", "__pycache__"})


class BundleError(ValueError):
    """Raised when a source checkout is outside the public build boundary."""


def collect_public_files(source_root: Path) -> list[Path]:
    source_root = source_root.expanduser().resolve()
    if not source_root.is_dir():
        raise BundleError(f"Source root is not a directory: {source_root}")

    files: list[Path] = []
    for relative in sorted(PUBLIC_FILES):
        path = source_root / relative
        if path.is_symlink():
            raise BundleError(f"Symlinks are not allowed in public bundles: {relative}")
        if not path.is_file():
            raise BundleError(f"Required public file is missing: {relative}")
        _ensure_contained(source_root, path)
        files.append(path)

    for directory in sorted(PUBLIC_DIRECTORIES):
        directory_path = source_root / directory
        if directory_path.is_symlink():
            raise BundleError(f"Symlinks are not allowed in public bundles: {directory}")
        if not directory_path.is_dir():
            raise BundleError(f"Required public directory is missing: {directory}")
        for path in sorted(directory_path.rglob("*")):
            if path.is_symlink():
                relative = path.relative_to(source_root).as_posix()
                raise BundleError(f"Symlinks are not allowed in public bundles: {relative}")
            if not path.is_file():
                continue
            _ensure_contained(source_root, path)
            relative_parts = path.relative_to(source_root).parts
            if FORBIDDEN_PARTS.intersection(relative_parts) or path.suffix in {".pyc", ".pyo"}:
                continue
            files.append(path)

    unique = {path.relative_to(source_root).as_posix(): path for path in files}
    return [unique[key] for key in sorted(unique)]


def _ensure_contained(source_root: Path, path: Path) -> None:
    """Reject files whose resolved location escapes the public checkout."""
    try:
        path.resolve().relative_to(source_root)
    except ValueError as exc:
        relative = path.relative_to(source_root).as_posix()
        raise BundleError(f"Public bundle path escapes source root: {relative}") from exc


def build_bundle(source_root: Path, output_path: Path) -> tuple[int, str]:
    source_root = source_root.expanduser().resolve()
    output_path = output_path.expanduser().resolve()
    files = collect_public_files(source_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            relative = path.relative_to(source_root).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())

    digest = hashlib.sha256(output_path.read_bytes()).hexdigest()
    return len(files), digest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a public-only Career Ops bundle")
    parser.add_argument("--source", default=".", help="Public program checkout")
    parser.add_argument("--output", required=True, help="Output ZIP path")
    args = parser.parse_args()

    try:
        count, digest = build_bundle(Path(args.source), Path(args.output))
    except (BundleError, OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"public_bundle_files={count}")
    print(f"public_bundle_sha256={digest}")


if __name__ == "__main__":
    main()
