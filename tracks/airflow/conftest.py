"""Give the Airflow checks their own Airflow home and database, so nothing touches yours."""

import os
import subprocess
import sys
import tempfile

import pytest

from binday.llm import use_binday_model

os.environ["AIRFLOW_HOME"] = tempfile.mkdtemp(prefix="binday-airflow-")
os.environ["AIRFLOW__CORE__LOAD_EXAMPLES"] = "False"
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
use_binday_model()


@pytest.fixture(scope="session")
def airflow_db():
    """Create the test database once, before the first Dag run."""
    subprocess.run([sys.executable, "-m", "airflow", "db", "migrate"], check=True, capture_output=True)
