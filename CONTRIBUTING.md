# Contributing

Use Python 3.11 or newer and an isolated environment. From the repository root:

```sh
python -m venv .venv
# Activate the environment for your shell before continuing.
python -m pip install -e '.[dev,rich]'
python -m ruff check .
python -m ruff format --check src tests tools
python -m pytest
python -m mypy
python -m build
python tools/check_artifact.py dist/scripteer-2.0.0-py3-none-any.whl
python tools/check_artifact.py dist/scripteer-2.0.0-py3-none-any.whl --rich
```

Build tooling/test dependencies need package-index access; runtime smoke operations
are local. Tests do not require provider keys. Never commit credentials or local
venvs. Test the installed wheel, not only editable imports. New runtime code must
include success/failure/interruption tests as applicable; new code should achieve
at least 90% changed-line coverage and cover critical recovery/security branches.
CI enforces 90% changed-line coverage across the framework, the documented platform/Python
matrix, static checks, dependency auditing, clean release rehearsals, and
three-OS [verified-release certification](docs/certification.md). See the
[quality and release contract](docs/quality-and-release.md) for required gates,
explicit legacy typing/formatting debt, provenance, and owner publishing setup.

Keep typed boundaries narrow and inject argv/IO/platform/provider dependencies.
Follow [ownership](docs/architecture.md) and [SemVer](docs/compatibility.md).
Do not update the API snapshot simply to make a breaking change pass. Explain
intentional differences in the PR, preserve MIT notices, and avoid consumer-only
dependencies. No fake manager/generator implementations in the composition root.

Submit a focused PR with test evidence. Rebase on main (never merge main into
feature branches), require current-head green CI and independent review before
merging. Publication is a separate maintainer operation; follow the
[release runbook](docs/RELEASING.md).

Write docs and commit summaries for public readers: explain behavior and rationale,
not private task identifiers, internal conversations or development orchestration.
Preserve licensing, attribution and verifiable security/release evidence. For new
user-facing features, include a runnable example and update the
[documentation index](docs/README.md).
Keep the repository free of pre-rename identifiers:
`tests/test_rename.py` enforces this repository-wide, so any identity-bearing edit
must keep that test green. Conformance/assistant rules are shipped in installed
resources; see [authoring guidance](docs/conformance.md).
