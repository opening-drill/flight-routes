import os

from src.config.constants import (
    DEFAULT_ALLOWED_POINT_MAX_ATTEMPTS,
    DEFAULT_API_KEY_HEADER_NAME,
    DEFAULT_API_LOGIN_PASSWORD,
    DEFAULT_API_LOGIN_URL,
    DEFAULT_API_LOGIN_USERNAME,
    DEFAULT_DISPATCH_TIMEOUT_SECONDS,
    DEFAULT_DISPATCH_URL,
    DEFAULT_JSON_OUTPUT_INDENT,
    DEFAULT_POSTGRES_AIRCRAFT_TABLE,
    DEFAULT_POSTGRES_EVENT_TABLE,
    DEFAULT_POSTGRES_POLYGON_TABLE,
    DEFAULT_POSTGRES_PORT,
    DEFAULT_POSTGRES_SCHEMA,
    DEFAULT_SIMULATION_FLIGHT_COUNT,
    DEFAULT_UNUSED_EVENT_ID_MAX_ATTEMPTS,
    ENV_ALLOWED_POINT_MAX_ATTEMPTS,
    ENV_API_KEY,
    ENV_API_KEY_HEADER_NAME,
    ENV_API_LOGIN_PASSWORD,
    ENV_API_LOGIN_URL,
    ENV_API_LOGIN_USERNAME,
    ENV_DISPATCH_TIMEOUT_SECONDS,
    ENV_DISPATCH_URL,
    ENV_JSON_OUTPUT_INDENT,
    ENV_POSTGRES_AIRCRAFT_TABLE,
    ENV_POSTGRES_BUSY_STATUS,
    ENV_POSTGRES_DBNAME,
    ENV_POSTGRES_EVENT_TABLE,
    ENV_POSTGRES_FREE_STATUS,
    ENV_POSTGRES_HOST,
    ENV_POSTGRES_PASSWORD,
    ENV_POSTGRES_POLYGON_TABLE,
    ENV_POSTGRES_PORT,
    ENV_POSTGRES_SCHEMA,
    ENV_POSTGRES_SSLMODE,
    ENV_POSTGRES_USER,
    ENV_SIMULATION_FLIGHT_COUNT,
    ENV_UNUSED_EVENT_ID_MAX_ATTEMPTS,
    STATUS_BUSY,
    STATUS_FREE,
)


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def get_env_str(name: str, default: str) -> str:
    return os.getenv(name, default)


def get_env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def get_env_float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


def get_allowed_point_max_attempts() -> int:
    return get_env_int(
        ENV_ALLOWED_POINT_MAX_ATTEMPTS,
        DEFAULT_ALLOWED_POINT_MAX_ATTEMPTS,
    )


def get_api_key() -> str | None:
    return os.getenv(ENV_API_KEY)


def get_api_key_header_name() -> str:
    return get_env_str(
        ENV_API_KEY_HEADER_NAME,
        DEFAULT_API_KEY_HEADER_NAME,
    )


def get_api_login_password() -> str:
    return get_env_str(
        ENV_API_LOGIN_PASSWORD,
        DEFAULT_API_LOGIN_PASSWORD,
    )


def get_api_login_url() -> str:
    return get_env_str(
        ENV_API_LOGIN_URL,
        DEFAULT_API_LOGIN_URL,
    )


def get_api_login_username() -> str:
    return get_env_str(
        ENV_API_LOGIN_USERNAME,
        DEFAULT_API_LOGIN_USERNAME,
    )


def get_dispatch_timeout_seconds() -> float:
    return get_env_float(
        ENV_DISPATCH_TIMEOUT_SECONDS,
        DEFAULT_DISPATCH_TIMEOUT_SECONDS,
    )


def get_dispatch_url() -> str:
    return get_env_str(ENV_DISPATCH_URL, DEFAULT_DISPATCH_URL)


def get_json_output_indent() -> int:
    return get_env_int(ENV_JSON_OUTPUT_INDENT, DEFAULT_JSON_OUTPUT_INDENT)


def get_postgres_aircraft_table_name() -> str:
    return get_env_str(
        ENV_POSTGRES_AIRCRAFT_TABLE,
        DEFAULT_POSTGRES_AIRCRAFT_TABLE,
    )


def get_postgres_busy_status() -> str:
    return get_env_str(ENV_POSTGRES_BUSY_STATUS, STATUS_BUSY)


def get_postgres_connection_settings() -> dict[str, str | int | None]:
    return {
        "host": get_required_env(ENV_POSTGRES_HOST),
        "port": get_env_int(ENV_POSTGRES_PORT, DEFAULT_POSTGRES_PORT),
        "dbname": get_required_env(ENV_POSTGRES_DBNAME),
        "user": get_required_env(ENV_POSTGRES_USER),
        "password": get_required_env(ENV_POSTGRES_PASSWORD),
        "sslmode": os.getenv(ENV_POSTGRES_SSLMODE),
    }


def get_postgres_event_table_name() -> str:
    return get_env_str(ENV_POSTGRES_EVENT_TABLE, DEFAULT_POSTGRES_EVENT_TABLE)


def get_postgres_free_status() -> str:
    return get_env_str(ENV_POSTGRES_FREE_STATUS, STATUS_FREE)


def get_postgres_polygon_table_name() -> str:
    return get_env_str(
        ENV_POSTGRES_POLYGON_TABLE,
        DEFAULT_POSTGRES_POLYGON_TABLE,
    )


def get_postgres_schema_name() -> str:
    return get_env_str(ENV_POSTGRES_SCHEMA, DEFAULT_POSTGRES_SCHEMA)


def get_simulation_flight_count() -> int:
    return get_env_int(
        ENV_SIMULATION_FLIGHT_COUNT,
        DEFAULT_SIMULATION_FLIGHT_COUNT,
    )


def get_unused_event_id_max_attempts() -> int:
    return get_env_int(
        ENV_UNUSED_EVENT_ID_MAX_ATTEMPTS,
        DEFAULT_UNUSED_EVENT_ID_MAX_ATTEMPTS,
    )
