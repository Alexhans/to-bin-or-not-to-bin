<!-- nav:top -->
[Home](../../../README.md) · [Contents](../../../README.md#contents) · Airflow track · Previous: [4. Get timely alerts without running it yourself](../04-on-a-schedule/README.md) · Next: [6. Move the decision from the model into code](../06-less-inference/README.md)
<!-- /nav:top -->

# 5. Reduce cost while still getting the right answer

*"Do the same for less."*

Now that it runs every day, it costs you 7 × the cost of one run each week. Chapter 4's Dag
asks whichever model `BINDAY_MODEL` you had set, and so far that you may have been using a powerful 
frontier model, which is meant to be the most capable but costs more than smaller ones.
Could a mid-tier model or an open-weight one do the same job for less? 

Don't conjecture, prove it: run the same checks with each.

The checks let you compare models, and they outlast them: new models will come
along, and the same checks will tell you whether each one does the job, until you decide they
no longer describe what you want. This is similar to what you see as external benchmarks, but
 instead of being for generic problems, you're benchmarking your actual workflows.

![A frontier model, a mid-tier model and two open-weight models all go through the same check: passes or doesn't pass](https://alexhans.github.io/talks/airflow-summit/2026/it-works-now-what/images/article/change-model.png)

## Compare the models

[`compare.py`](compare.py) runs chapter 4's agent checks with each model, three times. The same
model can pass one run and fail the next, so three runs per model is a common quick safeguard.

If you're concerned about why three and not five or some other number, you can actually avoid that question altogether 
by moving work out of the model, but this tutorial wants to show the progression for illustrative purposes.

Running several tests at once also uses your AI budget faster so it may be something that you want to do thoughtfully.

In the checks terminal, give it the models as you'd set them in `BINDAY_MODEL`; it sets `BINDAY_MODEL` for
each run itself. These are the ones I tried while writing this tutorial (The [talk has many LLM models in a beautiful chart](https://alexhans.github.io/talks/airflow-summit/2026/it-works-now-what/#/change-the-model-1)), on Amazon Bedrock:

```bash
uv run --extra airflow python tracks/airflow/05-cheaper-model/compare.py \
  bedrock:global.anthropic.claude-opus-5-5 \
  bedrock:global.anthropic.claude-sonnet-5-5 \
  bedrock:global.anthropic.claude-haiku-5-5 \
  bedrock:global.anthropic.claude-haiku-4-5-20251001-v1:0 \
  bedrock:openai.gpt-oss-120b-1:0 \
  bedrock:openai.gpt-oss-20b-1:0 \
  bedrock:mistral.mistral-large-3-675b-instruct
```

With another provider, use its names for the models you want to try, for example
`openrouter:openai/gpt-oss-20b`; [Choosing a model](../../../docs/models.md) has the options.

All the runs go at the same time, up to 8 at once, so the whole comparison takes about as long
as the slowest run, and a line appears as each one finishes. `-n 5` would run each model five
times, and `--parallel 4` would run at most four at a time. You'll see something like this:

```
Running 7 models, 3 runs each, up to 8 at a time...
  claude-haiku-4-5, run 1: 3/4 checks passed (88 s)
  claude-haiku-5-5, run 1: 4/4 checks passed (98 s)
  mistral-large-3-675b-instruct, run 1: 3/4 checks passed (99 s)
  gpt-oss-20b, run 1: 4/4 checks passed (102 s)
  claude-opus-5-5, run 2: 4/4 checks passed (104 s)
  claude-opus-5-5, run 1: 4/4 checks passed (104 s)
  claude-sonnet-5-5, run 1: 4/4 checks passed (105 s)
  gpt-oss-120b, run 1: 3/4 checks passed (106 s)
  claude-sonnet-5-5, run 2: 4/4 checks passed (100 s)
  claude-haiku-4-5, run 2: 3/4 checks passed (91 s)
  claude-haiku-5-5, run 2: 4/4 checks passed (100 s)
  mistral-large-3-675b-instruct, run 2: 3/4 checks passed (94 s)
  gpt-oss-120b, run 2: 4/4 checks passed (102 s)
  gpt-oss-20b, run 2: 4/4 checks passed (103 s)
  claude-opus-5-5, run 3: 4/4 checks passed (102 s)
  claude-sonnet-5-5, run 3: 4/4 checks passed (107 s)
  claude-haiku-4-5, run 3: 3/4 checks passed (64 s)
  claude-haiku-5-5, run 3: 4/4 checks passed (71 s)
  mistral-large-3-675b-instruct, run 3: 4/4 checks passed (57 s)
  gpt-oss-120b, run 3: 4/4 checks passed (70 s)
  gpt-oss-20b, run 3: 3/4 checks passed (82 s)

model                           runs passing   tokens read   tokens written   seconds   cost per run
claude-opus-5-5                          3/3        13,631              432      34.0        $0.0116
claude-sonnet-5-5                        3/3        13,633              397      32.2        $0.0056
claude-haiku-5-5                         3/3        13,633              586      30.8        $0.0005
claude-haiku-4-5                         0/3        11,409              332      26.9        $0.0131
gpt-oss-120b                             2/3         8,422              922      31.9        $0.0018
gpt-oss-20b                              2/3         7,868              854      32.7        $0.0008
mistral-large-3-675b-instruct            1/3         8,419              281      26.9        $0.0046

Tokens, seconds and cost are the median of one agent run. Cost is the estimate the tool reports, and `-` where it reports none.

claude-haiku-4-5
  test_stays_quiet_two_nights_before failed in 3/3 runs: "AssertionError: Alert: sent. Put out your blue recycling wheelie bin and food box tonight by 7am Thursday for collection" | "AssertionError: Alert: sent. Put out the blue recycling wheelie bin and food box tonight; collection is tomorrow (Thursd"

gpt-oss-120b
  test_tells_me_the_night_before failed in 1/3 runs: "AssertionError: Alert: none tonight. No – the next collection is on Saturday 27 August 2026. You don’t need to put any b"

gpt-oss-20b
  test_the_step_2_checks_still_pass[ordinary week] failed in 1/3 runs: "AssertionError: assert BinDayFacts(n...ers_due=set()) == BinDayFacts(n...WHEELIE BIN'})"

mistral-large-3-675b-instruct
  test_stays_quiet_two_nights_before failed in 2/3 runs: "AssertionError: Alert: sent. Put out the blue recycling wheelie bin and food box tonight"

Every run's full results are in tracks/airflow/05-cheaper-model/results/.
```

The table has one row per model: how many runs passed every check, and what a typical run
read, wrote, took and cost, using the cost estimate that Airflow's task log also shows. Below it, you can see each model's failures and the reason. Every run's full results are kept in `tracks/airflow/05-cheaper-model/results/`, so you can read them without running anything again. To see one model's whole difference, run its checks yourself:

```bash
BINDAY_MODEL=<a model that failed> uv run --extra airflow pytest tracks/airflow/04-on-a-schedule -n 4 -v
```

<details>
<summary>Anecdotal evidence</summary>
Haiku 5.5 passed all three runs, and cost a small fraction of what the Opus runs cost, about
$0.0005 against about $0.0116 by these estimates, with Sonnet 5.5 also passing every run at
roughly half Opus's cost. The older Haiku 4.5 failed the check on 25 August in every run, by
telling me to put the bins out two nights early, and it cost more than Opus did, even though
it's a smaller model. The gpt-oss and Mistral models passed some runs and
failed others, on the decision or with a Dag run that failed outright, for example when a model
called a tool by a name that doesn't exist.
</details>

A smaller model is not automatically cheaper or more reliable, which is
the reason to measuring instead of assuming. 

Reading the results is also something you may want to hand to your agent. If you have run a comparison, from the repo folder, start
`claude` and paste:

```text
Read the files in tracks/airflow/05-cheaper-model/results/ and tell me, for each model, why its failing runs failed and which check they failed. Then say which model you would pick for cost and speed, and why.
```

> [!NOTE]
> While making this tutorial, I found that whether a model passed depended partly on how it
> wrote the bin names, `food box` or `FOOD BOX`, and that came from how each agent had
> happened to write its skill. Which bins go out is what I really cared about, so I changed the check to
> ignore capitals and spacing (`BinDayFacts` in
> [`src/binday/facts.py`](../../../src/binday/facts.py)). Deciding what a check should and
> shouldn't care about is part of writing it.

<details>
<summary>What the cost column does and doesn't tell you</summary>

The cost is an estimate of a particular "Agent run".  Part of that is actually served from a prompt cache.

 Reading from the cache costs much less than fresh input, and how much of a run hits it depends on what ran just before, as the note on [comparing runs in step 1](../../../steps/01-do-it-for-me/README.md#did-the-skill-help) describes.
So part of the gap between models here is cache luck rather than actual price.

The estimate also depends on the price list the tool carries, which may not match what your
provider bills you, and prices change. Haiku 4.5 costing more than Haiku 5.5 here is a real possibility, and
not something you'd guess from their names. To compare models on price alone, look up your
provider's current rates and price the tokens each model read at its uncached input rate, which
gives you the most a run could have cost and doesn't depend on the cache.

</details>

## Pick one

Having done the comparisons you're satisfied with, you'd pick a model to actually put "in production" for your scheduled runs, based on cost, speed and reliability.

Once you've chosen, switch to it. Stop Airflow in the Airflow terminal with `Ctrl-C`, then start
it again with the new model:

```bash
export BINDAY_MODEL=bedrock:global.anthropic.claude-haiku-5-5
uv run --extra airflow airflow-up 04-on-a-schedule
```

Nothing else changes: the Dag, the skill and the checks are the same, and the connection is
made from the new `BINDAY_MODEL`. That's what the checks are for. They said the cheaper model is
safe to use, and they will say so again for the next model that comes along.

## What now?

Haiku 5.5 passes, but some of the other models failed on the decision itself, whether tonight
is the evening before a collection. That's date arithmetic, and it doesn't need a model. The
next chapter moves it into code, and compares the models again.

From the talk: the slide [Change the Model](https://alexhans.github.io/talks/airflow-summit/2026/it-works-now-what/#/change-the-model), and the [video and transcript](https://alexhans.github.io/posts/talk.it-works-now-what.html).

---

<!-- nav:bottom -->
[Home](../../../README.md) · [Contents](../../../README.md#contents) · Airflow track · Previous: [4. Get timely alerts without running it yourself](../04-on-a-schedule/README.md) · Next: [6. Move the decision from the model into code](../06-less-inference/README.md)
<!-- /nav:bottom -->
