import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_json_output_indent
from src.env_loader import load_project_env
from src.features.user_simulator.simulator_runner import run_simulator
from src.services.api import dispatch_simulation_payloads
from src.utils import configure_runtime

configure_runtime(__file__, 1)


def main() -> dict[str, object] | list[dict[str, object]]:
    load_project_env()
    simulation_output = run_simulator()
    output_indent = get_json_output_indent()
    print(json.dumps(simulation_output, indent=output_indent))
    
    """
    dispatch_response = dispatch_simulation_payloads(simulation_output)
    print(json.dumps(dispatch_response, indent=output_indent))
    """
    
    return simulation_output


if __name__ == "__main__":
    main()
