#!/usr/bin/env sh
# End to end test of loop.py with the fake agent, in a throwaway git project.
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

"$loop" init stuck --profile quick --check false >/dev/null
"$loop" add stuck "Never passes" -c x >/dev/null
"$loop" approve stuck >/dev/null
"$loop" run stuck >/dev/null 2>&1 && fail "a failing check should block"
grep -q '| blocked | 2 |' .loop/stuck/BOARD.md || fail "story should be blocked after 2 attempts"

"$loop" init crash --profile quick --check true >/dev/null
"$loop" add crash "Agent dies" -c x >/dev/null
"$loop" approve crash >/dev/null
LOOP_AGENT="exit 3" "$loop" run crash >/dev/null 2>&1 && fail "a crashed agent should stop the loop"
grep -q '| S1 | Agent dies | todo | 0 |' .loop/crash/BOARD.md || fail "a crashed agent should not count as an attempt"

# Models: the story wins, then the step, then the phase, then the default.
git switch -q -c models-test
export FAKE_MODEL_LOG="$tmp/models.log"
"$loop" init models --profile feature --check true --model small --model build=big --model review-quality=mid >/dev/null
"$loop" add models "Normal story" -c x >/dev/null
"$loop" add models "Hard story" -c x --model huge >/dev/null
"$loop" approve models >/dev/null
"$loop" run models --agent "$here/fake-agent.sh {model}" >/dev/null || fail "models run did not finish"
[ "$(tr '\n' ' ' < "$FAKE_MODEL_LOG")" = "big small mid small huge huge huge huge " ] || fail "wrong models: $(tr '\n' ' ' < "$FAKE_MODEL_LOG")"
unset FAKE_MODEL_LOG
LOOP_PLAN_AGENT='printf "%s|%s" {model} {prompt} > plan-out.txt' "$loop" plan models plan-stories --start
grep -q '^small|# Plan 4: stories' plan-out.txt || fail "plan --start did not pass the model and prompt"
rm plan-out.txt

# PR mode: a branch and a PR per story, each stacked on the one before.
git init -q --bare "$tmp/remote.git" && git remote add origin "$tmp/remote.git"
git switch -q -c pr-base
"$loop" init prs --profile quick --check true --pr >/dev/null
"$loop" add prs "One" -c x >/dev/null
"$loop" add prs "Two" -c y >/dev/null
python3 - <<'PY'
import json
p = ".loop/prs/task.json"; t = json.load(open(p))
t["prCommand"] = "echo https://example.test/pr/{branch}/onto/{base}"
json.dump(t, open(p, "w"), indent=2)
PY
"$loop" approve prs >/dev/null
"$loop" run prs >/dev/null || fail "pr run did not finish"
git --git-dir="$tmp/remote.git" branch | grep -q 'loop/prs/S1' || fail "S1 branch not pushed"
git --git-dir="$tmp/remote.git" branch | grep -q 'loop/prs/S2' || fail "S2 branch not pushed"
grep -q 'PR https://example.test/pr/loop/prs/S1/onto/pr-base' .loop/prs/BOARD.md || fail "S1 PR should target the starting branch"
grep -q 'PR https://example.test/pr/loop/prs/S2/onto/loop/prs/S1' .loop/prs/BOARD.md || fail "S2 PR should target the S1 branch"
[ "$(git log --oneline loop/prs/S1..loop/prs/S2 | wc -l)" -eq 1 ] || fail "S2 should be one commit on top of S1"

echo "smoke test ok"
