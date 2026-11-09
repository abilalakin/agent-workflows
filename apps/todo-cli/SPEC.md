# Toy app: to-do CLI

One spec, two implementations. `python/todo.py` (Python 3, stdlib only) and
`typescript/todo.ts` (TypeScript on Node 24). Both read and write the same JSON
file, so a file written by one must work with the other.

## Data file

Path: `$TODO_FILE`, default `todo.json` in the current folder.

```json
{
  "tasks": [
    { "id": 1, "title": "Buy milk", "done": false }
  ]
}
```

Rules:
- `id` is an integer, starting at 1. Ids are never reused. S1 may use `max(id) + 1`;
  S3 must switch to a stored counter so a removed id is not handed out again.
- New fields added by later stories must be optional. Old files must still load.
- Both implementations must write the same JSON for the same commands.

## Output format

One task per line: `[ ] 1 Buy milk` for open, `[x] 1 Buy milk` for done.

## How to run

Python (from `python/`):

```sh
python3 -m unittest -v
python3 todo.py add "Buy milk"
```

TypeScript (from `typescript/`, run `npm install` once):

```sh
npm run check          # typecheck + tests
node todo.ts add "Buy milk"
```

Everything (from this folder):

```sh
./check.sh             # both test suites, then check-compat.sh
```

## Stories

Each story applies to both implementations. A story is done when its tests pass
in both languages and `check-compat.sh` still passes.

### S1. Add and list (done, template)

- `add <title>` appends a task and prints it.
- `list` prints all tasks in id order.

### S2. Mark done

- `done <id>` sets `done` to true and prints the task.
- Unknown id: print `no task <id>` to stderr, exit code 1.
- `done` on an already done task is fine and prints it.

### S3. Remove

- `remove <id>` deletes the task. Prints nothing. Exit code 0.
- Unknown id: `no task <id>` on stderr, exit code 1.
- Ids are not reused: after removing 3 of [1,2,3], the next add gets id 4.

### S4. Due dates

- `add <title> --due YYYY-MM-DD` stores `"due": "YYYY-MM-DD"`.
- `list` shows the due date after the title: `[ ] 1 Buy milk (due 2026-11-10)`.
- `list --overdue` shows only open tasks with a due date before today.
- Tasks without `due` still load and list.

### S5. Priority

- `add <title> --priority low|normal|high` stores `"priority"`. Default `normal`
  when the flag is given without a value is not allowed; omit the field if the
  flag is not used.
- `list` sorts high, then normal, then low, then by id. Missing priority counts
  as normal.
- `list` shows `!` before the title for high: `[ ] 1 ! Call bank`.

### S6. Clear done

- `clear` removes all done tasks and prints `removed N`.
- Ids are not reused.
