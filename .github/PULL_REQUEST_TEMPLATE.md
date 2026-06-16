## What

Describe the user-facing or agent-facing change.

## Why

Explain the structural, safety, or developer-experience reason.

## Expert Areas

- [ ] Agent Runtime Architect
- [ ] Safety and Permissions Expert
- [ ] MIR and Evidence Schema Expert
- [ ] Adapter Integration Expert
- [ ] Geometry and Invariant Expert
- [ ] CI and Release Engineer
- [ ] Test Fixture Curator
- [ ] Developer Experience Expert

## Validation

- [ ] `python -m compileall -q scripts tests`
- [ ] `python scripts/microcosm.py compat-check --project .`
- [ ] `python tests/run_acceptance.py`
- [ ] `python tests/run_verify_acceptance.py`
- [ ] `python tests/run_plan_acceptance.py`
- [ ] `python tests/run_trust_acceptance.py`
- [ ] `python -m unittest discover -v tests/unit`

## Safety

- [ ] No repository code execution added.
- [ ] No writes outside `.microcosm/`.
- [ ] Secret and generated paths remain excluded.
- [ ] New adapter behavior is covered by fixtures or unit tests.
