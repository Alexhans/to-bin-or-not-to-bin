<!-- nav:top -->
[Home](../../README.md) · [Contents](../../README.md#contents) · Previous: [1. Delegate to an agent with a skill](../01-do-it-for-me/README.md) · Next: [Pick your track](#pick-your-track)
<!-- /nav:top -->

# 2. Check the agent's answer automatically to enable fast iteration

*"Tell me the agent still works as intended without me having to verify it manually every time."*

So far, you've compared the agent's answer with the one you found by hand. This means that every time you 
change the solution, you'd have to manually compare again.

It's also tempting to start guessing what to change: the prompt, the tools, the model. 
More important than that is finding a way to check, after each change, that the solution still does 
what it did before. Programmers call that refactoring: changing how something works on 
the inside (code) without changing what it does from the outside (observable behaviour).  
Refactoring can be done safely when you can automatically check this using tests.

![A loop of change, run and check, with the things you might want to change: the prompt, the model, the tools, the workflow, the runtime](https://alexhans.github.io/talks/airflow-summit/2026/it-works-now-what/images/article/cheap-loop.png)

So the rule is: **"before you delegate, build a check that tells you whether something is right
or wrong."**

You can call that **executable intent**. 

In step 1 you wrote down an input and the outcome you expect from it. In general, that's:

```
f(address, date)  ->  next collection date and bins
```

`f` can be a prompt, a skill, a model or plain code; the input and the desired outcome stay
the same. A test runs `f` and compares what comes back with the desired outcome. That turns
"is it still right?" into a yes or no you get from one command, without reading the answer
yourself. It's also something you can give your coding agent: "change this, and keep going
until the tests pass, without changing them."

There's one catch. In real life, the council's website only answers for today, so every week
that passes the input is different, and you get a different, updated answer. If you tested
against the real website, you'd get the right answer for `f(address, today)`, but you couldn't
test `f(address, a date you know about)` against the answer you know. So I made the
tutorial's council able to show any date, which freezes the scenarios you test and lets the
tests keep passing as you change the workflow: add a date to the address, such as
`/w/2026-08-22/`, and the site answers as it would have on that day.

<details>
<summary>This is a mock server</summary>

The dated council stands in for a service you don't control, which is what a mock server
does: it answers like the real thing, but for the situation you choose. With a real website
you'd record its answers once and replay them, for example with
[mitmproxy](https://mitmproxy.org), or have your coding agent write a small fake like this
one. You don't need to do that here. From the talk: the slide
[Simulate the Effect](https://alexhans.github.io/talks/airflow-summit/2026/it-works-now-what/#/simulate-the-effect).

</details>

## Freeze a day you know

Keep the council's website running from step 1, and work from the repo folder,
`to-bin-or-not-to-bin`. If you're still in `sandbox`, run `cd ../../..` first.

Start by finding the answer for a frozen day, by hand, the same way you did in step 1. Open
<http://localhost:8111/w/2026-08-22/>, which is the site as it was on Saturday 22 August 2026,
and look up **2 Wibble Way, Ollie Woley** as before. You should see the blue recycling bin and
the food box on Thursday 27 August 2026. That's the answer the test will expect.

## Run the test

The test is already written, in [`test_bin_day.py`](test_bin_day.py). Run it:

```bash
uv run pytest steps/02-know-its-right -v
```

```
steps/02-know-its-right/test_bin_day.py::test_ordinary_week PASSED       [100%]
```

It takes about as long as asking the skill yourself, because the test asks the agent again and
compares its answer with the one you just found. The test is only a few lines:

```python
def test_ordinary_week(council):
    facts = ask_agent(f"{council}/w/2026-08-22/")
    assert facts == BinDayFacts(
        next_collection_date=dt.date(2026, 8, 27),
        containers_due={"BLUE RECYCLING WHEELIE BIN", "FOOD BOX"},
    )
```

`ask_agent` asks your skill from step 1 about a specific day: 2026-08-22. `assert facts == BinDayFacts(...)` checks 
that what the agent returned must equal the answer you found by hand; if they differ, the test
fails and shows the difference. [`pytest`](https://docs.pytest.org) is a popular testing library 
that works by running every function whose name starts with `test_`.  If it says `SKIPPED`, it couldn't find your
skill.  You can point your coding agent to it to learn more about it and why we pass the council information as a parameter.

<details>
<summary>If it fails with no bins at all</summary>

If the test fails with `containers_due=set()` and the date you asked about, your skill is
probably asking for an address rather than telling the agent where to get one. The agent has
nobody to ask: each run is a fresh one with only the skill and the question. Open
`steps/01-do-it-for-me/sandbox/.claude/skills/bin-day/SKILL.md` and check that the postcode and
address are in it, as the defaults to use when the question doesn't name an address. Add them if
they aren't, and run the test again.

</details>

<details>
<summary>What ask_agent does</summary>

```python
def ask_agent(site: str) -> BinDayFacts:
    """Ask the step 1 skill about one council site, and return its answer as facts."""
    done = subprocess.run(
        [
            "claude", "-p",
            f"Use the bin-day skill, with the council site at {site} instead of http://localhost:8111 "
            f"(for every URL, including the API endpoints). Do I need to put the bins out?",
            "--allowedTools", "Bash(curl:*)", "Skill",
            "--json-schema", json.dumps(BinDayFacts.model_json_schema()),
            "--output-format", "json",
        ],
        cwd=SANDBOX, capture_output=True, text=True, check=True,
    )
    return BinDayFacts.model_validate(json.loads(done.stdout)["structured_output"])
```

It runs `claude -p` from step 1's `sandbox`, with `--json-schema`, which makes the agent answer
as data in the shape of `BinDayFacts` instead of as prose. `BinDayFacts`, in
[`src/binday/facts.py`](../../src/binday/facts.py), is a date and a set of container names, so
the order of the bins doesn't matter. The test also starts its own copy of the council's
website on a free port, so yours can keep running.

</details>

A test like this is often called an [AI eval](https://ai-evals.io/). It's an assertion over the result of LLM inference (what the agent returned).  Note that we're using a deterministic assertion, not LLMaaJ (LLM as a Judge).

## Break it on purpose

A test you've only seen pass doesn't tell you much yet, so make it fail to confirm it can (Sometimes known as red-green refactor). In `test_bin_day.py`, change the expected date, `dt.date(2026, 8, 27)`, to `dt.date(2026, 8, 28)`, 
and run the test again. It fails and shows where the two answers differ:

```
E         - BinDayFacts(next_collection_date=datetime.date(2026, 8, 28), containers_due={'BLUE RECYCLING WHEELIE BIN', 'FOOD BOX'})
E         ?                                                          ^
E         + BinDayFacts(next_collection_date=datetime.date(2026, 8, 27), containers_due={'BLUE RECYCLING WHEELIE BIN', 'FOOD BOX'})
```

The `-` line is what the test expected, the `+` line is what the agent answered, and `^` points
at the character that differs. Change the date back before you go on.

## Add a harder day

Ordinary weeks are the easy case. Collections move around holidays, so check a week like that
too. Open <http://localhost:8111/w/2026-12-27/> and look up the same address: New Year's Day
moves the Thursday collection to Saturday 2 January 2027. 

Create a second test to cover that and run both:

```bash
cat >> steps/02-know-its-right/test_bin_day.py <<'EOF'


def test_new_years_week(council):
    facts = ask_agent(f"{council}/w/2026-12-27/")
    assert facts == BinDayFacts(
        next_collection_date=dt.date(2027, 1, 2),
        containers_due={"BLUE RECYCLING WHEELIE BIN", "FOOD BOX"},
    )
EOF
uv run pytest steps/02-know-its-right -v
```

```
steps/02-know-its-right/test_bin_day.py::test_ordinary_week PASSED       [ 50%]
steps/02-know-its-right/test_bin_day.py::test_new_years_week PASSED      [100%]
```

<details>
<summary>What the <code>cat &gt;&gt; … &lt;&lt;'EOF'</code> block does</summary>

It adds everything up to the line `EOF` to the end of `test_bin_day.py`, then runs the tests.
Run it once: running it again adds a second copy of the test.

</details>

This is the kind of case you probably wouldn't think of when you first build a workflow, and
would discover while running it. You might not have known beforehand that New Year's Day moves the
collection, and you don't really need to. As long as the job reads the date the council publishes,
instead of assuming "it's every Thursday", a workflow will get the right answer.

From the talk: the slide [The Smallest Check](https://alexhans.github.io/talks/airflow-summit/2026/it-works-now-what/#/the-smallest-check), and the [video and transcript](https://alexhans.github.io/posts/talk.it-works-now-what.html).

## Pick your track

From here on, you choose how to schedule the job. Both tracks go from running it on a schedule to
running it without a model (no inference).

- **[Airflow](../../tracks/airflow/03-in-airflow/README.md)**, if you use [Apache Airflow](https://airflow.apache.org)
  or want to see how an agent fits into it. The agent runs inside a Dag (Airflow's word for
  a workflow), and Airflow decides when it runs and what it may touch. Your code calls the
  model directly instead of going through Claude Code, so you'll need an API key for a
  model; [Choosing a model](../../docs/models.md) lists the options, including free ones.
- **[Coding agent](../../tracks/agent/03-on-a-schedule/README.md)**, if you'd rather stay with Claude Code. A
  short Python command runs the agent every evening with `cron`, and you don't need to install
  anything else.

---

<!-- nav:bottom -->
[Home](../../README.md) · [Contents](../../README.md#contents) · Previous: [1. Delegate to an agent with a skill](../01-do-it-for-me/README.md) · Next: [Pick your track](#pick-your-track)
<!-- /nav:bottom -->
