"""Turn BINDAY_MODEL into the Airflow connection the Dags ask the model through."""

import json
import os
import sys

CONN_ID = "binday_llm"


def connection(model: str) -> str:
    """Return the connection for a Pydantic AI model string, as Airflow reads it from the environment."""
    if model.startswith("bedrock:"):
        region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"
        return json.dumps({"conn_type": "pydanticai_bedrock", "extra": {"model": model, "region_name": region}})
    conn = {"conn_type": "pydanticai", "extra": {"model": model}}
    # A server you run yourself (llama.cpp, Ollama, vLLM, LM Studio) speaks the OpenAI API at its own
    # address, which the connection holds as its host. Most take any key, so BINDAY_API_KEY defaults to one.
    if base := os.environ.get("BINDAY_BASE_URL"):
        conn["host"] = base
        conn["password"] = os.environ.get("BINDAY_API_KEY", "local")
    return json.dumps(conn)


def use_binday_model() -> bool:
    """Define the binday_llm connection from BINDAY_MODEL, unless it's already defined."""
    model = os.environ.get("BINDAY_MODEL")
    if model:
        os.environ.setdefault(f"AIRFLOW_CONN_{CONN_ID.upper()}", connection(model))
        if os.environ.get("BINDAY_BASE_URL") and model.startswith("openai:"):
            # `openai:` asks for OpenAI's Responses API, which servers you run yourself don't offer.
            print(f"BINDAY_BASE_URL is set, but {model} uses OpenAI's Responses API. A server you run "
                  f"yourself usually wants openai-chat:{model.split(':', 1)[1]}", file=sys.stderr)
    return bool(model)
