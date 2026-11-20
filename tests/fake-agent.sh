#!/usr/bin/env sh
# A stand-in for a real agent, so loop.py can be tested for free.
#
# It reads the prompt on stdin, like a real agent would, and then:
#   - build prompt:   adds a line to built.txt, as if it wrote code.
#   - review prompt:  writes the review file named in the prompt.
#                     The first review ever fails, all later ones pass.
#                     That lets the test cover the retry path.
#   - deliver prompt: commits built.txt and writes a fake PR link.
#                     With FAKE_SKIP_DELIVER set, it does nothing instead.
#
# Optional argument: a model name. It is appended to $FAKE_MODEL_LOG, so the
# test can see which model the loop asked for.

prompt=$(cat)
[ -n "${1:-}" ] && [ -n "${FAKE_MODEL_LOG:-}" ] && echo "$1" >> "$FAKE_MODEL_LOG"
path_after() { printf '%s' "$prompt" | sed -n "s/.*$1: \`\([^\`]*\)\`.*/\1/p"; }
review=$(path_after "Write your review to")
result=$(path_after "Delivery result file")
if [ -n "$result" ] && [ -z "$review" ]; then
  [ -n "${FAKE_SKIP_DELIVER:-}" ] && exit 0
  git add built.txt && git commit -q --allow-empty -m "fake delivery" && echo "https://example.test/pr/1" > "$result"
elif [ -z "$review" ]; then
  echo built >> built.txt
elif [ ! -f .failed-once ]; then
  touch .failed-once
  printf 'VERDICT: fail\n\n## blocking: fake finding\n' > "$review"
else
  printf 'VERDICT: pass\n' > "$review"
fi
