import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { add, formatTask, type Store } from "./todo.ts";

const cli = fileURLToPath(new URL("./todo.ts", import.meta.url));

test("add assigns incrementing ids", () => {
  const data: Store = { tasks: [] };
  const a = add(data, "one");
  const b = add(data, "two");
  assert.deepEqual([a.id, b.id], [1, 2]);
  assert.equal(a.done, false);
});

test("formatTask", () => {
  assert.equal(formatTask({ id: 3, title: "x", done: true }), "[x] 3 x");
});

test("cli round trip", () => {
  const path = join(mkdtempSync(join(tmpdir(), "todo-")), "todo.json");
  const run = (...args: string[]) =>
    execFileSync(process.execPath, [cli, ...args], {
      env: { ...process.env, TODO_FILE: path },
      encoding: "utf8",
    });
  run("add", "Buy milk");
  assert.equal(run("list"), "[ ] 1 Buy milk\n");
  assert.deepEqual(JSON.parse(readFileSync(path, "utf8")), {
    tasks: [{ id: 1, title: "Buy milk", done: false }],
  });
});
