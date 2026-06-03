import sys
from pathlib import Path

sys.dont_write_bytecode = True

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.env_loader import load_project_env
from src.features.simulator.simulator_runner import run_simulator


def main() -> None:
    load_project_env()
    run_simulator()


if __name__ == "__main__":
    main()
