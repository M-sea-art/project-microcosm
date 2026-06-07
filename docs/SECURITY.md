# Security Policy

Project Microcosm is an **advisory, read-only** structural cognition
kernel. It does not modify project source code, does not execute
repository scripts, and does not request broader permissions than what
its caller provides.

## Reporting a Vulnerability

Please report security issues **privately** through the repository's
Security tab using GitHub private vulnerability reporting. Do not file
a public issue until a fix is available.

If you are unsure whether something is a vulnerability, treat it as one
and report privately.

## What to Include

1. Affected component (mode, adapter, schema, or report file).
2. Reproduction steps, ideally a fixture under `tests/fixtures/`.
3. Observed behavior vs. expected behavior.
4. Whether the issue can be triggered with the default safety
   exclusions or requires custom configuration.

## Threat Model

Project Microcosm processes:

- Local source files and configuration (read-only).
- User-supplied JSON / YAML (`invariants`, `assertions`, `policies`,
  `change-plan`).
- Run-time produced JSON output under `.microcosm/`.

It must never:

- Execute code from the scanned project.
- Write outside `.microcosm/`.
- Read known sensitive paths (`.env`, SSH keys, system key stores,
  browser credentials).
- Auto-escalate its own permissions.

## Built-in Exclusions

| Path pattern         | Why                                 |
| -------------------- | ----------------------------------- |
| `.env`               | Environment secrets                 |
| `*.pem`, `*.key`, `*.p12` | Cryptographic material         |
| `~/.ssh/`            | SSH credentials                     |
| `node_modules/`      | Untrusted vendor code (skip scan)   |
| `.git/objects/`      | Binary object database              |
| Build cache dirs     | Generated content                   |

## Schema Versioning

`mir/v0.x` schemas may evolve. Incompatible baselines must be rejected
by `verify` rather than silently re-interpreted. See
`references/migration-policy.md`.
