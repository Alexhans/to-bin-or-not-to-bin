# To bin or not to bin

A hands-on companion to my Airflow Summit 2026 talk,
[It Works! Now What? Fast Iteration for AI Capabilities in Airflow](https://alexhans.github.io/posts/talk.it-works-now-what.html),
where you'll also find the video, the slides and a transcript.

## Summary

Getting an AI agent to do something useful is easy now. The hard part comes after it
works, because you'll want to change it and be able to trust it will still work as intended.  You may decide you want to run it on a schedule, reduce cost, make it faster or actually change the behaviour to suit new needs.  Any change that you make can quietly
break what worked, and if the only way to find out is to test things manually, you end up changing it slowly or not at all.

The talk's answer is to use fast feedback loops. Before handing a job to an agent, write a check that tells you whether the answer is right, and run it after every change, so that each change is checked by one command instead of by hand.

In this tutorial you build that loop yourself, on one small problem, starting from the first prompt.

## The problem

In my part of London, the council collects household waste from outside each house:
rubbish and recycling on alternate weeks, and food waste every week. So the night before, I
have to remember to check the council's website and put the right bins out. If I miss it,
that bin waits another two weeks on top of the two it has already waited, which is a whole
month of rubbish in my garden.

![Rubbish and recycling alternate weekly and food goes every week, so missing one rubbish collection means a month of rubbish in the garden](https://alexhans.github.io/talks/airflow-summit/2026/it-works-now-what/images/article/bins.png)

To mimic this problem, you'll use a made-up borough, Dilly Dally, with a made-up postcode,
`FX1 2ZZ`. Its website runs on your machine, so you don't hit any real service or any real
council.

## What you'll do

1. **Delegate to an agent with an "agent skill".** A coding agent is an assistant that can read
   websites and run commands for you, such as Claude Code or Codex, and a skill is a repeatable workflow, which can
   be as simple as a markdown file with instructions.
2. **Check the agent's answer automatically**, with a test that compares what it says with
   what you found by hand.
3. **Get timely alerts without running it yourself**, with Apache Airflow or with `cron`.
4. **Reduce cost while still getting the right answer**, even to a point where no AI model is needed.

## You need

- [git](https://git-scm.com/downloads), to download this tutorial.
- [uv](https://docs.astral.sh/uv/getting-started/installation/), which installs and runs the
  tutorial's Python code, including the made-up council's website and the checks.
- [Claude Code](https://docs.claude.com/en/docs/claude-code/setup), signed in with a Claude
  account or set up with an API key. The commands in this tutorial are written for it.
- [jq](https://jqlang.org/download/), which turns the agent's JSON output into something
  you can read.

Linux or macOS. On Windows, use [WSL](https://learn.microsoft.com/windows/wsl/install).

## Start

```bash
git clone https://github.com/Alexhans/to-bin-or-not-to-bin
cd to-bin-or-not-to-bin
uv sync
```

`uv sync` installs everything the tutorial needs into a `.venv` folder inside it, so
nothing is installed anywhere else on your machine.

<!-- start -->
Then start with [step 1: Delegate to an agent with a skill](steps/01-do-it-for-me/README.md). After step 2
you'll choose whether to carry on with Airflow or with your coding agent.
<!-- /start -->

## Contents

<!-- toc -->

1. [Delegate to an agent with a skill](steps/01-do-it-for-me/README.md)
2. [Check the agent's answer automatically to enable fast iteration](steps/02-know-its-right/README.md)

Airflow track:

3. [Run the skill in Airflow](tracks/airflow/03-in-airflow/README.md)
4. [Get timely alerts without running it yourself](tracks/airflow/04-on-a-schedule/README.md)
5. [Reduce cost while still getting the right answer](tracks/airflow/05-cheaper-model/README.md)
6. [Move the decision from the model into code](tracks/airflow/06-less-inference/README.md)
7. [Replace the agent with plain code](tracks/airflow/07-no-model/README.md)

Coding agent track:

3. [Get timely alerts without running it yourself](tracks/agent/03-on-a-schedule/README.md)
4. [Reduce cost while still getting the right answer](tracks/agent/04-cheaper-model/README.md)
5. [Move the decision from the model into code](tracks/agent/05-less-inference/README.md)
6. [Replace the agent with plain code](tracks/agent/06-no-model/README.md)
<!-- /toc -->

## Feedback

If something doesn't work, or you'd like this to cover something it doesn't, open an
[issue](https://github.com/Alexhans/to-bin-or-not-to-bin/issues), or find me through
[my links](https://linktr.ee/alex.guglielmone.nemi).
