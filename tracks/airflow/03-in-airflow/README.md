<!-- nav:top -->
[Home](../../../README.md) · [Contents](../../../README.md#contents) · Airflow track · Previous: [2. Check the agent's answer automatically to enable fast iteration](../../../steps/02-know-its-right/README.md) · Next: [4. Get timely alerts without running it yourself](../04-on-a-schedule/README.md)
<!-- /nav:top -->

# 3. Run the skill in Airflow

At the end of step 2, your skill gives the right answer and you have checks that prove it, but
it only runs when you trigger the agent skill, in other words, the agent only acts when you ask it to. 
This means you need to remmember to ask, which was the original problem. 

To have it run by itself every evening, this track uses
[Airflow](https://airflow.apache.org), which runs work on a schedule and keeps a record of every
run.

## Airflow in a few lines

If you already use Airflow, skip to [Start Airflow](#start-airflow).

In Airflow, you describe the work in a *Dag*, a Python file that says which steps to run, in
what order and when. Each step is a *task*. An *operator* is a ready-made kind of task, and
this chapter uses one called `AgentOperator`, which runs an agent. Airflow keeps credentials in
*connections*, each with a name, so the Dag refers to the model by the name `binday_llm` and
never holds your keys.

Every run of a Dag is for a particular day, called its *logical date*. A run that the schedule
starts at 7pm on 26 August has the logical date 26 August, and when you start a run by hand, you
can choose its logical date. The Dag can use that date, written `{{ ds }}`, and this one uses it
to read the council's website as it was on that day. That's also how a check can run the Dag
for a day whose answer you already know. Airflow's
[core concepts](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/index.html)
explain all of this in more depth.

## Start Airflow

From here on you'll use three terminals, all in the repo folder, `to-bin-or-not-to-bin`:

1. **Council:** the one from step 1, still running `uv run council`. If you stopped it, start it
   again there.
2. **Airflow:** a new one, where Airflow will run.
3. **Checks:** another new one, for the checks and any other commands.

In the Airflow terminal, install Airflow and the Common AI provider:

```bash
uv sync --extra airflow
```

The Dag asks a model through your own account with a model provider, and `BINDAY_MODEL` says
which one. I used Claude Opus on Amazon Bedrock, with my AWS credentials. Set it in both the
Airflow terminal and the checks terminal, because `export` only lasts in the terminal you run
it in:

```bash
export BINDAY_MODEL=bedrock:global.anthropic.claude-opus-5-5
```

You can use any provider instead, with a different value. If you don't have one,
[OpenRouter](https://openrouter.ai) lets you pay per call for models from several companies
with one key, for example `BINDAY_MODEL=openrouter:openai/gpt-oss-20b` with your
`OPENROUTER_API_KEY` set in the same two terminals. If you already pay for ChatGPT, or would
rather run a model on your own machine, [Choosing a model](../../../docs/models.md) has the
setting for those too.

Then, in the Airflow terminal, start Airflow:

```bash
uv run --extra airflow airflow-up
```

`airflow-up` runs [`airflow standalone`](https://airflow.apache.org/docs/apache-airflow/stable/start.html),
which starts all of Airflow in this one terminal.

Once you see the terminal stops scrolling, Airflow should be up and running and you can open it on <http://localhost:8080>.
You should see our `bin_day` dag in the list of dags.

<details>
<summary>What <code>airflow-up</code> sets up</summary>

It keeps everything Airflow writes in `.airflow/` in the repo, loads this chapter's `dags`
folder, and makes the `binday_llm` connection from `BINDAY_MODEL`. It also runs Airflow without
a login, and in that case it only accepts connections from your own machine.

</details>

## The Dag

[`dags/bin_day.py`](dags/bin_day.py) has two tasks:

```
ask_the_agent  →  tell_me
```

`ask_the_agent` runs the same skill file you saved with Claude Code in step 1,
`steps/01-do-it-for-me/sandbox/.claude/skills/bin-day/SKILL.md`, unchanged, with the
[Common AI provider](https://airflow.apache.org/docs/apache-airflow-providers-common-ai/stable/index.html)'s
`AgentOperator` instead of Claude Code. It asks the question you asked in step 1, and the
answer comes back as the next collection date and the bins due, the same shape step 2's checks
compare. `tell_me` then prints that answer. The Dag looks something like this:

```python
@dag(schedule=None)
def bin_day():
    ask_the_agent = AgentOperator(
        task_id="ask_the_agent",
        llm_conn_id="binday_llm",
        prompt="Use the bin-day skill, with the council's website at the path /w/{{ ds }}/ ... "
               "Which bins do I put out next, and when?",
        output_type=BinDayFacts,
        toolsets=[
            AgentSkillsToolset(sources=[str(SKILLS)], exclude_tools={"run_skill_script"}),
            FunctionToolset([get, post], id="council"),
        ],
        usage_limits={"request_limit": 15},
    )

    @task
    def tell_me(answer: dict) -> str:
        message = describe(BinDayFacts.model_validate(answer))
        print(message)
        return message

    tell_me(ask_the_agent.output)
```

`schedule=None` means it only runs when you start it. In Claude Code, the agent used `curl`; here
it has no shell, so the prompt tells it to use two tools, `get` and `post`, which can only reach
the council's website.

<details>
<summary>What the tools do, and don't do</summary>

`AgentSkillsToolset` lets the agent load your `SKILL.md`. `FunctionToolset` gives it `get` and
`post`, two plain functions that only reach the council's website. Those are the only things
it can do, which is a tighter box than the `curl` it had in Claude Code, and `usage_limits`
stops a run that asks the model more than 15 times. If something must never happen, though,
prevent it with controls the agent can't change, such as a user without access, read-only
credentials or a sandbox. Checks tell you whether it did the right thing; they aren't
security.

![Two kinds of control: can it do this at all, and did it do the right thing](https://alexhans.github.io/talks/airflow-summit/2026/it-works-now-what/images/article/control.png)

From the talk: the slide [Two Kinds of Control](https://alexhans.github.io/talks/airflow-summit/2026/it-works-now-what/#/two-kinds-of-control).

</details>

<details>
<summary>The Common AI provider, from 0.7.0 to 1.0</summary>

When I gave the talk, the provider was at 0.7.0, released on 6 August 2026, and the Dag on my
slides read the skill into Pydantic AI by hand, with a footnote pointing to `AgentOperator` and
`AgentSkillsToolset`. Version 1.0.0 came out on 18 October 2026, after 0.8, 0.9 and 0.10, and
moved the provider out of incubation. Two things this chapter uses are new since 0.7.0: the
estimated cost in the task's log, and `usage_limits` counting every retry of a task together.
It also gained cost limits per run, a Model tab on the task page, approval of an agent's tool
calls by a person, durable runs that don't repeat finished steps on a retry,
sandboxes, and support for Airflow 2.11. The
[changelog](https://airflow.apache.org/docs/apache-airflow-providers-common-ai/stable/changelog.html)
has the rest.

Thank you to everyone who has contributed to the provider, from its start in February 2026 to
1.0: Aaron Chen, Amogh Desai, André Ahlert, Andrew Chang, Ash Berlin-Taylor, Baha Bouali,
Colten, Dev-iL, Ehab Abdalla, Elad Kalif, Gökhan Çetin, GPK, Guan-Ming Chiu, HARSHITH GANDHE,
Henry Chen, Hussein Awala, Jarek Potiuk, Jason (Zhe-You) Liu, Jed Cunningham, Jeff (Wei-Hao)
Lu, Jens Scheffler, Joseph Perla, Jyun-An Chen, Kaxil Naik, Pankaj Koti, Pankaj Singh, Pierre
Jeambrun, PoAn Yang, Shahar Epstein, Simar Rekhi, Siva Varma, Sruthi, Stefan Wang, Vikram Koka,
Vincent, Wei Lee, Yash jain, Yossi Eliaz, Yuseok Jo and Zach Liu.

</details>

## Run it

Start a run for Saturday 22 August 2026, the ordinary week you looked up in step 2:

1. In the Airflow UI, click `bin_day` and press **Trigger**.
2. Set **Logical Date** to 22 August 2026, and press **Trigger**.
3. Open the **Runs** tab and click the run. When both tasks show **Success**, click
   `ask_the_agent`. Its **Logs** tab shows each tool call, then what the run took, something
   like this:

   ```
   Tool call: load_skill
   Tool call: post
   Tool call: post
   LLM run complete: model=global.anthropic.claude-opus-5-5, requests=4, tool_calls=3, input_tokens=13149, output_tokens=300, total_tokens=13449
   LLM run cost: $0.0086678 (USD, best-effort)
   ```

   Click a line that starts with ▶ to open it. The **Rendered Templates** tab shows the prompt
   with the date filled in.
4. Go back to the run and click `tell_me`. Its log shows the answer:

   ```
   Next collection: Thursday 27 August 2026, blue recycling wheelie bin and food box.
   ```

That's the answer you found by hand in step 2. The form also unpaused the Dag, which changes
nothing yet, since it has no schedule.

![The bin Dag in the Airflow UI, with task runs and logs](https://alexhans.github.io/talks/airflow-summit/2026/it-works-now-what/images/article/airflow-ui.png)

## Check it

In step 2 you checked the skill's answer for two days whose answers you knew. You can now run those checks,
in [`test_in_airflow.py`](test_in_airflow.py), which run the dag and compare what 
`ask_the_agent` returns. 

One cool thing is that they don't really need for your Airflow instance to be up. 
Airflow's [dag.test()](https://airflow.apache.org/docs/apache-airflow/2.5.3/core-concepts/executor/debug.html) runs a dag in a single python process.

The test looks like this:

```python
def test_the_step_2_checks_still_pass(council, monkeypatch, name):
    monkeypatch.setenv("BIN_SERVICE_URL", council)
    today, expected = KNOWN_DAYS[name]
    got = dagtest.run(bin_day.bin_day_dag, today)["ask_the_agent"]
    assert BinDayFacts.model_validate(got) == expected
```

`KNOWN_DAYS` holds the two days from step 2 with the answers you found by hand, and
[`dagtest.run`](../../../src/binday/dagtest.py) runs the Dag for a day and returns what each task
returned. In the checks terminal, run both checks side by side with `-n 2`:

```bash
uv run --extra airflow pytest tracks/airflow/03-in-airflow -n 2 -v
```

If a check says `SKIPPED`, the line at the end says why, for example that `BINDAY_MODEL` isn't
set in this terminal. Otherwise you'll see something like this:

```
[gw0] [ 50%] PASSED tracks/airflow/03-in-airflow/test_in_airflow.py::test_the_step_2_checks_still_pass[ordinary week]
[gw1] [100%] PASSED tracks/airflow/03-in-airflow/test_in_airflow.py::test_the_step_2_checks_still_pass[new year's week]
2 passed in 22.26s
```

<details>
<summary>Where the checks' Airflow lives</summary>

[`tracks/airflow/conftest.py`](../conftest.py) gives the checks their own Airflow home and
database in a temporary folder, so they never touch `.airflow/` or an Airflow you already have,
and it makes the `binday_llm` connection from `BINDAY_MODEL`, as `airflow-up` does. Each check
also starts its own copy of the council's website on a free port.

</details>

## What's next

The skill now runs in Airflow, and the checks from step 2 still pass (meaning your agent still does what you intended), but it only runs when you trigger it. In the next chapter you actaully put it on a schedule, so it runs every evening and alerts you when "the bins go out tomorrow".

From the talk: the slide [From Agent Skill to Airflow Dag](https://alexhans.github.io/talks/airflow-summit/2026/it-works-now-what/#/from-agent-skill-to-airflow-dag), and the [video and transcript](https://alexhans.github.io/posts/talk.it-works-now-what.html).

---

<!-- nav:bottom -->
[Home](../../../README.md) · [Contents](../../../README.md#contents) · Airflow track · Previous: [2. Check the agent's answer automatically to enable fast iteration](../../../steps/02-know-its-right/README.md) · Next: [4. Get timely alerts without running it yourself](../04-on-a-schedule/README.md)
<!-- /nav:bottom -->
