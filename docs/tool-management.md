# Manage a collection of tools

The manager is useful when you need a curated collection with exact releases,
verified artifacts and isolated per-tool environments. For a single ordinary
Python CLI, pipx or uv may be sufficient. Scripteer does not discover publishers
or install a default collection for you.

## Choose the manager root

Install the CLI as described in [getting started](getting-started.md), or use
[verified bootstrap](bootstrap.md) for a separately managed manager generation.
State defaults to `~/.scripteer`. An explicit global `--root PATH` overrides
`SCRIPTEER_ROOT`, which overrides that default. Use a local private directory.

```sh
scripteer doctor
scripteer registry list
```

`doctor` reports interpreter, manager/root and PATH health without repairing
anything. For a separate trial root, pass `--root ./trial-root` **before** the
subcommand on every invocation. Installation does not silently edit your PATH;
use launchers under the selected root's `bin` directory or add that directory
to PATH yourself.

## Trust a publisher explicitly

Obtain a registry JSON file from a publisher you trust and verify its origin and
pins through an independent channel. The following is a command pattern, not a
live example registry; replace the file, origin and qualified release with the
publisher's real values:

```sh
scripteer registry add registry.json --trust-origin https://tools.example.org/releases/
scripteer catalog team
scripteer install team/report-tool@1.0.0 --dry-run
scripteer install team/report-tool@1.0.0
```

The namespace (`team`) comes from the registry contract. Exact origin consent,
catalog hashes, expiration, tool compatibility and dependency locks are checked.
A dry run resolves a plan without activation; it can still fetch metadata/artifacts.
Installing runs trusted package/tool code with your permissions: a virtual
environment is not a security sandbox.

For publishers, [registry authoring](registry-author.md) explains how to create
real catalog artifacts, hashes and locks. Do not substitute invented hashes or
placeholder download URLs into a usable registry.

## Update, roll back and remove

```sh
scripteer update team/report-tool@1.1.0 --dry-run
scripteer update team/report-tool@1.1.0
scripteer rollback report-tool
scripteer uninstall report-tool
```

Updates stage and smoke-test a new generation before switching stable launchers.
Rollback selects the retained, verified previous generation; it does not fetch
an arbitrary old version. Uninstall removes owned launchers but retains tool
data, config and generations. It is not a full disk purge. See
[retention and cleanup](installation.md) before removing retained state.

Removing trust with `scripteer registry remove team` prevents future resolution
but does not uninstall existing tools.

## Offline use and interrupted operations

`catalog`, `install` and `update` accept `--offline`. This uses previously
verified cached inputs; it does not waive expiry, trust or hash checks. Missing
cache entries fail rather than falling back to the network. Provision the
required artifacts before disconnecting.

If an installation is interrupted, inspect diagnostics and run:

```sh
scripteer recover report-tool
scripteer doctor
```

An error after activation can mean the new generation is already committed.
Do not delete journals or blindly reinstall to hide the failure. Recovery
replays pending state transitions; [installation](installation.md) documents
receipts, failure boundaries and manual retention policy.

Tool rollback and manager rollback are separate. `self-update` needs an exact
manager wheel URL, SHA-256 and version; `self-rollback` restores a retained manager
from a bootstrap-managed installation. See [bootstrap](bootstrap.md).

## Automate safely

Global flags precede the subcommand:

```sh
scripteer --json catalog team
scripteer --json install team/report-tool@1.0.0 --dry-run
```

Parse the versioned [output envelope](output.md), not human progress text.
Check both the exit status and `ok`: 0 is success, 1 a domain failure, 2 invalid
usage and 130 interruption. Never put secrets into catalogs or diagnostic reports.
