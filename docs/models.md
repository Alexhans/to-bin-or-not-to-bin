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
| Running your own server (llama.cpp, vLLM, LM Studio, or any OpenAI-compatible router) | `openai-chat:<model as your server names it>` | `BINDAY_BASE_URL=http://localhost:8081/v1`, plus `BINDAY_API_KEY` if it asks for one (defaults to `local`) |

[OpenRouter](https://openrouter.ai) is the one I'd suggest if you don't have anything yet.
You pay per call in one place, you can set a spending limit, and you can switch between
models from different companies by changing the string.
Each run's task log shows the tokens it used and an estimated cost, so you can work out what a
call costs you before you schedule it.

> [!NOTE]
> The subscription routes use your plan's usage limits, and running something on a
> schedule falls under each company's terms for that plan. Read them before you leave it
> running.

> [!NOTE]
> **A server you run yourself.** `openai:` asks for OpenAI's Responses API, which your own
> server almost certainly doesn't offer: use `openai-chat:` for the Chat Completions API it
> does speak. If you set `BINDAY_BASE_URL` together with `openai:`, the tutorial says so and
> names the string to use instead.
>
> Two things to expect when you run the model yourself: the cost column shows `-`, because
> there is no price list for a model you host (tokens and seconds are still measured), and
> Airflow's UI wants port 8080, a popular port for a model server. If something already
> answers there, `airflow-up` stops and tells you; run it with `AIRFLOW__API__PORT=8090` and
> open the UI on that port instead.