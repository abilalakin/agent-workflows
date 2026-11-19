#!/usr/bin/env sh
# A fake agent for testing loop.py. It reads the prompt on stdin.
# Build step: appends a line to built.txt.
# Review step: fails the first review it sees, then passes all later ones.
# If given an argument, it is the model name. It is logged to $FAKE_MODEL_LOG.
prompt=$(cat)
[ -n "${1:-}" ] && [ -n "${FAKE_MODEL_LOG:-}" ] && echo "$1" >> "$FAKE_MODEL_LOG"
out=$(printf '%s' "$prompt" | sed -n 's/.*Write your review to: `\(.*\)`/\1/p')
if [ -z "$out" ]; then
  echo built >> built.txt
elif [ ! -f .failed-once ]; then
  touch .failed-once
  printf 'VERDICT: fail\n\n## blocking: fake finding\n' > "$out"
else
  printf 'VERDICT: pass\n' > "$out"
fi
