# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## Timezone Doctrine

- **System time** = UTC (internal operations, due checks, scheduling logic)
- **User-facing time** = Asia/Kolkata (timestamps shown to Gerson)
- **Due checks** = UTC only (never compare against local time)
- **User-visible timestamps** = Always Asia/Kolkata (format: `[Day YYYY-MM-DD HH:MM IST]`)
- **Scheduled items** = Store both UTC and IST timestamps

---

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
