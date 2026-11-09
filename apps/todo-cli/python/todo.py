#!/usr/bin/env python3
"""Tiny to-do CLI. Stores tasks in a JSON file. Spec: ../SPEC.md"""
import argparse
import json
import os
import sys

DEFAULT_FILE = "todo.json"


def data_path():
    return os.environ.get("TODO_FILE", DEFAULT_FILE)


def load(path):
    if not os.path.exists(path):
        return {"tasks": []}
    with open(path) as f:
        return json.load(f)


def save(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def add(data, title):
    next_id = max((t["id"] for t in data["tasks"]), default=0) + 1
    task = {"id": next_id, "title": title, "done": False}
    data["tasks"].append(task)
    return task


def format_task(t):
    mark = "x" if t["done"] else " "
    return f"[{mark}] {t['id']} {t['title']}"


def main(argv=None):
    parser = argparse.ArgumentParser(prog="todo")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_add = sub.add_parser("add")
    p_add.add_argument("title")
    sub.add_parser("list")
    args = parser.parse_args(argv)

    path = data_path()
    data = load(path)
    if args.cmd == "add":
        task = add(data, args.title)
        save(path, data)
        print(format_task(task))
    elif args.cmd == "list":
        for t in data["tasks"]:
            print(format_task(t))
    return 0


if __name__ == "__main__":
    sys.exit(main())
