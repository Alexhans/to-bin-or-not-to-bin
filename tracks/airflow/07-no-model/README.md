<!-- nav:top -->
[Home](../../../README.md) · [Contents](../../../README.md#contents) · Airflow track · Previous: [6. Move the decision from the model into code](../06-less-inference/README.md)
<!-- /nav:top -->

# 7. Replace the agent with plain code

*"Do I need a model at all?"*

Look at the path so far. You had an agent skill, and the agent solved a lot at inference time.
Then the Dag took over the schedule and the decision, and the agent was left as a web scraper
of sorts. [Can you go further?](https://alexhans.github.io/talks/airflow-summit/2026/it-works-now-what/#/move-more-out-of-inference).  Yes you can.  What I run at home doesn't use AI at all. I use AI to evolve the Dag 
as my needs change, but the Dag itself runs as a plain scraper against the same checks.

It costs almost nothing to run: no inference, just the electricity of the machine it runs on.
It's faster, easier to optimise, and it removes the uncertainty of a model's answers, since
the same input gives the same output every time. This is how most things should be, where
they can.

## The plain code

This chapter's Dag, [`dags/bin_day.py`](dags/bin_day.py), doesn't ask a model, so it doesn't
need `BINDAY_MODEL` or the Common AI provider. In place of the agent task, `ask_the_council`
calls [`dags/council.py`](dags/council.py), which calls the two addresses the skill named, the
same way the skill describes:

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

## Check it

The checks in [`test_no_model.py`](test_no_model.py), don't need a model any more, so none of
them is marked `agent`. Besides the checks from chapter 6, there's one for a day none of the
earlier checks used, 14 October, so that `next_collection` can't pass by knowing the answers.
From the repo folder, `to-bin-or-not-to-bin`:

```bash
uv run --extra airflow pytest tracks/airflow/07-no-model -v
```

You'll see something like this:

```
tracks/airflow/07-no-model/test_no_model.py::test_decides_tonight_the_day_before PASSED [  9%]
tracks/airflow/07-no-model/test_no_model.py::test_decides_nothing_two_days_before PASSED [ 18%]
tracks/airflow/07-no-model/test_no_model.py::test_decides_nothing_on_the_collection_day_itself PASSED [ 27%]
tracks/airflow/07-no-model/test_no_model.py::test_decides_nothing_after_the_collection PASSED [ 36%]
tracks/airflow/07-no-model/test_no_model.py::test_decides_tonight_across_the_new_year PASSED [ 45%]
tracks/airflow/07-no-model/test_no_model.py::test_never_tells_me_twice PASSED [ 54%]
tracks/airflow/07-no-model/test_no_model.py::test_the_step_2_checks_still_pass[ordinary week] PASSED [ 63%]
tracks/airflow/07-no-model/test_no_model.py::test_the_step_2_checks_still_pass[new year's week] PASSED [ 72%]
tracks/airflow/07-no-model/test_no_model.py::test_answers_for_a_day_it_has_not_seen PASSED [ 81%]
tracks/airflow/07-no-model/test_no_model.py::test_tells_me_the_night_before PASSED [ 90%]
tracks/airflow/07-no-model/test_no_model.py::test_stays_quiet_two_nights_before PASSED [100%]
============================== 11 passed in 7.65s ==============================
```

None of them waits for a model, so they take seconds, most of it Airflow setting up its test
database.

## Let your agent write it

This part is optional. Here the agent's job is to write the code that replaces it. Delete mine:

```bash
rm tracks/airflow/07-no-model/dags/council.py
```

Then, from the repo folder, start `claude` and paste:

```text
Write tracks/airflow/07-no-model/dags/council.py with a function next_collection(site) that does what the bin-day skill in steps/01-do-it-for-me/sandbox/.claude/skills/bin-day/SKILL.md describes, in plain Python with httpx and no model. The tests in tracks/airflow/07-no-model/test_no_model.py must pass; don't change them or anything under src/. Run them with: uv run --extra airflow pytest tracks/airflow/07-no-model -v
Keep going until they pass. Don't use git, and don't look at other chapters.
```

To compare its version with mine, and then to get mine back:

```bash
git diff tracks/airflow/07-no-model/dags/council.py
git checkout -- tracks/airflow/07-no-model/dags/council.py
```

## Run it every evening

In the Airflow terminal, stop Airflow with `Ctrl-C` if it's running, and start it again with
this chapter's Dag in place of the earlier one:

```bash
uv run --extra airflow airflow-up 07-no-model
```

Open <http://localhost:8080>, go to `bin_day`, press **Trigger**, set **Logical Date** to New
Year's Day, 1 January 2027, and press **Trigger**. Then open the **Runs** tab, click that
run and then `tell_me`. Its log shows the answer, then what it did about the alert:

```
Next collection: Saturday 2 January 2027, blue recycling wheelie bin and food box.
Alert: sent. Put out the blue recycling wheelie bin and food box tonight, for Saturday 2 January.
```

## When the website changes


What happens when the council changes its website? The scraper part will break and Airflow will mark the task as failed.

That hasn't happened yet, and I'm not sure I want to pay for inference every evening in case it
does, but I can set alerts and deal with it in two ways:

- On alert, operating on the Dag and fixing the scraper.  Probably using a coding agent to create an updated version of the python code that scrapes.
- On alert, auto-remediate by having that previous step be performed automatically.

The agent will have the logs to root cause, and the checks to honor, so it's just hooking up the loop to your alerting flow.

Auto-remediation is a small version of what agentic software development and orchestration can be, though.  Any new feature or change can be evolved this way, if your tests and environment are efficient and safe enough to allow for it.  Think of online training of a machine learning model, but instead of having a machine learning model, you have your entire infrastructure at your disposal.

In any case, I hope you took something out of this. If you have a request or some feedback, open
an [issue](https://github.com/Alexhans/to-bin-or-not-to-bin/issues) on the repo, or
find me through [my links](https://linktr.ee/alex.guglielmone.nemi).

From the talk: the slide [Move More Out of Inference](https://alexhans.github.io/talks/airflow-summit/2026/it-works-now-what/#/move-more-out-of-inference), and the [video and transcript](https://alexhans.github.io/posts/talk.it-works-now-what.html).

---

<!-- nav:bottom -->
[Home](../../../README.md) · [Contents](../../../README.md#contents) · Airflow track · Previous: [6. Move the decision from the model into code](../06-less-inference/README.md)
<!-- /nav:bottom -->
