#!/usr/bin/env sh
# The full gate for a story: Python tests, TypeScript typecheck + tests, then compat.
set -eu
cd "$(dirname "$0")"
echo "== python"
(cd python && python3 -m unittest)
echo "== typescript"
[ -d typescript/node_modules ] || (cd typescript && npm ci --no-fund --no-audit)
(cd typescript && npm run --silent check)
echo "== compat"
./check-compat.sh
