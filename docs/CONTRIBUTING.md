# Contributing to Project Microcosm

Thanks for the interest. This is a small, opinionated kernel. Most
contributions fall into one of these categories:

- New geometry invariant.
- New adapter (scan more of a project).
- New finding category or trust rule.
- Documentation and example fixtures.

## Setup

```powershell
git clone https://github.com/M-sea-art/project-microcosm.git
cd project-microcosm

# All standard tests are run from repo root with PYTHONPATH set.
$env:PYTHONPATH = "$PWD\scripts"
python -m compileall -q scripts tests

# Run the full acceptance + unit test suite.
python tests/run_acceptance.py
python tests/run_verify_acceptance.py
python tests/run_plan_acceptance.py
python tests/run_trust_acceptance.py

python -m unittest discover -v tests/unit
```

The kernel is pure-Python 3.10+ and depends on the standard library
only. Do not introduce third-party dependencies without prior
discussion.

## Workflow

1. Fork and create a feature branch.
2. Add or update a fixture under `tests/fixtures/<your-case>/` with:
   - `edges.microcosm.json` (or a real source tree for adapter work).
   - `.microcosm/config/invariants.json` when the case is about an
     invariant.
   - `.microcosm/snapshots/run-baseline.json` when the case is about
     `verify`.
3. Add an acceptance case to one of:
   - `tests/run_acceptance.py` (capability)
   - `tests/run_verify_acceptance.py` (verify)
   - `tests/run_plan_acceptance.py` (plan-change)
   - `tests/run_trust_acceptance.py` (trust)
   - `tests/unit/test_*.py` (kernel unit)
4. Run the full suite locally. Every case must remain green.
5. Open a pull request.

## Design Rules

- A finding **must** have `evidence_refs` that resolve to evidence in
  the same MIR, except for `band=hypothesis, severity<=low`.
- Do not mark Inferred facts as Verified. They go into the
  `bootstrap-inferred.json` draft and must be Proposed by the user
  before they become Target Assertions.
- New invariants belong in
  `scripts/microcosm/geometry/operators.py` and must be wired into
  `scripts/microcosm/geometry/engine.py`.
- New adapters go in `scripts/microcosm/adapters/`. They must be
  deterministic: identical project state must produce identical MIR.
- Adapters must not execute repository code. They may read files.
- Adapters must skip secret paths (see `references/security-policy.md`).

## Stable Finding IDs

Finding ids are deterministic: `finding.<category>.<sha1_8>`. Do not
introduce run-local counters. The category must come from
`FINDING_CATEGORIES` in `validate.py`.

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat: add required-path evidence_ref enrichment`
- `fix(cli): reject plan against missing file`
- `test(trust): cover evidence demotion`

## Security

See `docs/SECURITY.md`. Never disclose a real-world vulnerability in a
public issue before a fix is available.
