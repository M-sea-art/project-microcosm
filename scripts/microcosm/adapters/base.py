import os
from pathlib import Path


EXCLUDED_DIR_NAMES = {
    ".git",
    ".microcosm",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".ssh",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "env",
    "htmlcov",
    "node_modules",
    "venv",
}
SECRET_FILE_NAMES = {"id_dsa", "id_ed25519", "id_rsa"}
SECRET_SUFFIXES = {".key", ".p12", ".pem", ".pfx"}


def should_skip_path(project_root, path):
    root = Path(project_root).resolve()
    candidate = Path(path).resolve()
    try:
        relative = candidate.relative_to(root)
    except ValueError:
        return True
    parts = {part.lower() for part in relative.parts}
    name = candidate.name.lower()
    return (
        bool(parts & EXCLUDED_DIR_NAMES)
        or name == ".env"
        or name.startswith(".env.")
        or name in SECRET_FILE_NAMES
        or candidate.suffix.lower() in SECRET_SUFFIXES
    )


def iter_project_paths(project_root):
    root = Path(project_root).resolve()
    for current, dir_names, file_names in os.walk(root):
        current_path = Path(current)
        dir_names[:] = sorted(
            name
            for name in dir_names
            if not should_skip_path(root, current_path / name)
        )
        for name in dir_names:
            yield current_path / name
        for name in sorted(file_names):
            path = current_path / name
            if not should_skip_path(root, path):
                yield path


def iter_project_files(project_root, suffixes=None):
    normalized = {suffix.lower() for suffix in suffixes or []}
    for path in iter_project_paths(project_root):
        if path.is_file() and (not normalized or path.suffix.lower() in normalized):
            yield path


class Adapter:
    name = "base"

    def available(self, project_root):
        return True

    def scan(self, project_root):
        return {
            "nodes": [],
            "edges": [],
            "observations": [],
            "evidence": [],
            "inferred": [],
            "proposed": [],
        }
