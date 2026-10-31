<!-- nav:top -->
[Home](../../../README.md) · [Contents](../../../README.md#contents) · Coding agent track · Previous: [5. Move the decision from the model into code](../05-less-inference/README.md)
<!-- /nav:top -->

# 6. Replace the agent with plain code

*"Do I need a model at all?"*

Look at the path so far. You had an agent skill, and the agent solved a lot at inference time.
Then the command took over the schedule and the decision, and the agent was left as a web
scraper of sorts. Can you go further? What I run at home doesn't use AI at all. I use AI to
change it, but it runs as a plain scraper against the same checks.

It costs almost nothing to run: no inference, just the electricity of the machine it runs on.
It's faster, easier to optimise, and it removes the uncertainty of a model's answers, since
the same input gives the same output every time. This is how most things should be, where
they can.

## The plain code

This chapter's [`bin_day.py`](bin_day.py) doesn't ask a model. In its place,
[`council.py`](council.py) calls the two addresses the skill named, the same way the skill
describes:

```python
def next_collection(site: str, postcode: str = POSTCODE, address: str = ADDRESS) -> BinDayFacts:
    addresses = httpx.post(f"{site}/api/addresses", data={"postcode": postcode}).json()["addresses"]
    uprn = ...  # the one address that starts with "2 Wibble Way"
    rows = httpx.post(f"{site}/api/collections", data={"uprn": uprn}).json()["collections"]
    first = min(dt.date.fromisoformat(r["next_collection"]) for r in rows)
    ...
```

Everything else, deciding whether it's tomorrow and sending the alert once, is the same code as
before.

## Try it

With the council running in another terminal (`uv run council`), run it from the repo folder,
`to-bin-or-not-to-bin`, as if it were New Year's Day:

```bash
time uv run python tracks/agent/06-no-model/bin_day.py --today 2027-01-01
```

You'll see something like this:

```
[bin_day] model=none tokens_read=0 tokens_written=0 seconds=0.03
Next collection: Saturday 2 January 2027, blue recycling wheelie bin and food box.
Alert: sent. Put out the blue recycling wheelie bin and food box tonight, for Saturday 2 January.

real	0m0.242s
```

It takes a quarter of a second, against tens of seconds for each agent run before. The checks,
in [`test_no_model.py`](test_no_model.py), don't need a model any more either, so they all run
in about a second:

```bash
uv run pytest tracks/agent/06-no-model -v
```

## Ask it from Claude Code, cheaply

You can keep asking in one line from Claude Code, and let the skill run the plain command
instead of reading the website itself. Ask your agent to write that skill in this chapter's
empty `sandbox` folder. From the repo folder, start `claude` and paste:

```text
Write a skill in tracks/agent/06-no-model/sandbox/.claude/skills/bin-day/SKILL.md that answers questions about bin day by running this command and reporting what it prints, with the full path of this repo folder in place of REPO: uv run --project REPO python REPO/tracks/agent/06-no-model/bin_day.py --no-alert
Don't call the council website yourself.
```

Then ask it from that folder with each model, and compare with step 1:

```bash
cd tracks/agent/06-no-model/sandbox
S='{answer: .result, model: (.modelUsage | keys | join(", ")), turns: .num_turns, seconds: (.duration_ms / 1000), tokens_read: (.usage.input_tokens + .usage.cache_creation_input_tokens + .usage.cache_read_input_tokens), tokens_written: .usage.output_tokens}'
for model in haiku sonnet opus; do
  echo "== $model"
  claude -p "Do I need to put the bins out?" --model $model --allowedTools "Bash(uv run:*)" Skill --output-format json | jq -c "$S"
done
cd ../../../..
```

You'll see something like this:

```
== haiku
{"answer":"Yes. Collection is today, Thursday 29 October 2026, for the black rubbish wheelie bin and the food box.","model":"claude-haiku-5-5","turns":4,"seconds":9.264,"tokens_read":91625,"tokens_written":351}
== sonnet
{"answer":"Yes, collection is today (Thursday 29 October 2026). Put out the black rubbish wheelie bin and the food box.","model":"claude-sonnet-5-5","turns":4,"seconds":9.523,"tokens_read":89162,"tokens_written":286}
== opus
{"answer":"Yes. Collection is today, Thursday 29 October 2026, so put out the black rubbish wheelie bin and the food box.","model":"claude-opus-5-5","turns":4,"seconds":10.781,"tokens_read":89297,"tokens_written":311}
```

The agent no longer reads the website or its JavaScript, so asking is quicker and cheaper with
any model, and the answer comes from the same code your checks test. The scheduled run doesn't
need the agent at all, so both ways of using it, on a schedule and on demand, are now quick and
cheap.

## Let your agent write it

This part is optional. Here the agent's job is to write the code that replaces it. Delete mine:

```bash
rm tracks/agent/06-no-model/council.py
```

Then, from the repo folder, start `claude` and paste:

```text
Write tracks/agent/06-no-model/council.py with a function next_collection(site) that does what the bin-day skill in steps/01-do-it-for-me/sandbox/.claude/skills/bin-day/SKILL.md describes, in plain Python with httpx and no model. The tests in tracks/agent/06-no-model/test_no_model.py must pass; don't change them or anything under src/. Run them with: uv run pytest tracks/agent/06-no-model -v
Keep going until they pass. Don't use git, and don't look at other chapters.
```

To compare its version with mine, and then to get mine back:

```bash
git diff tracks/agent/06-no-model/council.py
git checkout -- tracks/agent/06-no-model/council.py
```

## Put it on a schedule

Schedule this chapter's command instead of the earlier one:

```bash
tracks/agent/schedule.sh 06-no-model
```

To take the tutorial out of your crontab altogether:

```bash
tracks/agent/schedule.sh --remove
```

## When the website changes

What happens when the council changes its website? This will break: `next_collection` stops
with an error instead of guessing, and the error ends up in `run.log`. But it hasn't happened
yet, and I'm not sure I want to pay for inference for a long time just in case. And if you're
getting the idea of feedback loops, the failure itself can start another loop: point your
agent at it with the checks ("fix it so the tests pass"), or write new checks if what you
want has changed.

In any case, I hope you took something out of this. If you have a request or some feedback, open
an [issue](https://github.com/Alexhans/to-bin-or-not-to-bin/issues) on the repo, or
find me through [my links](https://linktr.ee/alex.guglielmone.nemi).

From the talk: the slide [Move More Out of Inference](https://alexhans.github.io/talks/airflow-summit/2026/it-works-now-what/#/move-more-out-of-inference), and the [video and transcript](https://alexhans.github.io/posts/talk.it-works-now-what.html).

---

<!-- nav:bottom -->
[Home](../../../README.md) · [Contents](../../../README.md#contents) · Coding agent track · Previous: [5. Move the decision from the model into code](../05-less-inference/README.md)
<!-- /nav:bottom -->
