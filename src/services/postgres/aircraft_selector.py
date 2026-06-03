from typing import Any


def select_random_free_aircraft_id(
    connection: Any,
    free_status: str = "FREE",
    busy_status: str = "BUSY",
) -> str:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            WITH selected_aircraft AS (
                SELECT id
                FROM aircraft
                WHERE status = %s
                ORDER BY RANDOM()
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            UPDATE aircraft
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
