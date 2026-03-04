#!/bin/bash
# Prune ops.log to last 30 days
# Run: nightly via cron

OPS_LOG="/root/.openclaw/workspace/system/ops.log"
DAYS=30

if [ -f "$OPS_LOG" ]; then
    # Get cutoff timestamp (30 days ago)
    CUTOFF=$(date -d "$DAYS days ago" +%s 2>/dev/null || date -v-${DAYS}d +%s)
    
    # Filter lines within cutoff
    TMP_FILE=$(mktemp)
    while IFS= read -r line; do
        # Extract timestamp from line [Tue 2026-03-03 04:13 UTC]
        if [[ $line =~ \[[A-Za-z]+\ ([0-9]{4}-[0-9]{2}-[0-9]{2})\ ([0-9]{2}:[0-9]{2})\ UTC\] ]]; then
            LINE_DATE="${BASH_REMATCH[1]}"
            LINE_TS=$(date -d "$LINE_DATE" +%s 2>/dev/null || date -j -f "%Y-%m-%d" "$LINE_DATE" +%s)
            if [ "$LINE_TS" -ge "$CUTOFF" ]; then
                echo "$line" >> "$TMP_FILE"
            fi
        else
            # Keep lines without timestamps (shouldn't happen, but safe)
            echo "$line" >> "$TMP_FILE"
        fi
    done < "$OPS_LOG"
    
    mv "$TMP_FILE" "$OPS_LOG"
    echo "[$(date -u '+%a %Y-%m-%d %H:%M UTC')] ops.log pruned to $DAYS days" >> "$OPS_LOG"
fi
