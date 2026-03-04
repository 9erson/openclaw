# Timezone Doctrine

This document expands on the rules in `TOOLS.md`. Read both.

## Rules

| Context | Timezone | Why |
|---------|----------|-----|
| System time | UTC | Universal, no DST, unambiguous |
| User-facing time | Asia/Kolkata (IST) | Gerson's local context |
| Due checks | UTC only | Avoids DST edge cases |
| Scheduled items | Store both | Enables accurate comparisons and readable display |

## Why UTC for Due Checks

- **No DST ambiguity** — IST doesn't observe DST, but UTC is still the canonical standard
- **Unambiguous comparison** — `now_utc >= due_utc` is always correct
- **Portable across systems** — Works regardless of server timezone shifts
- **Log correlation** — System logs are UTC; due checks should match

**Never** compare a stored local time against "now" — DST transitions can cause off-by-one-hour bugs or duplicate/missed checks.

## Why IST for User Messaging

- **Cognitive ease** — Gerson thinks in IST. "3pm" means 3pm Kolkata.
- **Actionable context** — "Meeting at 14:30 IST" is immediately useful
- **Reduced translation burden** — No mental math required

**Always** display times in IST when showing timestamps to Gerson.

## Storage Format

All scheduled items must store **both** timestamps:

```json
{
  "due_utc": "2026-03-02T12:00:00Z",
  "due_ist": "2026-03-02T17:30:00+05:30",
  "display": "Mon 2026-03-02 17:30 IST"
}
```

This enables:
- Accurate due checks using `due_utc`
- Readable display using `due_ist` or `display`

## Conversion Examples

**UTC to IST:**
```
UTC:  2026-03-02 05:44
IST:  2026-03-02 11:14 (+5:30)
```

**IST to UTC:**
```
IST:  2026-03-02 17:30
UTC:  2026-03-02 12:00 (-5:30)
```

## Display Format

User-visible timestamps use this format:
```
[Mon 2026-03-02 17:30 IST]
```

Short, clear, unambiguous.

---

This document reinforces `TOOLS.md`. When in doubt, refer to both.
