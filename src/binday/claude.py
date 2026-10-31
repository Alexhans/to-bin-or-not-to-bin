"""Ask the bin-day skill from step 1 a question through Claude Code, and get typed data back."""

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

SANDBOX = Path(__file__).resolve().parents[2] / "steps/01-do-it-for-me/sandbox"


@dataclass
class Usage:
    """What one `claude -p` run took."""

    model: str
    tokens_read: int
    tokens_written: int
    seconds: float
    cost_usd: float | None = None

    def line(self) -> str:
        cost = f" cost_usd={self.cost_usd:.4f}" if self.cost_usd is not None else ""
        return (f"[bin_day] model={self.model} tokens_read={self.tokens_read} "
                f"tokens_written={self.tokens_written} seconds={self.seconds:.1f}{cost}")


def ask[T: BaseModel](question: str, site: str, answer_type: type[T], model: str | None = None) -> tuple[T, Usage]:
    """Ask the skill `question` about the council at `site`, and return its answer as `answer_type`.

    `model` (or BINDAY_CLAUDE_MODEL) is passed to `claude --model`, for example haiku or sonnet.
    """
    site = site.rstrip("/")
    if not (SANDBOX / ".claude/skills/bin-day/SKILL.md").exists():
        raise RuntimeError("Make the bin-day skill in step 1 first.")
    prompt = (f"Use the bin-day skill, with the council site at {site} instead of http://localhost:8111 "
              f"(for every URL, including the API endpoints, e.g. {site}/api/addresses). {question}")
    cmd = ["claude", "-p", prompt, "--allowedTools", "Bash(curl:*)", "Skill",
           "--json-schema", json.dumps(answer_type.model_json_schema()), "--output-format", "json"]
    if model := model or os.environ.get("BINDAY_CLAUDE_MODEL"):
        cmd += ["--model", model]
    done = subprocess.run(cmd, cwd=SANDBOX, capture_output=True, text=True, timeout=900)
    try:
        out = json.loads(done.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"claude failed (exit {done.returncode}): {done.stderr[-500:]}") from None
    if not out.get("structured_output"):
        raise RuntimeError(f"The agent gave no answer: {str(out.get('result'))[:300]}")
    usage = out["usage"]
    return answer_type.model_validate(out["structured_output"]), Usage(
        model=",".join(out.get("modelUsage", {})),
        tokens_read=usage["input_tokens"] + usage["cache_creation_input_tokens"] + usage["cache_read_input_tokens"],
        tokens_written=usage["output_tokens"],
        seconds=out["duration_ms"] / 1000,
        cost_usd=out.get("total_cost_usd"),
    )
