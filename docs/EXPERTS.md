# Expert Decision Model

Project Microcosm uses expert areas to compress slow implementation
work into the smallest, fastest feasible path. The labels below are
role names; map them to real GitHub users or teams in `CODEOWNERS` when
maintainers are assigned.

## Time Compression Architect

Owns the core purpose: shorten the path from "what should we build?" to
"what is the smallest safe next move?" A change is done when the report
reduces execution drag instead of merely describing risk.

## Minimum Path Expert

Owns `smallest_fastest_path` in `temporal-report.json`. Reviews whether
the proposed path can be applied as-is, must be split, needs a narrow
fix, or should stop at a human decision gate.

## Structural Probe Expert

Owns structural exploration before execution. Reviews whether the model
has enough observed structure to avoid guessing, overbuilding, or
starting a broad execution flow too early.

## Deep Decision Expert

Owns wisdom-depth and confidence. Reviews whether weak evidence stays
as hypothesis, whether a decision is actually supported, and whether
more structure must be inspected before action.

## Causal Chain Expert

Owns downstream consequence reasoning. Reviews dependency paths,
required mediation paths, undeclared edges, cycles, and any action that
can create delayed structural cost.

## Scenario Rehearsal Expert

Owns `plan-change` behavior. Reviews whether a proposed change can be
rehearsed into a direct path: apply, split, fix, or reject before
source code is touched.

## State Snapshot Expert

Owns `.microcosm/snapshots/`, state summaries, baseline selection, and
single-writer/state-persistence conflicts. A snapshot must represent
history, current state, target state, or rollback evidence.

## Flow Simplification Expert

Owns the removal of unnecessary process. Reviews whether the output
avoids broad rewrites, open-ended execution, and manual multi-step
loops when one narrow plan and one verification pass can prove the
path.

## Risk Visibility Expert

Owns deferred consequence language, risk scoring, blast radius,
irreversibility, external dependency risk, and "what gets expensive if
we wait" guidance.

## Human-Agent Decision Expert

Owns human approval boundaries and agent handoff decisions. Agent and
skill work are high-frequency applications of time compression: they
move fast, so wrong paths become expensive quickly.

## Supporting Areas

- Adapter integration matters because missing adapters hide structure
  and force slow guessing.
- CI and release engineering matters because tags, releases, and PR
  checks are timeline states.
- Test fixture curation matters because every path decision needs a
  reproducible before/after scenario.
- Developer experience matters because the shortest path must be clear
  enough for humans and agents to act on immediately.
