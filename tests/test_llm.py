"""Checks for how BINDAY_MODEL becomes the Airflow connection. No model needed."""

import json

from binday.llm import connection


def test_other_providers_read_their_key_from_their_usual_variable(monkeypatch):
    monkeypatch.delenv("BINDAY_BASE_URL", raising=False)
    assert json.loads(connection("openrouter:openai/gpt-oss-20b")) == {
        "conn_type": "pydanticai", "extra": {"model": "openrouter:openai/gpt-oss-20b"}}


def test_bedrock_carries_the_region(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "eu-west-2")
    conn = json.loads(connection("bedrock:global.anthropic.claude-haiku-5-5"))
    assert conn["conn_type"] == "pydanticai_bedrock"
    assert conn["extra"]["region_name"] == "eu-west-2"


def test_a_server_you_run_yourself_gets_its_address_and_a_key(monkeypatch):
    monkeypatch.setenv("BINDAY_BASE_URL", "http://localhost:8081/v1")
    monkeypatch.delenv("BINDAY_API_KEY", raising=False)
    conn = json.loads(connection("openai-chat:qwen3.8-flash-next-strata"))
    assert conn["host"] == "http://localhost:8081/v1"
    assert conn["password"] == "local"  # most local servers accept any key
    assert conn["extra"]["model"] == "openai-chat:qwen3.8-flash-next-strata"


def test_a_key_for_a_local_server_can_be_given(monkeypatch):
    monkeypatch.setenv("BINDAY_BASE_URL", "http://localhost:8081/v1")
    monkeypatch.setenv("BINDAY_API_KEY", "secret")
    assert json.loads(connection("openai-chat:gpt-oss:20b"))["password"] == "secret"
