import json
import os
import subprocess
import sys
import tempfile
import unittest

import todo


class AddListTests(unittest.TestCase):
    def test_add_assigns_incrementing_ids(self):
        data = {"tasks": []}
        a = todo.add(data, "one")
        b = todo.add(data, "two")
        self.assertEqual((a["id"], b["id"]), (1, 2))
        self.assertFalse(a["done"])

    def test_format_task(self):
        self.assertEqual(todo.format_task({"id": 3, "title": "x", "done": True}), "[x] 3 x")

    def test_cli_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "todo.json")
            env = {**os.environ, "TODO_FILE": path}

            def run(*args):
                out = subprocess.run(
                    [sys.executable, todo.__file__, *args],
                    env=env, capture_output=True, text=True, check=True,
                )
                return out.stdout

            run("add", "Buy milk")
            self.assertEqual(run("list"), "[ ] 1 Buy milk\n")
            with open(path) as f:
                self.assertEqual(
                    json.load(f),
                    {"tasks": [{"id": 1, "title": "Buy milk", "done": False}]},
                )


if __name__ == "__main__":
    unittest.main()
