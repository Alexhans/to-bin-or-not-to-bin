[Home](../README.md) · [Airflow track](../tracks/airflow/03-in-airflow/README.md)

# Choosing a model

The Airflow track calls a model from a Dag, with the
[Common AI provider](https://airflow.apache.org/docs/apache-airflow-providers-common-ai/stable/index.html),
which uses [Pydantic AI](https://ai.pydantic.dev/). You pick the model with one setting,
`BINDAY_MODEL`, which is a Pydantic AI model string: the part
before the colon says who you're paying, and the rest names the model. If you already
have an API key you use, set that and go back to the chapter.

If you don't, here's what I'd pick depending on your situation.

| If you're… | Set | And |
|---|---|---|
| At a company that gives you an API | `bedrock:<model id>`, `openai:<model>` or `anthropic:<model>` | The usual credentials: AWS credentials and `AWS_REGION`, `OPENAI_API_KEY`, or `ANTHROPIC_API_KEY` |
| At home, happy to pay per call | `openrouter:openai/gpt-oss-20b` | `OPENROUTER_API_KEY` |
| Already paying for ChatGPT | `openai-codex:<model>` | Log in once with `codex login` |
| Already paying for GitHub Copilot | `github-copilot:<model>` | Your Copilot login (untested) |
| Already paying for Claude | No direct route from code | Use OpenRouter, or follow the coding agent track, which runs on your Claude Code login |
| Offline, or don't want to pay | `ollama:gpt-oss:20b` | [Ollama](https://ollama.com) running locally (untested) |

[OpenRouter](https://openrouter.ai) is the one I'd suggest if you don't have anything yet.
You pay per call in one place, you can set a spending limit, and you can switch between
models from different companies by changing the string.
Each run's task log shows the tokens it used and an estimated cost, so you can work out what a
call costs you before you schedule it.

> [!NOTE]
> The subscription routes use your plan's usage limits, and running something on a
> schedule falls under each company's terms for that plan. Read them before you leave it
> running.