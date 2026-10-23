# End-to-end release certification

This gate certifies the current **Scripteer** candidate end to end, not a PyPI
launch. No publishing credentials, Trusted Publisher, repository variable or
release asset is changed. Scripteer was selected by the owner on 2026-10-11;
publication remains independently human-approved. Independent exact-head review
and applicable QA are separate acceptance gates; author-run tests do not
replace them. Their verdicts and exact CI run/head belong in the handoff, not a
self-issued approval in this document.

## Reproduce

From an environment provisioned with `.[dev]`, git and Python:

```sh
python tools/certify_release.py --output certification
```

The runner certifies only artifacts built from the current checkout:

1. Builds the sdist and wheel from the exact working tree, writes a SHA256SUMS
   manifest and verifies exact manifest membership and every artifact digest
   (fail closed on extra, missing or tampered files), then runs
   `twine check --strict` over both artifacts.
2. Extracts the sdist (regular files only, links/devices rejected) and checks
   its metadata — distribution, version and entry point — against the current
   `pyproject.toml`.
3. Installs the wheel into a clean venv outside the source checkout and runs
   the full installed suite, examples and installers via
   `tools/check_artifact.py`, once bare and once with the optional Rich extra,
   with imports checked against the venv prefix. Installed resources,
   POSIX/PowerShell bootstrap, registry consent, tool lifecycle, failures,
   interruption, recovery and AI fixture boundaries are exercised. The
   `test_authored_tool_release_journey` lifecycle (installed manager → offline
   scaffold → handwritten handler → fixture-backed AI disclosure/review/apply →
   two built wheels → explicit catalog trust → install/update/rollback/uninstall)
   runs inside that suite with real pip environments and launchers.
4. Rebuilds the wheel from the extracted sdist outside the checkout, compares
   every package file against the directly built wheel (including
   template/contract/assistant resources), installs the rebuilt wheel into
   another clean venv offline and smokes help/version/resources.

`certification.json` is written even on failure (`complete: false`); only a true
completion plus green job represents a pass. JUnit `framework.xml` is uploaded by
each of the three required CI jobs. The existing 12-cell Python/OS runtime matrix
still runs both bare and Rich installed-artifact tests. `required-quality` fails
closed if any matrix or prerequisite is skipped, cancelled or failed.

## Scope after pre-rename release removal (POK-696)

The historical baseline journey — attested pre-rename release download, legacy
manager bootstrap/rollback against it, cross-generation performance comparison
and the pinned consumer rehearsal — was retired when the owner removed the
pre-rename GitHub releases; its pins and historical onboarding were removed with
them. Certification therefore compares the candidate against itself
(sdist↔wheel parity, offline rebuild, clean-room installs) rather than against a
downloaded baseline. Migration and rollback behavior for existing pre-rename
installations remains covered by the head test suite and the compatibility
identities documented in [scripteer-launch.md](scripteer-launch.md); the
coordinated consumer update reintroduces consumer rehearsal against a published
Scripteer release.

Network is required only for build-tool and test dependency provisioning.
Authoring and the deterministic tool registry journey are offline. All provider
behavior is synthetic; real secrets/data never enter CI.

## Performance method and budgets

`tools/benchmark.py` records OS/architecture/Python, all wall-clock samples and
medians: five fresh-process interpreter/import/help samples, five fresh-project
render+preview+transaction generations, and five real pip installations of the
same tiny wheel. There is no automatic retry-until-pass. The checked-in
[Linux reference](performance-linux.json) was measured from the pre-rename 1.5.0
wheel on CPython 3.13.5 x86_64: interpreter ~5 ms, import ~25 ms, help ~61 ms,
generation ~5 ms, installer ~1.39 s. It is reproducible evidence, not a universal
target for Windows/macOS. When comparing a candidate against any verified
baseline on the same OS/Python runner, every median must stay below
**2× baseline + 100 ms**, or **2× baseline + 2 s** for pip installation, with the
absolute hang/user latency ceilings of 1 s interpreter/import, 2 s help/generation
and 60 s install. Investigate failures and fix regressions; do not silently
increase budgets.

## Evidence limitations

See [support matrix](support.md) and [threat model](security-certification.md).
Three hosted OS families are not all architectures/filesystems. The
original six-tool GPU/service-dependent suite is not universally portable; this
gate runs collection transaction and generated-tool flows, not credentialed
application behavior. Windows untrusted arguments must not pass through `.cmd`
wrappers. Runtime-only 1.3.0 compatibility remains covered separately. Main
merge protection remains the owner's accepted procedural control; this gate
does not claim to restore technical branch protection.
