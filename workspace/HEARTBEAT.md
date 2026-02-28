# HEARTBEAT.md

# Qubit global heartbeat checklist
# This is autonomous mode. Do not ask conversational questions unless blocked.

1. Run: `python3 /Users/gerson/development/openclaw/workspace/skills/qubit/scripts/qubit.py --workspace /Users/gerson/development/openclaw/workspace --json due-scan`
2. If due-scan has no due actions, reply exactly: HEARTBEAT_OK
3. If due actions exist, execute due item(s) and post concise updates in the mapped Discord channels.
4. Loop prompts are only for pillars with completed onboarding and review tracking history.
