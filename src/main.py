import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.env_loader import load_project_env
from src.features.simulator.simulator_runner import run_simulator


def main() -> dict[str, object] | list[dict[str, object]]:
    load_project_env()
    simulation_output = run_simulator()
    print(json.dumps(simulation_output))
    return simulation_output


if __name__ == "__main__":
    main()
