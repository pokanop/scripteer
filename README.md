# Scripteer

A dependency-light Python **3.11+** runtime for cohesive command-line tools.
This repository prepares the 1.6.0 framework with its compatible runtime, versioned data contracts,
an opt-in [deterministic project generator](docs/generator.md),
[offline tool/collection scaffolds](docs/scaffolds.md), and a
[verified bootstrap and transactional tool manager](docs/bootstrap.md).
Optional [BYOK AI authoring](docs/ai-proposals.md) uses explicit disclosure and
reviewed proposals; manual generation works entirely offline.

> **Scripteer** is the owner-approved name (POK-645, 2026-10-11), formerly
> Pokanop ScriptKit. Distribution, Python import and CLI are all `scripteer`.
> Version 1.6.0 is a release candidate, **not yet published to PyPI**. Follow the
> [rename, migration and publication guide](docs/scripteer-launch.md). Historical
> ScriptKit artifacts remain immutable; no affiliation with other similarly named projects is implied.

## Install a verified release

Start with [candidate installation and migration](docs/scripteer-launch.md).
[Historical v1.5.0 onboarding](docs/getting-started.md) remains available for rollback.
Then see the
[CLI/API reference](docs/cli-reference.md), [registry-author guide](docs/registry-author.md),
[generator upgrades](docs/generator-upgrades.md), [migration/rollback](docs/migration.md)
and [support matrix](docs/support.md). [Certification](docs/certification.md)
records artifact/platform/performance evidence; the [rename inventory](docs/rename-inventory.md)
keeps this provisional identity ready for the owner-approved rename.

## Build and try

```sh
python -m venv .venv
# Activate .venv using your shell's platform-specific activation command.
python -m pip install '.[dev]'
python -m build
python -m pip install dist/scripteer-1.6.0-py3-none-any.whl
scripteer --version
python -m scripteer --help
```

The `scripteer` command exposes doctor, registry/catalog, tool lifecycle and
staged manager self-update. See [bootstrap instructions](docs/bootstrap.md) for
pinned release inputs, no-PATH installation, repair and rollback. Bare invocation
shows help without modifying state; unknown commands fail with argparse exit 2.

```python
import scripteer as sk

sk.success("Ready")
result = sk.run(["git", "status", "--short"])
print(result.out)
```

There are **no mandatory runtime dependencies**, including no `requests`.
Install `.[rich]` from a checkout for optional Rich 13 rendering; without it,
plain-text output, progress, tables and diagnostics still work.

For opt-in automation-safe JSON, themes, shared progress and prompts, see
[output contracts](docs/output.md) and [customization example](examples/output.py).
Legacy helpers keep their existing behavior.

Validate authored tools with `scripteer validate PROJECT`; see
[conformance checks and installed assistant guidance](docs/conformance.md).
Optional [AI proposals](docs/ai-proposals.md) provide explicit context preview,
static review/diffs and hash-approved application, without running proposed code.
Static checks never execute project code or certify it safe.

See [runtime API](docs/runtime.md), [versioned contracts](docs/contracts.md),
[component ownership](docs/architecture.md),
[compatibility policy](docs/compatibility.md), [contributing](CONTRIBUTING.md)
and [security](SECURITY.md). MIT; attribution and extraction provenance are in
[NOTICE.md](NOTICE.md).
