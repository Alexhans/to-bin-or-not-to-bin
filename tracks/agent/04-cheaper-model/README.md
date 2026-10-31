<!-- nav:top -->
[Home](../../../README.md) · [Contents](../../../README.md#contents) · Coding agent track · Previous: [3. Get timely alerts without running it yourself](../03-on-a-schedule/README.md) · Next: [5. Move the decision from the model into code](../05-less-inference/README.md)
<!-- /nav:top -->

# 4. Reduce cost while still getting the right answer

*"Do the same for less."*

Now that it runs every day, it costs you 7 × the cost of one run each week. Chapter 3's command runs the
whole workflow, and setting `BINDAY_CLAUDE_MODEL` lets you choose which Claude model it uses. So far it
has used Claude Code's default model, Opus at the time of writing, which is meant to be the most
capable but costs more than Sonnet and Haiku. Could Sonnet or Haiku do the same job for less? Don't conjecture,
prove it: run the same checks with each.

The checks are what let you compare the models, and they outlast them: new models will come
along, and the same checks will tell you whether each one does the job, until you decide they
no longer describe what you want.

![A frontier model, a mid-tier model and two open-weight models all go through the same check: passes or doesn't pass](https://alexhans.github.io/talks/airflow-summit/2026/it-works-now-what/images/article/change-model.png)

## Compare the models

[`compare.py`](compare.py) runs chapter 3's agent checks with each model, three times. The same
model can pass one run and fail the next, so three runs per model is a common quick safeguard;
you can avoid much of this by moving work out of the model, but this tutorial goes one step at
a time. From the repo folder, `to-bin-or-not-to-bin`:

```bash
uv run python tracks/agent/04-cheaper-model/compare.py haiku sonnet opus --parallel 3
```

The runs go at the same time, so the whole comparison takes about as long as the slowest few
runs, and a line appears as each one finishes. `--parallel 3` keeps it to three Claude Code
agents at once, which is gentler on your plan's limits; leave it out for the default of 8.
`-n 5` would run each model five times. You'll see something like this:

```
Running 3 models, 3 runs each, up to 3 at a time...
  sonnet, run 1: 4/4 checks passed (45 s)
  opus, run 1: 4/4 checks passed (51 s)
  haiku, run 1: 4/4 checks passed (57 s)
  haiku, run 2: 4/4 checks passed (41 s)
  sonnet, run 2: 4/4 checks passed (43 s)
  opus, run 2: 4/4 checks passed (52 s)
  haiku, run 3: 4/4 checks passed (39 s)
  sonnet, run 3: 4/4 checks passed (41 s)
  opus, run 3: 4/4 checks passed (48 s)

model    runs passing   tokens read   tokens written   seconds   cost per run
haiku             3/3       252,900            1,552      28.9        $0.0084
sonnet            3/3       196,622              774      24.5        $0.1319
opus              3/3       199,466              781      27.8        $0.2664
```

The table has one row per model: how many runs passed every check, and what a typical run read,
wrote, took and cost. If a run fails, the failing checks are listed below the table, grouped
under that model, with how many runs each failed in and the first line of why. Every run's full
results are kept in `tracks/agent/04-cheaper-model/results/`, so you can read them without
running anything again.

All three models passed every run, so the cost is what separates them: by these estimates a
Haiku run cost about $0.008 against about $0.27 for Opus, which is what chapter 3 used by
default. The checks and the skill are the same in both, so it's the same job done for much
less.

<details>
<summary>What the cost column does and doesn't tell you</summary>

It's the estimate the tool reports for the run that happened, and that run's input was partly
served from the prompt cache. Reading from the cache costs much less than fresh input, and how
much of a run hits it depends on what ran just before, as the note on
[comparing runs in step 1](../../../steps/01-do-it-for-me/README.md#did-the-skill-help) describes.
So part of the gap between two models here is cache luck rather than price.

Here Haiku read more tokens than Opus and still came out about thirty times cheaper, which is
more than the models' published prices differ by. To compare models on price alone, take the
tokens each one read and price them at that model's uncached input rate.

</details>


## Pick one

The checks say which models do the job, and the table says what they cost. Here all three do the
job, so take the cheapest: Haiku. Three runs is a small sample, so run the comparison again
before you rely on it, with more runs if you like (`-n 5`), and the cost is Claude Code's
estimate, so check it against your plan or your provider's prices. If a wrong answer would cost
you more than the runs do, the middle option is worth the money.

Once you've chosen, use it for the scheduled runs, with your choice in place of `<your choice>`:

```bash
BINDAY_CLAUDE_MODEL=<your choice> tracks/agent/schedule.sh 03-on-a-schedule
```

Nothing else changes: the command, the skill and the checks are the same. The checks told you
the cheaper model does the job, and they'll tell you the same about whichever model comes
next.

## What now?

The model is smaller now, but every run still goes through a coding agent, so it can still
feel slow and costly.

From the talk: the slide [Change the Model](https://alexhans.github.io/talks/airflow-summit/2026/it-works-now-what/#/change-the-model), and the [video and transcript](https://alexhans.github.io/posts/talk.it-works-now-what.html).

---

<!-- nav:bottom -->
[Home](../../../README.md) · [Contents](../../../README.md#contents) · Coding agent track · Previous: [3. Get timely alerts without running it yourself](../03-on-a-schedule/README.md) · Next: [5. Move the decision from the model into code](../05-less-inference/README.md)
<!-- /nav:bottom -->
