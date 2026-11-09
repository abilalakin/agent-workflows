#!/usr/bin/env node
// Tiny to-do CLI. Stores tasks in a JSON file. Spec: ../SPEC.md
import { existsSync, readFileSync, writeFileSync } from "node:fs";

export type Task = { id: number; title: string; done: boolean };
export type Store = { tasks: Task[] };

export function dataPath(): string {
  return process.env.TODO_FILE ?? "todo.json";
}

export function load(path: string): Store {
  if (!existsSync(path)) return { tasks: [] };
  return JSON.parse(readFileSync(path, "utf8")) as Store;
}

export function save(path: string, data: Store): void {
  writeFileSync(path, JSON.stringify(data, null, 2) + "\n");
}

export function add(data: Store, title: string): Task {
  const nextId = Math.max(0, ...data.tasks.map((t) => t.id)) + 1;
  const task: Task = { id: nextId, title, done: false };
  data.tasks.push(task);
  return task;
}

export function formatTask(t: Task): string {
  return `[${t.done ? "x" : " "}] ${t.id} ${t.title}`;
}

export function main(argv: string[]): number {
  const [cmd, ...rest] = argv;
  const path = dataPath();
  const data = load(path);

  if (cmd === "add" && rest[0] !== undefined) {
    const task = add(data, rest[0]);
    save(path, data);
    console.log(formatTask(task));
    return 0;
  }
  if (cmd === "list") {
    for (const t of data.tasks) console.log(formatTask(t));
    return 0;
  }
  console.error("usage: todo add <title> | todo list");
  return 2;
}

if (import.meta.main) process.exit(main(process.argv.slice(2)));
