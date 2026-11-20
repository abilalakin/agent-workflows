#!/usr/bin/env sh
# Tests loop.py from start to finish. Run it after every change: ./tests/smoke.sh
#
# It makes a throwaway git project in a temp folder, runs the loop there with
# fake-agent.sh instead of a real agent, and checks the results. It costs
# nothing and touches no real project. It prints "smoke test ok" or "FAIL: why".
#
# What it covers, in order:
#   1. A normal run: approval gate, retry after a failed review, commits,
#      criteria and story files, context files, unrelated files left alone.
#   2. A check that never passes: the story ends up blocked.
#   3. An agent command that crashes: the loop stops, the attempt is not counted.
#   4. Models: the right model reaches each step.
#   5. A deliver step: an agent hands over each story and another reviews the
#      delivery. A failed delivery or a failed delivery review is retried.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
loop="$here/../loop.py"
export LOOP_AGENT="$here/fake-agent.sh"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
cd "$tmp"
git init -q && git config user.email test@example.com && git config user.name test
echo spec > SPEC.md && git add . && git commit -qm init
start=$(git rev-parse HEAD)

fail() { echo "FAIL: $1"; exit 1; }

echo private > my-notes.txt   # an untracked file from before the task
echo edited >> SPEC.md         # an uncommitted edit from before the task

# 1. A normal run.
printf -- '- [ ] from file one\n- from file two\n' > criteria.txt
printf '# Title with no bullets\n\n## Second story\n- one\n- two\n' > stories.md

"$loop" init demo --profile feature --check "test -f built.txt" --check "test -f SPEC.md" --context SPEC.md >/dev/null
"$loop" add demo "First story" -c "inline" --criteria-file criteria.txt >/dev/null
"$loop" add demo --from stories.md >/dev/null
"$loop" run demo >/dev/null 2>&1 && fail "ran before approval"
"$loop" approve demo >/dev/null
"$loop" run demo >/dev/null || fail "run did not finish"

board=.loop/demo/BOARD.md
grep -q '2 of 2 done' $board || fail "board does not show 2 of 2 done"
grep -q '| S1 | First story | done | 2 |' $board || fail "S1 should pass on attempt 2"
grep -q '"inline"' .loop/demo/task.json && grep -q '"from file two"' .loop/demo/task.json || fail "criteria not read"
grep -q 'Read this too: `SPEC.md`' .loop/demo/logs/S1-a1-build.prompt.md || fail "context file not in prompt"
[ "$(git rev-parse --abbrev-ref HEAD)" = loop/demo ] || fail "not on the task branch"
[ "$(git log --oneline | wc -l)" -eq 3 ] || fail "expected one commit per story"
"$loop" check demo >/dev/null || fail "checks should pass"
git log --name-only --format= "$start"..HEAD | grep -q -e my-notes.txt -e SPEC.md && fail "files changed before the task were committed"
git status --porcelain | grep -q '?? my-notes.txt' || fail "my-notes.txt should still be untracked"
git log --name-only --format= "$start"..HEAD | grep -q built.txt || fail "the story's own file was not committed"

# 2. A check that never passes.
"$loop" init stuck --profile quick --check false >/dev/null
"$loop" add stuck "Never passes" -c x >/dev/null
"$loop" approve stuck >/dev/null
"$loop" run stuck >/dev/null 2>&1 && fail "a failing check should block"
grep -q '| blocked | 2 |' .loop/stuck/BOARD.md || fail "story should be blocked after 2 attempts"

# 3. An agent command that crashes.
"$loop" init crash --profile quick --check true >/dev/null
"$loop" add crash "Agent dies" -c x >/dev/null
"$loop" approve crash >/dev/null
LOOP_AGENT="exit 3" "$loop" run crash >/dev/null 2>&1 && fail "a crashed agent should stop the loop"
grep -q '| S1 | Agent dies | todo | 0 |' .loop/crash/BOARD.md || fail "a crashed agent should not count as an attempt"

# 4. Models: the story wins, then the step, then the phase, then the default.
git switch -q -c models-test
export FAKE_MODEL_LOG="$tmp/models.log"
"$loop" init models --profile feature --check true --model small --model build=big --model review-simplicity=mid >/dev/null
"$loop" add models "Normal story" -c x >/dev/null
"$loop" add models "Hard story" -c x --model huge >/dev/null
"$loop" approve models >/dev/null
"$loop" run models --agent "$here/fake-agent.sh {model}" >/dev/null || fail "models run did not finish"
[ "$(tr '\n' ' ' < "$FAKE_MODEL_LOG")" = "big small mid huge huge huge " ] || fail "wrong models: $(tr '\n' ' ' < "$FAKE_MODEL_LOG")"
unset FAKE_MODEL_LOG
LOOP_PLAN_AGENT='printf "%s|%s" {model} {prompt} > plan-out.txt' "$loop" plan models plan-stories --start
grep -q '^small|# Plan 4: stories' plan-out.txt || fail "plan --start did not pass the model and prompt"
rm plan-out.txt

# 5. A deliver step: an agent hands over each story, and a failed delivery is retried.
"$loop" init handover --profile quick --check true --deliver deliver-pr >/dev/null
"$loop" add handover "One" -c x >/dev/null
"$loop" approve handover >/dev/null
FAKE_SKIP_DELIVER=1 "$loop" run handover >/dev/null 2>&1 && fail "a delivery with no commit should stop the loop"
grep -q '| S1 | One | done |' .loop/handover/BOARD.md || fail "the story itself should still be done"
before=$(git rev-parse HEAD)
rm -f .failed-once   # make the next review, the delivery review, fail once
"$loop" run handover >/dev/null || fail "the delivery retry did not finish"
[ "$(git rev-parse HEAD)" != "$before" ] || fail "the retry should have committed"
grep -q 'delivered https://example.test/pr/1' .loop/handover/BOARD.md || fail "the PR link should be on the board"
grep -q 'review-delivery fail' .loop/handover/progress.md || fail "the delivery review should fail once"
grep -q 'review-delivery pass' .loop/handover/progress.md || fail "the delivery review should pass after the fix"
grep -q 'fix every blocking finding' .loop/handover/logs/S1-a1-deliver-pr.prompt.md || fail "the second delivery should get the review findings"
grep -q 'Title for the commit and the PR' .loop/handover/logs/S1-a1-deliver-pr.prompt.md || fail "deliver prompt lacks the title"

echo "smoke test ok"
