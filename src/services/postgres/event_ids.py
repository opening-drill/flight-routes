import uuid
from typing import Any


def generate_unused_event_id(
    connection: Any,
    max_attempts: int = 1_000,
) -> str:
    for _ in range(max_attempts):
        candidate = uuid.uuid4()
        if not _event_id_exists(connection, candidate):
            return str(candidate)

    raise RuntimeError(
        "Failed to generate a unique event id that is not present in the event table"
    )


def _event_id_exists(connection: Any, event_id: uuid.UUID) -> bool:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM event WHERE id = %s LIMIT 1", (event_id,))
        return cursor.fetchone() is not None
