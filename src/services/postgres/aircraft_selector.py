from typing import Any


def select_random_free_aircraft_id(
    connection: Any, free_status: str = "FREE"
) -> int:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id
            FROM aircraft
            WHERE status = %s
            ORDER BY RANDOM()
            LIMIT 1
            """,
            (free_status,),
        )
        row = cursor.fetchone()

    if row is None:
        raise RuntimeError("No aircraft with status FREE was found")

    return row[0]
