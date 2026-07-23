---
name: managing-backlog-issues
description: Use when working with Backlog issues across one or more projects, including parent-child tracking, assignees, statuses, dates, comments, member notifications, local attachments, mentions, or possible unreplied messages.
---

# Managing Backlog Issues

## Core contract

Read current Backlog state first. Before every write, show the exact space,
project, target, fields, comment, recipients, and attachments. Wait for
approval, execute only that proposal, then re-read the result. An explicit
approval of the immediately preceding proposal is sufficient.

## Local configuration

Keep configuration outside this skill:

- `BACKLOG_DOMAIN`
- `BACKLOG_API_KEY`
- `BACKLOG_DEFAULT_PROJECT_KEY` (optional)

Never print, copy, commit, or store credential values. Read only the optional
default project key when project selection requires it. Do not persist project
lists; live Backlog state is authoritative.

## Resolve project and identity

1. Select the configured Backlog organization without hard-coding a space.
2. Fetch the authenticated user and their current project list.
3. Resolve the target in this order:
   - a project key or name explicitly stated in the request;
   - `BACKLOG_DEFAULT_PROJECT_KEY`;
   - user selection from the live project list.
4. Match keys exactly. Match names only when exactly one current project has
   that name. Stop on missing, inaccessible, archived-only, or ambiguous
   targets.
5. Confirm that the authenticated user is a current member of the selected
   project.
6. Read issue types, categories, priorities, project users, statuses, and
   relevant issues before proposing IDs or values.
7. Discover status IDs from current project issues with the matching status
   name. Stop if the desired status cannot be resolved.
8. Treat issue type and category as different fields. Ask which one the user
   means when a label such as "tag" is ambiguous.

## Issue and reply operations

- Search issues created by any member within the selected project.
- Treat a parent as a theme or deliverable and a child as a team-visible work
  item.
- For a new parent or child issue, default the assignee to the authenticated
  user. An explicit request for another assignee or no assignee overrides this.
  Stop if the authenticated user is not a project member.
- Do not change the assignee of an existing issue unless explicitly requested.
- Manage content, parent, assignee, status, dates, category, issue type,
  priority, and comments. Leave unknown users and dates unset.
- Read notifications without changing them. A reply candidate has another user
  as the latest relevant commenter and no later comment by the authenticated
  user. Show the chronology and label this as a heuristic.
- Classify items as `返信候補`, `相手待ち`, `対応済み`, or `情報共有`.
- Mark notifications read only when explicitly requested.

## Notifications

Use `notifiedUserId` as Backlog's mention and notification mechanism. Resolve
each recipient from live users in the selected project and show display names
before posting. Stop on ambiguous names. Never infer recipients from assignees
or participants. Verify returned notifications instead of assuming delivery.
Backlog can suppress self-notifications; do not use one as proof that another
member was notified.

## Comments and attachments

Keep comments to the conclusion or status, requested decision, next action, and
attachment summary. Put background, investigation, logs, evidence, findings,
and unresolved questions in Markdown. Use ZIP for artifact bundles.

For each existing or generated file:

1. Run `python3 scripts/upload_attachment.py inspect FILE`.
2. Show path, name, type, size, SHA-256, ZIP members, complete generated
   Markdown, exact comment, target, and recipients.
3. After approval, load the user's existing Backlog environment and run
   `python3 scripts/upload_attachment.py upload FILE --expected-sha256 DIGEST`.
4. Immediately pass the returned ID to the approved issue or comment write.
5. Re-read and verify attachment name and size.

If inspection blocks a sensitive filename or ZIP member, require a sanitized
replacement. If association fails after upload, report the unattached temporary
upload.

## Boundaries

Never create, update, archive, or delete projects. Never delete issues or use
Wiki, document, Git, or pull-request writes. Do not generate weekly reviews or
maintain estimated or actual hours. Never guess IDs, identities, projects, or
dates.
