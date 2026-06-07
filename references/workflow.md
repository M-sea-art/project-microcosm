# Workflow

Run Project Microcosm as an advisory checker.

1. Choose mode: bootstrap, inspect, plan-change, verify, simulate, or compat-check.
2. Locate project root.
3. Apply security exclusions before reading files.
4. Build MIR observations from deterministic adapters.
5. Load accepted assertions, policies, and invariants from .microcosm/config/.
6. Run geometry checks.
7. Persist snapshots and reports under .microcosm/ only.
8. Present confirmed/probable findings separately from concerns/hypotheses.

Bootstrap must not declare the target architecture. It produces Observed, Inferred, and Proposed material. Only user-accepted Proposed constraints become Target Assertions.
