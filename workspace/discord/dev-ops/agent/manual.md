# Manual - #dev-ops

**Current Mode:** Infrastructure Stabilization & Monitoring Setup

## Active Focus Areas

### Immediate
- acutisflow.com — fixed (2026-03-03)
- Baseline health checks for all 5 services — needs execution
- Update monitoring for self-hosted apps

### Services to Monitor
- acutisflow.com (Docker)
- PocketBase instances
- n8n automation
- (2 other services TBD)

## Patterns Observed

1. **Docker networking:** Port exposure requires explicit UFW rules for external access
2. **Self-hosted apps:** Need recurring update checks (not just one-time)
3. **Questions that surface needs:** "Which app to prioritize?" → reveals priority/traffic info

## Strategy

- Focus on proactive monitoring setup before issues occur
- Establish update cadence for self-hosted apps
- Document all services and their criticality levels

## Next Angle Ideas

- Automated health check scripts (cron-based)
- Alert notification setup (Discord/email)
- Backup strategy for each service
- Security audit checklist

---

_Updated: 2026-03-03 (Quiet Hours - Domain Setup)_
