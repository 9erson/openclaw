# HEARTBEAT.md

# Qubit global heartbeat checklist
# This is autonomous mode. Do not ask conversational questions unless blocked.

1. Run: `python3 /Users/gerson/development/openclaw/workspace/skills/qubit/scripts/qubit.py --workspace /Users/gerson/development/openclaw/workspace --json due-scan`
2. If no due actions, reply exactly: HEARTBEAT_OK
3. If due actions exist, execute the highest-priority item(s) and post concise updates in the mapped Discord channels.
4. For loop prompts, ask focused questions; for reminders, issue direct alerts.
