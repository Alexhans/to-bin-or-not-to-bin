<!-- nav:top -->
[Home](../../../README.md) · [Contents](../../../README.md#contents) · Airflow track · Previous: [5. Reduce cost while still getting the right answer](../05-cheaper-model/README.md) · Next: [7. Replace the agent with plain code](../07-no-model/README.md)
<!-- /nav:top -->

# 6. Move the decision from the model into code

*"Give the model only what needs a model."*

So far the agent does two jobs: it reads the next collection date off the council's website,
and it works out whether that date is tomorrow, which is what decides if you get an alert
tonight. The second job is a date comparison, which plain code does the same way every time.
Chapter 5 showed models getting it wrong, telling me to put the bins out two nights early. So
in this chapter the agent only returns the date and the bins, and a Python function compares
that date with the day of the run.

This chapter is mostly to read. Running it is optional.

## What changed

Before, the agent was asked the whole question, and `tell_me` trusted its decision:

```python
prompt="... Today is {{ logical_date.strftime('%A %-d %B %Y') }}. Do I need to put the bins out tonight?",
output_type=BinDayAlert,

if not answer.put_out_tonight:
    return f"Alert: none tonight. {answer.message}"
```

Now it's asked only for the date and the bins, and `decide` in
[`dags/bin_day.py`](dags/bin_day.py) compares that date with the day of the run, which `tell_me`
gets as `{{ ds }}`:

```python
prompt="... Today is {{ logical_date.strftime('%A %-d %B %Y') }}. Which bins go out next, and when?",
output_type=BinDayFacts,


def decide(facts: BinDayFacts, today: dt.date) -> str | None:
    """Return tonight's message, or None if the next collection isn't tomorrow."""
    if facts.next_collection_date != today + dt.timedelta(days=1):
        return None
    bins = " and ".join(sorted(b.lower() for b in facts.containers_due))
    return f"Put out the {bins} tonight, for {facts.next_collection_date:%A %-d %B}."
```

Because `decide` is plain code, it gets fast checks of its own, in
[`test_less_inference.py`](test_less_inference.py), which run in milliseconds without a model:

```python
def test_decides_tonight_across_the_new_year():
    assert bin_day.decide(DUE_2_JAN, dt.date(2027, 1, 1)) is not None
```

## What it saves

It doesn't save many tokens, because the agent still reads the skill and calls the website, so a
run reads about as much as before. What it saves is the models you can use. Run chapter 5's
comparison again on this chapter, with the same models:

```bash
uv run --extra airflow python tracks/airflow/05-cheaper-model/compare.py --chapter 06-less-inference <your models>
```

You could get something like this:

```
model                           runs passing   tokens read   tokens written   seconds   cost per run
claude-opus-5-5                          3/3        13,203              300      30.6        $0.0087
claude-sonnet-5-5                        3/3        13,203              300      27.6        $0.0043
claude-haiku-5-5                         3/3        13,203              492      28.9        $0.0004
claude-haiku-4-5                         3/3        11,181              271      24.7        $0.0125
gpt-oss-120b                             3/3        10,020              840      28.1        $0.0020
gpt-oss-20b                              1/3         7,896              930      27.0        $0.0008
mistral-large-3-675b-instruct            1/3         8,302              238      24.4        $0.0046
```

Three of these seven passed every run in chapter 5. Now five do: Haiku 4.5 went from failing the
25 August check every time to passing everything, and gpt-oss-120b, an open-weight model, went
from two runs out of three to all three. Comparing the collection date with today was the part
they got wrong, and it's no longer theirs to get wrong. The two that still fail do so for other
reasons, with Dag runs that failed outright or a fact read wrong.

So the cheapest run doesn't get cheaper, since Haiku 5.5 was already passing at about $0.0004.
What you get is a wider field to choose from, including open-weight models you could run on your
own machine, and one less thing a model can get wrong.

<details>
<summary>A check caught this chapter's first version</summary>

When I first wrote this chapter, the new prompt asked only "Which bins go out next, and when?"
and no longer said what day it was, because the code works that out now. The two checks from
chapter 3 failed: asked about the 22 August world, the agent answered with a collection in
November. Without a date in the prompt, it used the real date it knew instead of the day the run
was for. So the prompt still says "Today is ...", and only the decision moved into code. The
change I made to save a model some work had quietly broken the answer, and a check I already had
told me within seconds.

</details>

To see the full difference between the two versions, ask your coding agent: "explain what
changed between tracks/airflow/04-on-a-schedule/dags/bin_day.py and
tracks/airflow/06-less-inference/dags/bin_day.py".

<details>
<summary>Try it yourself</summary>

In the checks terminal, where `BINDAY_MODEL` is set, run the quick checks and the agent checks
together:

```bash
uv run --extra airflow pytest tracks/airflow/06-less-inference -n 4 -v
```

Compare the models on this chapter:

```bash
uv run --extra airflow python tracks/airflow/05-cheaper-model/compare.py --chapter 06-less-inference <the models you compared in chapter 5>
```

To run this version in Airflow, stop Airflow in the Airflow terminal with `Ctrl-C`, and start
it again with this chapter's Dag:

```bash
uv run --extra airflow airflow-up 06-less-inference
```

</details>

<details>
<summary>Let your agent write it</summary>

Put chapter 4's version in place of mine, so your agent has something to change:

```bash
cp tracks/airflow/04-on-a-schedule/dags/bin_day.py tracks/airflow/06-less-inference/dags/bin_day.py
```

Then, from the repo folder, with `BINDAY_MODEL` set, start `claude` and paste:

```text
In tracks/airflow/06-less-inference/dags/bin_day.py, change the Dag so that the agent only returns the facts (the next collection date and the containers due, as binday.facts.BinDayFacts) and a plain Python function decide(facts, today) decides whether that date is tomorrow and writes the message. The tests in tracks/airflow/06-less-inference/test_less_inference.py must pass; don't change them or anything under src/. Run them with: uv run --extra airflow pytest tracks/airflow/06-less-inference -n 4 -v
Keep going until they pass. Don't use git, and don't look at other chapters.
```

To compare its version with mine, and then to get mine back:

```bash
git diff tracks/airflow/06-less-inference/dags/bin_day.py
git checkout -- tracks/airflow/06-less-inference/dags/bin_day.py
```

</details>

## What's left

The agent is now a web scraper: it fills in a postcode, reads a date and some bin names off the
page, and hands them over. Everything that happens to that answer is plan python code with no LLM inference.

From the talk: the slide [Move More Out of Inference](https://alexhans.github.io/talks/airflow-summit/2026/it-works-now-what/#/move-more-out-of-inference), and the [video and transcript](https://alexhans.github.io/posts/talk.it-works-now-what.html).

---

<!-- nav:bottom -->
[Home](../../../README.md) · [Contents](../../../README.md#contents) · Airflow track · Previous: [5. Reduce cost while still getting the right answer](../05-cheaper-model/README.md) · Next: [7. Replace the agent with plain code](../07-no-model/README.md)
<!-- /nav:bottom -->
