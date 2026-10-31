#!/usr/bin/env bash
# Run a chapter's bin_day.py at 7pm every day, replacing any chapter scheduled before.
#   tracks/agent/schedule.sh 03-on-a-schedule
#   tracks/agent/schedule.sh --remove
# BINDAY_CLAUDE_MODEL, if set, is passed on to bin_day.py.
set -euo pipefail

TRACK="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$TRACK/../.." && pwd)"

if [ $# -ne 1 ]; then
  echo "Usage: $0 <chapter folder, e.g. 03-on-a-schedule> | --remove" >&2
  exit 1
fi

# Your crontab without this track's lines.
OTHERS="$(crontab -l 2>/dev/null | grep -vF "$TRACK/" || true)"

if [ "$1" = "--remove" ]; then
  echo "$OTHERS" | crontab -
  echo "Removed the bin-day job from your crontab."
  exit 0
fi

CHAPTER="$TRACK/${1%/}"
if [ ! -f "$CHAPTER/bin_day.py" ]; then
  echo "There's no bin_day.py in $CHAPTER" >&2
  exit 1
fi

# Cron starts with almost no PATH, so give it the folders that hold uv and claude.
command -v uv > /dev/null || { echo "Install uv first: https://docs.astral.sh/uv/" >&2; exit 1; }
CRON_PATH="$(dirname "$(command -v uv)"):$(dirname "$(command -v claude || echo /usr/bin)")"
# Claude Code installed with npm needs node too.
if command -v node > /dev/null; then CRON_PATH="$CRON_PATH:$(dirname "$(command -v node)")"; fi
CRON_PATH="$CRON_PATH:/usr/bin:/bin"
LINE="0 19 * * * cd \"$REPO\" && PATH=\"$CRON_PATH\" ${BINDAY_CLAUDE_MODEL:+BINDAY_CLAUDE_MODEL=\"$BINDAY_CLAUDE_MODEL\" }uv run python \"$CHAPTER/bin_day.py\" >> \"$CHAPTER/run.log\" 2>&1"

{ [ -n "$OTHERS" ] && echo "$OTHERS"; echo "$LINE"; } | crontab -
echo "Scheduled for 7pm every day:"
echo "  $LINE"
