from typing import Any

from src.services.postgres.connection import resolve_postgres_relation_name


def select_random_free_aircraft_id(
    connection: Any,
    free_status: str = "FREE",
    busy_status: str = "BUSY",
) -> str:
    aircraft_table = resolve_postgres_relation_name(
        default_table_name="aircraft",
        table_env_var_name="FLIGHT_GENERATOR_POSTGRES_AIRCRAFT_TABLE",
    )

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            WITH selected_aircraft AS (
                SELECT id
                FROM {aircraft_table}
                WHERE status = %s
                ORDER BY RANDOM()
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            UPDATE {aircraft_table}
            SET
                status = %s,
                update_date = CURRENT_TIMESTAMP
            WHERE id IN (SELECT id FROM selected_aircraft)
            RETURNING id
            """,
            (free_status, busy_status),
        )
        row = cursor.fetchone()

    if row is None:
        raise RuntimeError("No aircraft with status FREE was found")

    return str(row[0])
