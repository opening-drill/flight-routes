import json
from pathlib import Path
from typing import Any


def load_combined_region_geojson() -> dict[str, Any]:
    region_path = Path(__file__).with_name("israel_gaza_west_bank.geojson")

    with region_path.open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)
