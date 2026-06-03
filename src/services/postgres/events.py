import random
from typing import Any


def generate_unique_event_id(
    connection: Any,
    min_value: int = 1,
    max_value: int = 2_147_483_647,
    max_attempts: int = 1_000,
) -> int:
    for _ in range(max_attempts):
        candidate = random.randint(min_value, max_value)
        if not _event_id_exists(connection, candidate):
            return candidate

    raise RuntimeError(
        "Failed to generate a unique event id that is not present in the event table"
    )


def _event_id_exists(connection: Any, event_id: int) -> bool:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM event WHERE id = %s LIMIT 1", (event_id,))
        return cursor.fetchone() is not None
