"""Run a chapter's agent checks with several Claude models, side by side, and summarise.

    uv run python tracks/agent/04-cheaper-model/compare.py haiku sonnet opus
    uv run python tracks/agent/04-cheaper-model/compare.py haiku sonnet --runs 1 --chapter 05-less-inference

Each model gets its runs one after another, and the models run at the same time. Every run's
results are kept in results/, so a failure can be read afterwards without running it again.
"""

from binday.compare import main

if __name__ == "__main__":
    main(__file__, "BINDAY_CLAUDE_MODEL", "haiku sonnet opus", "03-on-a-schedule")
