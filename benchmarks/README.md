# Project Microcosm Benchmarks

Benchmarks are evidence for time compression, not marketing claims.
Each case should show whether Microcosm helped avoid a slower path,
choose a smaller path, or prove that execution landed safely.

## Metrics

- Seeded structural violations detected.
- False positives avoided.
- Stable finding ids across plan/verify.
- `smallest_fastest_path.decision` matched expected outcome.
- Cumbersome flow avoided by compressed steps.

## First Pass

The initial benchmark skeleton uses committed fixture metadata only.
Larger agent-session benchmarks should be added after the path decisions
are stable enough to compare against a baseline workflow.
