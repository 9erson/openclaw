# Dev-Ops Operations Manual

## Channel Purpose
VPS monitoring and maintenance for acutisflow.com subdomains. Unlike other channels (personal pillars), this is app management — we're teammates keeping services healthy and improving.

---

## Quiet Hours (00:00–05:00 IST)

### 1. Health Checks (one service at a time)
Run sequentially, not in parallel:
- Git sync check (custom apps)
- Build verification
- Unit tests
- Lint & typecheck
- Self-hosted version checks

Results → `reports/health-YYYY-MM-DD.json`

### 2. Feature Discovery
Scan custom apps for potential improvements:
- New feature opportunities
- UX enhancements
- Performance optimizations
- Technical debt cleanup

Results → `features/potential-features.md`

### 3. Update Checks
Check for updates to:
- n8n (Docker Hub)
- PocketBase (GitHub releases)
- Traefik (Docker Hub)

Report available updates, don't auto-install.

---

## Active Hours (05:00–00:00 IST)

### 1. Feature Discussion
Present one feature at a time from `features/potential-features.md`:
- Explain the suggestion
- Discuss and refine together
- When approved → create GitHub issue

### 2. PR Monitoring
Check for new pull requests across repos:
- `~/development/acutis-flow/medi-guide`
- `~/development/live-wise`
- `/var/www/acutisflow.com`

### 3. PR Review Offers
For unreviewed PRs:
- Offer to review
- Add constructive comments
- Summarize findings

---

## Service Management

### Systemd Services
```bash
systemctl status acutisflow live-wise medi-guide pocketbase
systemctl restart <service>
journalctl -u <service> -f
```

### Docker Services
```bash
docker ps
cd /srv/n8n && docker compose restart
cd /srv/proxy && docker compose restart
docker logs <container> -f
```

---

## Deployment Procedures

### Live-Wise
```bash
cd ~/development/live-wise && git pull && bun install && bun run build && sudo systemctl restart live-wise
```

### Medi-Guide
```bash
cd ~/development/acutis-flow/medi-guide && git pull && bun install && bun run build && sudo systemctl restart medi-guide
```

### AcutisFlow Main
```bash
cd /var/www/acutisflow.com && git pull && sudo systemctl restart acutisflow
```
