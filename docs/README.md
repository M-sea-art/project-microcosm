# Project Microcosm

> **Temporal microcosm for the smallest fastest feasible implementation path.**

Project Microcosm compresses slow implementation time: it helps humans
and agents find the smallest, fastest feasible path before a software,
agent, or skill project gets dragged into a cumbersome execution flow.
It does this through structural exploration, deep decision-making,
current state, projected future state, and a verification path. It
models the project **horizontally** (structural topology) and
**vertically** (state evolution) as a typed, evidence-backed
intermediate representation (MIR), then answers the questions ordinary
code graphs avoid:

- Should this edge exist?
- Who is allowed to traverse it?
- When is it open, and when does it close?
- Did the change introduce or resolve a violation?
- What is the evidence, and how strong is it?

> **v0.1.0-beta.1** — read this `Status` section before you wire it into
> anything that touches production decisions.

![Status](https://img.shields.io/badge/status-v0.1--beta-orange)
![Mode](https://img.shields.io/badge/mode-advisory-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-Apache--2.0-green)

## What Project Microcosm Is

A deterministic, **advisory** checker that:

1. Scans a project with explicit, switchable adapters.
2. Builds a typed MIR: nodes, edges, observations, assertions,
   policies, evidence, findings.
3. Runs geometry invariants against the MIR and against
   `.microcosm/config/{invariants,assertions,policies}.{json,yaml}`.
4. Emits one Finding set, then renders machine (`findings.json`,
   `next-actions.json`, `temporal-report.json`) and human
   (`summary.md`) reports from the same data.
5. Tracks pre-change and post-change state with stable finding ids so
   "resolved / new / still open" actually means something.

## What Project Microcosm Is Not

- Not a code writer. It does not modify source files.
- Not a CI blocker. It does not commit, push, or block.
- Not a permission grant. It does not request broader access.
- Not a runtime monitor. V0.1 has no trace ingestion.
- Not a replacement for code review, tests, or human judgment.

## Operating Principles

1. **Observe before changing.** Never treat the current structure as
   the intended structure.
2. **Separate the layers.** Observation is what exists; assertion is
   what should exist; policy is what is allowed; evidence is why we
   believe any of it.
3. **Mark inferences as inferences.** Heuristics produce Inferred
   nodes; only Accepted Proposed constraints become Target
   Assertions.
4. **Minimum useful graph resolution.** L0/L1 by default, L2 for
   module inspection, L3 only for local fault isolation.
5. **Advisory by default.** The kernel reports; the agent or human
   decides.
6. **Every Finding carries evidence.** A finding without
   `evidence_refs` is forced to band `hypothesis` and severity `low`.

## Quick Start

Requires Python 3.10+. No third-party dependencies.

```powershell
# Bootstrap a project: discover observed/inferred/proposed structure
python scripts/microcosm.py bootstrap --project <repo>

# Static structural check against accepted invariants
python scripts/microcosm.py inspect --project <repo>

# Pre-change structural rehearsal from a change plan
python scripts/microcosm.py plan-change --project <repo> --plan change-plan.yaml

# Post-change comparison against a baseline snapshot
python scripts/microcosm.py verify --project <repo> --against run-xxxx

# Direct Scenario DSL execution is unavailable; temporal reports come from inspect/plan-change/verify
python scripts/microcosm.py simulate --project <repo>

# Check skill/platform packaging compatibility
python scripts/microcosm.py compat-check --project <repo>
```

`PYTHONPATH` must include the `scripts` directory (or install via
`pip install -e .` once `pyproject.toml` is configured for your
environment).

## Modes

| Mode             | Purpose                                                         |
| ---------------- | --------------------------------------------------------------- |
| `bootstrap`      | First run. Discovers structure, drafts `.microcosm/`.          |
| `inspect`        | Static check against accepted assertions / policies / invariants. |
| `plan-change`    | Preview structural consequences before writing code.            |
| `verify`         | Compare current run against a previous snapshot, prove no drift. |
| `simulate`       | Direct Scenario DSL execution is unavailable in V0.1.           |
| `compat-check`   | Verify skill packaging compatibility.                           |

## Output Contract

Every run writes under `<project>/.microcosm/reports/<run-id>/`:

| File                  | Audience | Purpose                                |
| --------------------- | -------- | -------------------------------------- |
| `summary.md`          | Humans   | Decision, temporal judgment, risk, queue, evidence summary. |
| `findings.json`       | Agents   | Stable finding ids, category, severity, evidence_refs. |
| `validation.json`     | Humans + Agents | MIR validator issues + schema-mismatch findings. |
| `queue-eligibility.json` | Agents | Confirmed / probable / concern / hypothesis / schema_mismatch buckets. |
| `next-actions.json`   | Agents   | Prioritized next actions with owner expert and recommended mode. |
| `temporal-report.json` | Humans + Agents | Current/projected states, events, transitions, smallest fastest path, forecast, expert judgment. |
| `unresolved.json`     | Humans   | Known unanalyzable regions.            |
| `geometry-diff.json`  | Agents   | Pre/post node + edge + finding diff (verify only). |
| `manifest.json`       | Both     | Decision, file list, versions.         |

Plus:

- `.microcosm/snapshots/<run-id>.json` — full MIR snapshot.
- `.microcosm/mir/current.json` — last run's MIR.

## Geometry Invariants (V0.1)

| Operator            | Meaning                                                       |
| ------------------- | ------------------------------------------------------------- |
| `forbidden-edge`    | A given edge must not appear in observations.                |
| `required-path`     | Path from A to C must traverse required nodes.                |
| `single-writer`     | A persistent state allows only declared writers.              |
| `no-cycle`          | Selected relations must form a DAG.                          |
| `max-fanout`        | Direct outbound relation count is bounded.                   |
| `permission-subset` | Observed capabilities must not exceed declared permissions.   |

## Trust Layer

Beyond geometric checks, the trust layer enforces:

- **MIR validation** with strict enums for node kinds, edge relations,
  policy decisions, evidence levels, finding categories, severities, and
  bands. Invalid values produce a `schema-mismatch` finding and a
  `validation.json` issue list.
- **Stable finding ids** derived from
  `category + subject_ref + normalized(expected, actual)`. The
  `verify` mode re-normalizes legacy baselines on the fly.
- **Confidence bands**:
  `confirmed (>=0.85)`, `probable (>=0.60)`, `concern (>=0.30)`,
  `hypothesis (<0.30)`.
- **Decision** per run: `PASS` / `WARN` / `FAIL` / `UNAVAILABLE`.
- **Risk scoring** for structural impact, state persistence,
  permission change, irreversibility, external dependency, uncertainty.
- **Queue eligibility** buckets machine-actionable vs. observe-only vs.
  investigate findings.

## Status: What Works, What Doesn't

### Implemented in V0.1-beta

- Bootstrap, inspect, plan-change, verify.
- Six geometry invariants.
- Trust validation, decision, risk, queue eligibility.
- Acceptance fixtures (capability, verify, plan-change, trust).
- Stable finding ids and post-change diff.
- Schema versioning with strict enums.
- Machine-readable next actions for agent handoff.
- Deterministic temporal reports for inspect, plan-change, and verify.
- Basic Agent Skills and MCP config adapters.

### Explicitly Not Implemented Yet

- Direct Scenario DSL execution (`simulate` is not a scenario runner).
- Runtime trace ingestion and E4 evidence.
- Deep adapter coverage (Codex, HMS, OpenClaw, and CodeGraph are
  stubs; Agent Skills and MCP config support is intentionally shallow).
- CI enforcement or commit blocking.
- Automatic repair.
- CodeGraph deep integration.

## Safety

- Does not execute repository code (no `postinstall`, no `setup.py`, no
  scanner binary from the repo).
- Does not read known secret paths (`.env`, `*.pem`, `*.key`, SSH dirs,
  system key stores, browser credentials, `node_modules`, build caches,
  `.git/objects`).
- Does not write outside `.microcosm/`.
- Does not request broader permissions automatically. If a region is
  unavailable, the kernel lowers confidence and reports it rather than
  escalating.

## Tests

```powershell
python -m compileall -q scripts tests

python tests/run_acceptance.py
python tests/run_verify_acceptance.py
python tests/run_plan_acceptance.py
python tests/run_trust_acceptance.py

python -m unittest discover -v tests/unit
```

The acceptance scripts exercise end-to-end flows against committed
fixtures under `tests/fixtures/`.

## Repository Layout

```
project-microcosm/
├── SKILL.md
├── LICENSE
├── pyproject.toml
├── .gitignore
│
├── docs/                        # Human-facing project documentation
│   ├── README.md
│   ├── CHANGELOG.md
│   ├── CONTRIBUTING.md
│   ├── EXPERTS.md
│   └── SECURITY.md
│
├── references/                  # Engineering references for the skill
│
├── schemas/                     # JSON schemas for MIR objects
│
├── templates/                   # starter config files
│
├── scripts/
│   ├── microcosm.py             # CLI entry point
│   └── microcosm/
│       ├── cli.py
│       ├── bootstrap.py
│       ├── config.py            # invariants/assertions/policies loaders
│       ├── discover.py
│       ├── diff.py
│       ├── evidence.py
│       ├── findings.py
│       ├── normalize.py
│       ├── plan_change.py
│       ├── reporting.py
│       ├── validate.py          # MIR validator
│       ├── verify.py
│       ├── versioning.py
│       ├── geometry/
│       ├── temporal/            # placeholder
│       └── adapters/
│
├── tests/
│   ├── unit/
│   ├── fixtures/
│   ├── run_acceptance.py
│   ├── run_verify_acceptance.py
│   ├── run_plan_acceptance.py
│   └── run_trust_acceptance.py
│
└── tools/
    ├── skills_compat_check.py
    └── migrate_schema.py
```

## Contributing

See `docs/CONTRIBUTING.md` for development setup, the merge checklist, and
the fixture discipline. New invariants and new adapters must ship with
a fixture under `tests/fixtures/`.

## License

Apache License 2.0. See `LICENSE`.
