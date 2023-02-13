import os
from pathlib import Path

prefix = f"TSP-{os.getenv('AgencyName')}"
project_root_dir = Path(__file__).parent.absolute() / "../../../.."
