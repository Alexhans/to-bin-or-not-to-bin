<!-- nav:top -->
[Home](../../../README.md) · [Contents](../../../README.md#contents) · Coding agent track · Previous: [4. Reduce cost while still getting the right answer](../04-cheaper-model/README.md) · Next: [6. Replace the agent with plain code](../06-no-model/README.md)
<!-- /nav:top -->

# 5. Move the decision from the model into code

*"Give the model only what needs a model."*

So far the agent does two jobs: it reads the council's website, and it decides whether the
next collection is tomorrow. The second job is date arithmetic, which plain code does without
a model and the same way every time. A model can get it wrong, for example by saying
"tomorrow" in its message and still deciding not to alert. So in this chapter the agent only
returns the facts, the date and the bins, and a plain Python function decides.

This chapter is mostly to read. Running it is optional, and it works the same way as before.

## What changed

Before, the agent was asked the whole question and the code trusted its decision:

```python
question = f"Today is {today:%A %-d %B %Y}. Do I need to put the bins out tonight?"
answer = claude.ask(question, site, BinDayAlert)
if not answer.put_out_tonight:
    return "Alert: none tonight."
```

Now it's asked only for the facts, and [`bin_day.py`](bin_day.py) decides:

```python
question = f"Today is {today:%A %-d %B %Y}. Which bins go out next, and when?"
facts, usage = claude.ask(question, site, BinDayFacts)


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

In this track, not much per run. Most of what Claude Code reads is its own instructions, so
asking for less doesn't shrink the run much, and it doesn't widen the choice of model either.
Run chapter 4's comparison on this chapter:

```bash
uv run python tracks/agent/04-cheaper-model/compare.py haiku sonnet opus --chapter 05-less-inference --parallel 3
```

You could get something like this:

```
model    runs passing   tokens read   tokens written   seconds   cost per run
haiku             3/3       252,086            1,394      26.6        $0.0082
sonnet            3/3       195,858              680      21.3        $0.1262
opus              3/3       196,629              608      25.2        $0.2616
```

All three models still pass every run, at about the same cost as in chapter 4, so there's no
cheaper model to switch to here: the decision was never the part they got wrong. What you do get is a
decision that's the same every time and is checked in milliseconds, so a model can't get that
part wrong any more. In the Airflow track, where the agent is called from a Dag rather than
through Claude Code, the same change takes two more models from failing to passing.

<details>
<summary>A check caught this chapter's first version</summary>

When I first wrote this chapter, the new question was just "Which bins go out next, and when?"
and no longer said what day it was, because the code works that out now. The two checks from
step 2 failed: asked about the 22 August world, the agent answered with a collection in
November. Without a date in the question, it used the real date it knew instead of the day the
run was for. So the question still says "Today is ...", and only the decision moved into code.
The change I made to ask the model for less had quietly broken the answer, and a check I already
had told me within seconds.

</details>

To see the full difference between the two versions, ask your coding agent: "explain what
changed between tracks/agent/03-on-a-schedule/bin_day.py and
tracks/agent/05-less-inference/bin_day.py".

<details>
<summary>Try it yourself</summary>

Run this chapter from the repo folder, `to-bin-or-not-to-bin`, with the council
running in another terminal (`uv run council`):

```bash
uv run python tracks/agent/05-less-inference/bin_day.py --today 2026-08-26
```

You'll see something like this:

```
[bin_day] model=global.anthropic.claude-opus-5-5 tokens_read=123035 tokens_written=665 seconds=16.2
Next collection: Thursday 27 August 2026, blue recycling wheelie bin and food box.
Alert: sent. Put out the blue recycling wheelie bin and food box tonight, for Thursday 27 August.
```

Run the checks, quick ones and agent ones together:

```bash
uv run pytest tracks/agent/05-less-inference -n 4 -v
```

And compare the models on this chapter:

```bash
uv run python tracks/agent/04-cheaper-model/compare.py haiku sonnet --chapter 05-less-inference
```

To use this version for the scheduled runs:

```bash
tracks/agent/schedule.sh 05-less-inference
```

</details>

<details>
<summary>Let your agent write it</summary>

Put chapter 3's version in place of mine, so your agent has something to change:

```bash
cp tracks/agent/03-on-a-schedule/bin_day.py tracks/agent/05-less-inference/bin_day.py
```

Then, from the repo folder, start `claude` and paste:

```text
In tracks/agent/05-less-inference/bin_day.py, change the code so that the agent only returns the facts (the next collection date and the containers due, as binday.facts.BinDayFacts) and a plain Python function decide(facts, today) decides whether that date is tomorrow and writes the message. The tests in tracks/agent/05-less-inference/test_less_inference.py must pass; don't change them or anything under src/. Run them with: uv run pytest tracks/agent/05-less-inference -n 4 -v
Keep going until they pass. Don't use git, and don't look at other chapters.
```

To compare its version with mine, and then to get mine back:

```bash
git diff tracks/agent/05-less-inference/bin_day.py
git checkout -- tracks/agent/05-less-inference/bin_day.py
```

</details>

## What's left

The agent is now a web scraper: it fills in a postcode, reads a date and some bin names off the
page, and hands them over. Everything that happens to that answer is in the command. And the
skill it follows already names the two URLs to call and says what they return, which is a short
description of a scraper.

From the talk: the slide [Move More Out of Inference](https://alexhans.github.io/talks/airflow-summit/2026/it-works-now-what/#/move-more-out-of-inference), and the [video and transcript](https://alexhans.github.io/posts/talk.it-works-now-what.html).

---

<!-- nav:bottom -->
[Home](../../../README.md) · [Contents](../../../README.md#contents) · Coding agent track · Previous: [4. Reduce cost while still getting the right answer](../04-cheaper-model/README.md) · Next: [6. Replace the agent with plain code](../06-no-model/README.md)
<!-- /nav:bottom -->
