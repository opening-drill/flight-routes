import os
from typing import Any


def open_postgres_connection(
    host: str,
    port: int,
    dbname: str,
    user: str,
    password: str,
    sslmode: str | None = None,
):
    psycopg_module = _load_postgres_driver()
    connect_kwargs: dict[str, Any] = {
        "host": host,
        "port": port,
        "dbname": dbname,
        "user": user,
        "password": password,
    }

    if sslmode:
        connect_kwargs["sslmode"] = sslmode

    return psycopg_module.connect(**connect_kwargs)


def open_postgres_connection_from_env():
    host = os.getenv("FLIGHT_GENERATOR_POSTGRES_HOST")
    port = int(os.getenv("FLIGHT_GENERATOR_POSTGRES_PORT", "5432"))
    dbname = os.getenv("FLIGHT_GENERATOR_POSTGRES_DBNAME")
    user = os.getenv("FLIGHT_GENERATOR_POSTGRES_USER")
    password = os.getenv("FLIGHT_GENERATOR_POSTGRES_PASSWORD")
    sslmode = os.getenv("FLIGHT_GENERATOR_POSTGRES_SSLMODE")

    missing_vars = [
        env_var_name
        for env_var_name, value in (
            ("FLIGHT_GENERATOR_POSTGRES_HOST", host),
            ("FLIGHT_GENERATOR_POSTGRES_DBNAME", dbname),
            ("FLIGHT_GENERATOR_POSTGRES_USER", user),
            ("FLIGHT_GENERATOR_POSTGRES_PASSWORD", password),
        )
        if not value
    ]
    if missing_vars:
        raise ValueError(
            "Missing required PostgreSQL environment variables: "
            + ", ".join(missing_vars)
        )

    return open_postgres_connection(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
        sslmode=sslmode,
    )


def close_postgres_connection(connection: Any) -> None:
    connection.close()


def commit_postgres_transaction(connection: Any) -> None:
    connection.commit()


def rollback_postgres_transaction(connection: Any) -> None:
    connection.rollback()


def resolve_postgres_relation_name(
    default_table_name: str,
    table_env_var_name: str,
) -> str:
    schema_name = os.getenv("FLIGHT_GENERATOR_POSTGRES_SCHEMA", "public")
    table_name = os.getenv(table_env_var_name, default_table_name)
    return (
        f"{_quote_postgres_identifier(schema_name)}."
        f"{_quote_postgres_identifier(table_name)}"
    )


def _quote_postgres_identifier(identifier: str) -> str:
    escaped_identifier = identifier.replace('"', '""')
    return f'"{escaped_identifier}"'


def _load_postgres_driver():
    try:
        import psycopg

        return psycopg
    except ModuleNotFoundError:
        try:
            import psycopg2

            return psycopg2
        except ModuleNotFoundError as error:
            raise ModuleNotFoundError(
                "A PostgreSQL driver is required. Install `psycopg` or `psycopg2`."
            ) from error
