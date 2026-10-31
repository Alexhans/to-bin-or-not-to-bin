"""Run a chapter's agent checks with several models, side by side, and summarise.

    uv run --extra airflow python tracks/airflow/05-cheaper-model/compare.py MODEL [MODEL ...]
    uv run --extra airflow python tracks/airflow/05-cheaper-model/compare.py MODEL --runs 1 --chapter 06-less-inference

Each model is a BINDAY_MODEL value. Each model gets its runs one after another, and the models
run at the same time. Every run's results are kept in results/, so a failure can be read
afterwards without running it again.
"""

from binday.compare import main

if __name__ == "__main__":
    main(__file__, "BINDAY_MODEL", "bedrock:global.anthropic.claude-haiku-4-5-20251001-v1:0 openrouter:openai/gpt-oss-20b", "04-on-a-schedule")
