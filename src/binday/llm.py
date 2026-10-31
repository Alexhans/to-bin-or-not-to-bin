"""Turn BINDAY_MODEL into the Airflow connection the Dags ask the model through."""

import json
import os

CONN_ID = "binday_llm"


def connection(model: str) -> str:
    """Return the connection for a Pydantic AI model string, as Airflow reads it from the environment."""
    if model.startswith("bedrock:"):
        region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"
        return json.dumps({"conn_type": "pydanticai_bedrock", "extra": {"model": model, "region_name": region}})
    # Other providers read their API key from their usual variable, for example OPENROUTER_API_KEY.
    return json.dumps({"conn_type": "pydanticai", "extra": {"model": model}})


def use_binday_model() -> bool:
    """Define the binday_llm connection from BINDAY_MODEL, unless it's already defined."""
    model = os.environ.get("BINDAY_MODEL")
    if model:
        os.environ.setdefault(f"AIRFLOW_CONN_{CONN_ID.upper()}", connection(model))
    return bool(model)
