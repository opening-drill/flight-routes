import os
from pathlib import Path


def load_project_env(env_path: str | Path | None = None) -> Path:
    resolved_env_path = Path(env_path) if env_path else _default_env_path()

    if not resolved_env_path.exists():
        return resolved_env_path

    for raw_line in resolved_env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), _normalize_env_value(value.strip()))

    return resolved_env_path


def _default_env_path() -> Path:
    return Path(__file__).resolve().parent.parent / ".env"


def _normalize_env_value(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]

    return value
