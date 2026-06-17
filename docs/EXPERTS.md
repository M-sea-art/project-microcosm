# Expert Decision Model

Project Microcosm uses expert areas to keep time-compressed software
evolution decisions reviewable. The labels below are role names; map
them to real GitHub users or teams in `CODEOWNERS` when maintainers are
assigned.

## Temporal Microcosm Architect

Owns the core purpose: current state, projected future state,
verification path, and the `State / Event / Transition / Snapshot /
Forecast` model. A change is done when delayed software-evolution risk
is visible before or immediately after a change lands.

## Causal Chain Expert

Owns downstream consequence reasoning. Reviews dependency paths,
required mediation paths, undeclared edges, cycles, and any change
where one action can create later structural risk.

## Scenario Rehearsal Expert

Owns `plan-change` behavior. Reviews whether a proposed change creates
clear projected findings, minimum safe next steps, and post-change
verification points.

## State Snapshot Expert

Owns `.microcosm/snapshots/`, state summaries, baseline selection, and
single-writer/state-persistence conflicts. A snapshot must clearly
represent history, current state, target state, or rollback evidence.

## Evidence and Confidence Expert

Owns schemas, validation, evidence levels, confidence bands, stable
finding IDs, and forecast certainty. Low-confidence projections must
remain hypotheses.

## Risk Visibility Expert

Owns deferred consequence language, risk scoring, blast radius,
irreversibility, external dependency risk, and "what gets expensive if
we wait" guidance.

## Human-Agent Decision Expert

Owns human approval boundaries and agent handoff decisions. Agent
governance remains an application of time compression: agents act fast,
so their future risks must become visible early.

## Supporting Areas

- Adapter integration remains necessary because missing adapters hide
  parts of the timeline.
- CI and release engineering remains necessary because tags, releases,
  and PR checks are timeline states.
- Test fixture curation remains necessary because every temporal claim
  needs a reproducible before/after scenario.
- Developer experience remains necessary because reports must be
  understandable by both humans and agents.
