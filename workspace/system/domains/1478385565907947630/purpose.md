# #dev-ops

VPS monitoring and maintenance for meet.acutisflow.com (hosting acutisflow.com subdomains).

## Infrastructure Overview

### Reverse Proxy
- **Traefik v2.11** in Docker (`/srv/proxy/`)
- Ports: 80, 443, 8080 (dashboard)
- Dynamic configs: `/srv/proxy/dynamic_conf/`
- SSL: Let's Encrypt (auto-renewal)

### Active Services

| Service | Subdomain | Type | Port | Location |
|---------|-----------|------|------|----------|
| AcutisFlow Main | acutisflow.com | Bun (systemd) | 58247 | /var/www/acutisflow.com |
| Medi-Guide | medi-guide.acutisflow.com | Bun (systemd) | 9101 | ~/development/acutis-flow/medi-guide |
| Live-Wise | live-wise.acutisflow.com | Bun (systemd) | 9456 | ~/development/live-wise |
| PocketBase | base.acutisflow.com | Binary (systemd) | 8090 | /opt/pocketbase |
| n8n | n8n.acutisflow.com | Docker | 5678 | /srv/n8n |

### Background Jobs
- **Telegram Newsletter Sender** - Docker container, runs every 15 min
  - Location: `/srv/cron-jobs/telegram-sender/`
  - Source: `~/development/telegram-scheduler/`

### Inactive/Development Projects
- **gogcli** - Go CLI tool (not deployed, development only)
  - Location: `~/development/gogcli/`
- **Appwrite** - Installed but not running (no containers)
- **Mailu** - Config exists but not running

## Responsibilities
1. **CI/CD**
   - Deploy on request
   - Run health checks (unit tests, e2e tests)
   - Fix failing tests when possible

2. **Maintenance**
   - Monitor site health
   - Update self-hosted apps when new versions available

3. **Improvements**
   - Suggest new features and optimizations
