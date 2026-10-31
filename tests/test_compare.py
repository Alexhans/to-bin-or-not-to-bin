"""Checks for how compare.py labels models and summarises runs. No model needed."""

from binday.compare import Run, labels, short_name, summary


def test_short_names_drop_the_provider_region_vendor_and_version():
    assert short_name("bedrock:global.anthropic.claude-haiku-4-5-20251001-v1:0") == "claude-haiku-4-5"
    assert short_name("bedrock:openai.gpt-oss-20b-1:0") == "gpt-oss-20b"
    assert short_name("bedrock:mistral.mistral-large-3-675b-instruct") == "mistral-large-3-675b-instruct"
    assert short_name("openrouter:openai/gpt-oss-20b") == "gpt-oss-20b"
    assert short_name("bedrock:global.anthropic.claude-opus-5-5") == "claude-opus-5-5"
    assert short_name("haiku") == "haiku"


def test_full_names_when_short_ones_would_clash():
    models = ["openrouter:openai/gpt-oss-20b", "bedrock:openai.gpt-oss-20b"]
    assert labels(models) == {m: m for m in models}


def test_summary_counts_clean_runs_and_groups_failures_by_check():
    ok = Run(passed=4, total=4, usage=[(100, 10, 1.0, 0.01)])
    bad = Run(passed=3, total=4, failures=[("test_quiet", "Alert: sent.")], usage=[(300, 30, 3.0, 0.03)])
    text = summary({"m": [ok, bad, bad]}, {"m": "m"})
    assert "1/3" in text
    assert "300" in text  # the median of 100, 300, 300
    assert "$0.0300" in text  # the median cost
    assert 'test_quiet failed in 2/3 runs: "Alert: sent."' in text


def test_no_cost_when_a_run_reports_none():
    run = Run(passed=1, total=1, usage=[(100, 10, 1.0, None)])
    assert summary({"m": [run]}, {"m": "m"}).splitlines()[1].rstrip().endswith("-")
