@AGENTS.md

## Claude Code specifics

- Experiment 01 uses the `Workflow` tool, read-only. Experiment 02 uses
  `Workflow` for a Ralph loop. Experiment 03 uses `SendMessage`, `ListAgents`
  and agent teams.
- Keep a workflow under 10 agents.
- Ask before calling `Workflow` or spawning a teammate. A short research
  subagent that reads docs is fine without asking.
