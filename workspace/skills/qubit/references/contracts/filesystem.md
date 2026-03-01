# Contract: Filesystem and State

Schema source of truth remains `../schemas.md`.

## Stability Requirements

1. Keep pillar root shape: `workspace/pillars/<status>/<pillar-slug>/`.
2. Keep required pillar files and sidecars.
3. Keep project frontmatter keys and enums stable.
4. Keep reminder and staged-message JSONL object contracts stable.
5. Keep classical-questioning sidecar/index schema stable.
6. Keep `cron/jobs.json` managed ID strategy stable.

## Mutation Constraints

1. Write only required files for the active command.
2. Preserve existing frontmatter keys when updating markdown.
3. Preserve runtime fields for existing cron jobs when upserting.
