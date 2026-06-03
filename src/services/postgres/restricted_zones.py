import json
from typing import Any


def fetch_restricted_zone_rows(connection: Any) -> list[dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT name, geojson, zone, state_duration
            FROM polygons
            """
        )
        rows = cursor.fetchall()
        column_names = [column[0] for column in cursor.description]

    return [
        _normalize_polygon_row(dict(zip(column_names, row, strict=False)))
        for row in rows
    ]


def _normalize_polygon_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized_row = dict(row)
    geojson_value = normalized_row.get("geojson")

    if isinstance(geojson_value, str):
        normalized_row["geojson"] = json.loads(geojson_value)

    return normalized_row
