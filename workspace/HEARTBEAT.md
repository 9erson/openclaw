# HEARTBEAT.md

# ⚠️ RARELY USED — Most scheduled tasks go to system/queue.jsonl
#
# This file is for MINIMAL periodic checks during heartbeat polls only.
#
# DEFAULTS:
# - "Remind me X" → system/queue.jsonl (scheduled messages)
# - "Check health", "update orchestrator" → discord/<channel>/agent/policy.md
# - "Create cron job" → explicit request only (very rare)
#
# This file should stay mostly empty to reduce token burn.

# Keep this file empty (or with only comments) to skip heartbeat API calls.

# Add tasks below when you want the agent to check something periodically.
