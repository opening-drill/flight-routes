"""
Application settings from new_impl/app.ini and repo-root .env.

Import this module before redis/db legacy imports (e.g. `database`, `monitor`).
It loads .env, applies PYTHONPATH from env or app.ini, and exposes `settings`.
"""

from __future__ import annotations

import os
import sys
from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path

NEW_IMPL_DIR = Path(__file__).resolve().parent
REPO_ROOT = NEW_IMPL_DIR.parent
APP_INI = NEW_IMPL_DIR / "app.ini"
ENV_FILE = REPO_ROOT / ".env"

# Maps .env variable names → confluent-kafka config keys
_KAFKA_ENV_MAP = {
    "KAFKA_BOOTSTRAP_SERVERS": "bootstrap.servers",
    "KAFKA_SECURITY_PROTOCOL": "security.protocol",
    "KAFKA_SASL_MECHANISMS": "sasl.mechanisms",
    "KAFKA_SASL_USERNAME": "sasl.username",
    "KAFKA_SASL_PASSWORD": "sasl.password",
    "KAFKA_CLIENT_ID": "client.id",
    "KAFKA_SESSION_TIMEOUT_MS": "session.timeout.ms",
}


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(ENV_FILE)


def _setup_import_paths(ini: ConfigParser) -> None:
    """
    Legacy redis/db modules use flat imports (`from database import …`).
    They are not installed as a package, so their directories must be on sys.path.
    """
    raw = os.getenv("PYTHONPATH") or ini.get("paths", "pythonpath", fallback="")
    if not raw.strip():
        return

    sep = os.pathsep if os.getenv("PYTHONPATH") else ":"
    entries = raw.split(sep) if os.getenv("PYTHONPATH") else raw.split(":")

    for entry in reversed(entries):
        entry = entry.strip()
        if not entry:
            continue
        path = Path(entry)
        if not path.is_absolute():
            path = (REPO_ROOT / path).resolve()
        else:
            path = path.resolve()
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))


def _read_properties_file(path: Path) -> dict[str, str]:
    config: dict[str, str] = {}
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                config[key] = value.strip()
    return config


@dataclass(frozen=True)
class Settings:
    repo_root: Path
    kafka_topic: str
    kafka_group_id: str
    kafka_auto_offset_reset: str
    kafka_properties_file: Path
    redis_host: str
    redis_port: int
    redis_db: int
    monitor_interval_seconds: int
    safety_buffer_meters: float
    polygons_api_url: str
    core_api_key: str

    def kafka_consumer_config(self) -> dict[str, str]:
        props_path = self.kafka_properties_file
        if not props_path.is_file():
            raise FileNotFoundError(f"Kafka properties file not found: {props_path}")

        config = _read_properties_file(props_path)

        for env_key, kafka_key in _KAFKA_ENV_MAP.items():
            value = os.getenv(env_key)
            if value:
                config[kafka_key] = value

        config["group.id"] = self.kafka_group_id
        config["auto.offset.reset"] = self.kafka_auto_offset_reset
        return config


def _int_env(name: str, fallback: int) -> int:
    raw = os.getenv(name)
    return int(raw) if raw is not None else fallback


def _float_env(name: str, fallback: float) -> float:
    raw = os.getenv(name)
    return float(raw) if raw is not None else fallback


def _load_settings() -> Settings:
    ini = ConfigParser()
    if not ini.read(APP_INI):
        raise FileNotFoundError(f"Config file not found: {APP_INI}")

    kafka_props = ini.get("kafka", "properties_file")
    props_path = Path(kafka_props)
    if not props_path.is_absolute():
        props_path = REPO_ROOT / props_path

    core_base = os.getenv("CORE_BASE_URL", ini.get("api", "core_base_url", fallback="")).strip()
    default_polygons_url = (
        f"{core_base.rstrip('/')}/api/polygons" if core_base else ini.get("api", "polygons_url")
    )
    polygons_url = (os.getenv("POLYGONS_API_URL") or default_polygons_url).strip()
    core_api_key = os.getenv("CORE_API_KEY") or ini.get("api", "api_key", fallback="")

    return Settings(
        repo_root=REPO_ROOT,
        kafka_topic=ini.get("kafka", "topic"),
        kafka_group_id=ini.get("kafka", "group_id"),
        kafka_auto_offset_reset=ini.get("kafka", "auto_offset_reset"),
        kafka_properties_file=props_path,
        redis_host=os.getenv("REDIS_HOST", ini.get("redis", "host")),
        redis_port=_int_env("REDIS_PORT", ini.getint("redis", "port")),
        redis_db=_int_env("REDIS_DB", ini.getint("redis", "db")),
        monitor_interval_seconds=_int_env(
            "MONITOR_INTERVAL_SECONDS",
            ini.getint("monitor", "interval_seconds"),
        ),
        safety_buffer_meters=_float_env(
            "SAFETY_BUFFER_METERS",
            ini.getfloat("planner", "safety_buffer_meters"),
        ),
        polygons_api_url=polygons_url,
        core_api_key=core_api_key,
    )


def _apply_api_env_from_settings() -> None:
    """Push ini/.env values into os.environ before api_client is imported elsewhere."""
    if settings.polygons_api_url and not os.getenv("POLYGONS_API_URL"):
        os.environ["POLYGONS_API_URL"] = settings.polygons_api_url
    if settings.core_api_key and not os.getenv("CORE_API_KEY"):
        os.environ["CORE_API_KEY"] = settings.core_api_key


_load_dotenv()
_ini = ConfigParser()
_ini.read(APP_INI)
_setup_import_paths(_ini)
settings = _load_settings()
_apply_api_env_from_settings()

# Backwards-compatible aliases for modules that import these names
SAFETY_BUFFER_METERS = settings.safety_buffer_meters
MONITOR_POLL_INTERVAL_SECONDS = settings.monitor_interval_seconds
KAFKA_TOPIC = settings.kafka_topic
KAFKA_GROUP_ID = settings.kafka_group_id
