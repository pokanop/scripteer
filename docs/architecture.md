# Ownership and dependency direction

Authoritative framework repository: https://github.com/pokanop/scripteer.
The runtime can be embedded in existing tools independently of the manager.

| Component / path | Ownership / dependency rule |
| --- | --- |
| Runtime: `src/scripteer/{app,blocks,cli,config,console,doctor,proc,progress,style,tables,text}.py`, `__init__.py` | Existing 1.3.0 API, dependency-light, never imports manager/registry/generator/AI. |
| Runtime IO: `safe_config.py`, `state.py`, `paths.py`, `regions.py`, `execution.py`, `_windows_job.py` | Opt-in strict/persistent/platform adapters; runtime-only imports. See [runtime IO](runtime-io.md). Composition roots inject these into upper-layer ports, except the narrow registry/manager IO edges below; no manager filesystem/sandbox semantics are implied. |
| Composition root: `entrypoint.py`, `__main__.py` | Typed `main(argv: Sequence[str] \| None) -> int` injectable argument boundary. Wires runtime, manager and authoring commands. Do not put business logic here. |
| Contracts: `scripteer.contracts` | Versioned frozen records, strict codec, resource schemas/examples and injected ports; depends only on stdlib. See [contracts](contracts.md). |
| Manager: `scripteer.manager` | Per-tool transactions, stable launchers and rollback; inject `InstallationSource` / `EnvironmentBackend`. See [installation](installation.md). CLI orchestration lives in `manager_cli.py`. |
| Registry: `scripteer.registry` | Resolution, verification/cache and `RegistryArtifactSource` port adapter; no CLI or AI dependency. |
| Generator: `scripteer.generator` | Deterministic spec-to-files logic, independent from manager and AI. |
| Conformance: `scripteer.conformance` | Static data/AST checks reuse contracts and generator ownership readers; opt-in reference fixtures use narrow output/command/execution adapters. Never imports manager, registry or AI. Installed rules/examples are provider-independent. |
| AI: `scripteer.ai` | Optional proposal/provider adapters; calls generator contracts, never imported by runtime. |

Each layer has concrete implementations behind narrow contracts. Existing typed result records
(`proc.Result`, `doctor.Check`, `blocks.ManagedBlock`) and runtime signatures remain
intact. We do not declare the whole inherited library PEP 561-complete (`py.typed`).

## Executable import graph

```text
entrypoint / __main__ (composition root)
    ├── runtime → stdlib, optional Rich
    ├── manager ────┐
    ├── registry ───┤
    ├── generator ──┼──→ contracts → stdlib
    └── AI ─────────┘
```

Conformance is an authoring-side consumer of generator ownership readers and contracts;
it never runs project imports. Its CLI/reference recipe may use only the narrow
output, command and execution runtime adapters. Runtime must never import conformance.

Other upper layers may import themselves and contracts, not one another. Cross-layer
calls use injected ports; composition roots wire concrete implementations.
The explicit exception is `registry → scripteer.state`: registry stores/cache reuse
`LocalStateIO` as a default atomic persistence adapter and accept injected `StateIO`
for testing/custom storage. No other runtime imports are allowed from registry.
Manager additionally reuses only `scripteer.state.StateConflict` and the narrow
`scripteer.execution` process-tree adapter, not runtime UI/config or providers.
These edges are encoded in `ALLOWED` and negative fixtures in the architecture test.
Registry owns `RegistryArtifactSource`, implementing `ArtifactSource` and
`InstallationSource` (including current-pin authorization) for manager consumption; composition roots bind namespace/offline policy and
inject it (see [registry](registry.md)). Runtime
does not import contracts or any upper layer. Contracts import neither runtime nor
upper layers, and load no optional package. `tests/test_architecture.py` checks
absolute/relative/static dynamic imports, rejects computed dynamic imports, tests
its own negative fixtures, and imports core behind a blocking import hook in an
isolated process. It scans the installed package too, so wheel tests enforce the
same graph. This is a regression guard, not a sandbox for malicious Python code.
Run `python -m pytest tests/test_architecture.py` to check ownership boundaries.

## Template resources

The generator ships immutable template rendering and version/checksum manifests
in `scripteer.generator.resources`. Load text via `importlib.resources.files()`; use
`as_file()` only for adapters requiring a temporary filesystem path. Never
resolve templates relative to cwd, a Git checkout or `__file__` parents.
Resources are included in wheel/sdist and exercised from installed artifacts
outside the source tree. No runtime network fetch or
AI generation may replace a missing bundled template.
