"""Start Airflow for the tutorial: `uv run --extra airflow airflow-up [chapter folder]`.

Everything Airflow writes goes in `.airflow/` at the repo root. The UI needs no login,
which is fine for a local tutorial and nowhere else.
"""

import os
import socket
import sys
from pathlib import Path

from binday.llm import use_binday_model

REPO = Path(__file__).resolve().parents[2]
CHAPTERS = REPO / "tracks/airflow"


def main() -> None:
    """Point Airflow at the tutorial's Dags and run `airflow standalone`."""
    env = os.environ
    env["AIRFLOW_HOME"] = str(REPO / ".airflow")
    chapter = sys.argv[1] if len(sys.argv) > 1 else "03-in-airflow"
    dags = CHAPTERS / chapter / "dags"
    if not dags.is_dir():
        sys.exit(f"No Dags in {dags}. Pass a chapter folder, for example: airflow-up 04-on-a-schedule")
    env["AIRFLOW__CORE__DAGS_FOLDER"] = str(dags)
    env["AIRFLOW__CORE__LOAD_EXAMPLES"] = "False"
    env.setdefault("PYDANTIC_AI_NO_BANNER", "1")
    if not use_binday_model() and chapter != "07-no-model":
        sys.exit("Set BINDAY_MODEL first, for example: export BINDAY_MODEL=bedrock:global.anthropic.claude-opus-5-5. See docs/models.md.")
    env["AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_ALL_ADMINS"] = "True"
    # No login, so only this machine may reach the UI.
    env["AIRFLOW__API__HOST"] = "127.0.0.1"
    # `airflow standalone` starts its other processes by running `airflow` from PATH.
    env["PATH"] = f"{Path(sys.executable).parent}{os.pathsep}{env['PATH']}"
    with socket.socket() as s:
        if s.connect_ex(("127.0.0.1", 8111)) != 0:
            sys.exit("Start the council first, in another terminal: uv run council")
    os.execvp("airflow", ["airflow", "standalone"])
