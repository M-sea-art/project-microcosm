# Expert Ownership Model

Project Microcosm uses expert areas to keep agent-facing changes
reviewable. The labels below are role names; map them to real GitHub
users or teams in `CODEOWNERS` when maintainers are assigned.

## Agent Runtime Architect

Owns `SKILL.md`, workflow references, CLI mode contracts, and agent
trigger behavior. A change is done when an agent can decide when to run
the skill, which mode to use, and which output file to consume without
extra interpretation.

## Safety and Permissions Expert

Owns filesystem traversal, secret exclusions, write boundaries, and
no-execution guarantees. Any adapter change requires this review.

## MIR and Evidence Schema Expert

Owns schemas, validation, evidence resolution, confidence bands, and
stable finding IDs. Schema and finding changes must preserve explicit
migration behavior.

## Adapter Integration Expert

Owns scanners under `scripts/microcosm/adapters/`. Adapters must be
read-only, deterministic, and covered by fixtures.

## Geometry and Invariant Expert

Owns geometry operators and invariant references. New invariants need
positive and negative fixtures plus stable finding IDs.

## CI and Release Engineer

Owns GitHub Actions, packaging, tags, changelog entries, and release
artifacts. Tags should point at the tested commit.

## Test Fixture Curator

Owns fixture shape and idempotent acceptance runs. Tests may generate
ignored reports and snapshots, but must restore tracked fixture files.

## Developer Experience Expert

Owns GitHub entry points, quickstart, examples, and public docs. A new
user should be able to install, inspect, and interpret results quickly.
