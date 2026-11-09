#!/usr/bin/env sh
# Python writes, TypeScript reads. Then the other way round. Both must agree.
set -eu
cd "$(dirname "$0")"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

export TODO_FILE="$tmp/a.json"
python3 python/todo.py add "From python" >/dev/null
node typescript/todo.ts add "From ts" >/dev/null
py=$(python3 python/todo.py list)
ts=$(node typescript/todo.ts list)
[ "$py" = "$ts" ] || { echo "MISMATCH"; echo "python:"; echo "$py"; echo "ts:"; echo "$ts"; exit 1; }

export TODO_FILE="$tmp/b.json"
node typescript/todo.ts add "From ts" >/dev/null
python3 python/todo.py add "From python" >/dev/null
py=$(python3 python/todo.py list)
ts=$(node typescript/todo.ts list)
[ "$py" = "$ts" ] || { echo "MISMATCH"; echo "python:"; echo "$py"; echo "ts:"; echo "$ts"; exit 1; }

echo "compat ok"
echo "$ts"
