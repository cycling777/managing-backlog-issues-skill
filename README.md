# Managing Backlog Issues Skill

A Codex skill for safely managing issues across the Backlog projects available
to the authenticated user.

## Prerequisites

- Codex CLI
- Python 3.10 or newer
- Node.js and `npx` for the Backlog MCP server
- A personal Backlog API key
- Access to the Backlog projects you intend to manage

The attachment helper uses only the Python standard library. No Python package
installation is required.

## Install the skill

Clone this repository into your personal Codex skills directory:

```bash
git clone <repository-url> "${CODEX_HOME:-$HOME/.codex}/skills/managing-backlog-issues"
```

Restart Codex CLI after installing or updating the skill.

## Configure Backlog locally

Store your own values outside the repository:

```bash
BACKLOG_DOMAIN=your-space.backlog.com
BACKLOG_API_KEY=replace-with-your-own-api-key
BACKLOG_DEFAULT_PROJECT_KEY=OPTIONAL_PROJECT_KEY
```

`BACKLOG_DEFAULT_PROJECT_KEY` is optional. An explicitly requested project takes
priority, and the skill verifies the selection against your current project
list.

Protect the environment file so only your local user can read it:

```bash
chmod 600 "$HOME/.backlog-mcp.env"
```

Register the Backlog MCP server with Codex using an organization-approved
server command. The command must export `BACKLOG_DOMAIN` and
`BACKLOG_API_KEY` to the MCP process.

## Check the local setup

From the installed skill directory, verify Python and the attachment helper:

```bash
python3 -c 'import sys; assert sys.version_info >= (3, 10), sys.version'
python3 scripts/upload_attachment.py --help
```

Verify that Codex sees the Backlog MCP server:

```bash
codex mcp list
```

Start a new Codex CLI session and request a read-only verification:

```text
Use $managing-backlog-issues to perform a read-only setup check. Identify the
authenticated Backlog user and list the current projects. Do not write, update,
upload, or mark notifications as read.
```

## Security

- Never commit `.backlog-mcp.env`, `.env`, API keys, or other credentials.
- Never copy another person's API key.
- Keep organization domains, real project keys, issue data, and personal
  identifiers out of this repository.
- Review the exact project, issue, fields, comment, recipients, and attachments
  before approving a Backlog write.
