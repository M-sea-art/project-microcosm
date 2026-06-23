# Project Microcosm

Temporal microcosm for the smallest fastest feasible implementation path.

Start with the full project guide:

- [Project overview](docs/README.md)
- [Always-on agent rules](AGENTS.md)
- [Contributing](docs/CONTRIBUTING.md)
- [Expert ownership model](docs/EXPERTS.md)
- [Security policy](docs/SECURITY.md)
- [Changelog](docs/CHANGELOG.md)

Quick check:

```powershell
python scripts/microcosm.py inspect --project .
```

Project Microcosm is advisory by default: it compresses structure
exploration, deep decision-making, projected future state, findings,
risk, and machine-readable next actions into the shortest feasible
path; it does not modify source code or enforce merges.

The main artifact is
`.microcosm/reports/<run-id>/temporal-report.json`, especially
`forecast.smallest_fastest_path`. It turns structural exploration into
a path decision, then uses verify to prove the selected path landed.
