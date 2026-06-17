# Changelog

All notable changes to Project Microcosm are documented in this file.
The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with the pre-release tag conventions described below.

## [Unreleased]

### Added

- Root `README.md` for GitHub and agent discoverability.
- `docs/EXPERTS.md` with practical expert ownership areas.
- GitHub `CODEOWNERS`, pull request template, and issue templates.
- `next-actions.json` report output and `manifest.json.next_actions`
  for machine-readable agent handoff.
- Basic read-only `agent-skills` and `mcp-config` adapters.
- `temporal-report.json` for inspect, plan-change, and verify runs.
- Minimal deterministic temporal model: State, Event, Transition,
  Snapshot, and Forecast.
- Temporal expert decision model centered on smallest-fastest feasible
  implementation paths.

### Changed

- GitHub Actions now runs `compat-check` against the repository root
  and uploads its JSON output as a workflow artifact.
- Project positioning now centers on compressing slow implementation
  flows into the smallest, fastest feasible path.
- `plan-change` now emits projected future findings, deferred
  consequences, minimum safe next steps, smallest-fastest path, and
  verification points.
- `verify` now emits observed timeline transitions and marks
  unpredicted new findings when no prior forecast exists.
- `next-actions.json` now includes temporal pressure and deferred
  consequence fields.

## [0.1.0-beta.1] - 2026-06-07

First public beta. Project Microcosm enters GitHub as an advisory,
read-only structural cognition kernel. It is not yet a production
governance tool, but the geometry kernel, trust layer, and CLI loop
are complete and accepted by automated fixtures.

### Added

- Skill entry point `SKILL.md` discoverable by Mavis, Codex, HMS, OpenClaw agents.
- CLI modes: `bootstrap`, `inspect`, `plan-change`, `verify`, `simulate`, `compat-check`.
- MIR (Microcosm Intermediate Representation) with strictly-typed Node,
  Edge, Assertion, Observation, Policy, Evidence, and Finding objects.
- Six geometry invariants:
  `forbidden-edge`, `required-path`, `single-writer`, `no-cycle`,
  `max-fanout`, `permission-subset`.
- Adapters: generic repository, Python AST imports, Node/TS imports,
  fixture edges. Stubs reserved for Codex, HMS, OpenClaw, CodeGraph,
  agent skills, and MCP config.
- Trust layer:
  - MIR validator (enum, id uniqueness, subject/evidence resolution).
  - Stable finding id via `category + subject_ref + normalized expected/actual` hash.
  - `validation.json` per run with issue list and schema-mismatch findings.
  - Decision (`PASS` / `WARN` / `FAIL` / `UNAVAILABLE`) and risk scoring.
  - Queue eligibility for confirmed / probable / concern / hypothesis findings.
- `plan-change` pre-flight that previews structural consequences from
  `change-plan.yaml` without mutating the project.
- `verify` post-change comparison against the latest baseline snapshot
  (or a specific run id) with stable id matching and `geometry-diff.json`.
- `simulate` placeholder that explicitly returns
  `Temporal engine is not available in this release.`
- Acceptance fixtures:
  capability (3), verify (3), plan-change (4), trust (4 + 7 unit tests).
- Schema validation, JSON schema files with strict `additionalProperties: false`.
- Lifecycle of `.microcosm/`: `meta/`, `config/`, `mir/`, `snapshots/`,
  `traces/`, `evidence/`, `reports/<run-id>/`.

### Limited / Not Implemented

- Temporal engine (Event, State, Transition, Tick, Trace, Scenario DSL).
- Runtime trace ingestion and E4 evidence.
- CodeGraph deep integration (only placeholder adapter).
- Codex / HMS / OpenClaw platform adapters (stubs only).
- CI enforcement or automatic repair.
- Policy / assertion deep reasoning beyond reading user-supplied JSON.

### Security

- Default read-only. None of the CLI modes modify project source code.
- Default path exclusions: `.env`, `*.pem`, `*.key`, `*.p12`, SSH dirs,
  system key stores, `node_modules`, build caches, `.git/objects`,
  large binaries.
- No repository code is executed (no `postinstall`, `setup.py`, or
  scanner binaries from the scanned project).
- Output is restricted to `.microcosm/`.

### Known Constraints

- `parse_simple_yaml` supports a small V0.1 subset of YAML; for complex
  configurations prefer JSON.
- Adapters for agent skills, MCP, and platform-specific layouts are
  placeholders and report `unavailable`.
- `verify` relies on `stable_finding_id` to compare findings across
  runs; old baseline snapshots with pre-trust ids are still accepted
  and re-normalized on the fly.
