# Getting started

This walkthrough builds a small installable greeting CLI. You need Python 3.11+
with pip and venv. Package installation needs access to a package index;
scaffold generation itself does not access the network.

## Install in an isolated environment

```sh
python -m venv .venv
```

Activate it with `source .venv/bin/activate` on POSIX shells, or
`.venv\Scripts\Activate.ps1` in PowerShell. If your shell calls Python `python3`,
use that for the first command. Activation is optional: you can instead invoke
`.venv/bin/python` or `.venv\Scripts\python.exe` directly.

```sh
python -m pip install scripteer==2.0.0
python -m scripteer --version
python -m scripteer --help
```

Expect version `2.0.0` and a list of manager and authoring commands. Bare
`scripteer` shows help and does not install anything. Optional terminal rendering
is available with `python -m pip install 'scripteer[rich]==2.0.0'`.

## Generate an installable tool

Save this as `tool-spec.json` in your working directory (outside the new project):

```json
{
  "schema_version": 1,
  "name": "hello-tool",
  "version": "1.0.0",
  "description": "A friendly first CLI",
  "entrypoint": "hello_tool.cli:main",
  "python": {"minimum": "3.11.0", "maximum_exclusive": "3.15.0"},
  "platforms": [{"os": "linux", "arch": "x86_64"}],
  "commands": [{
    "schema_version": 1,
    "name": "greet",
    "help": "Greet someone by name",
    "arguments": [{
      "schema_version": 1,
      "name": "name",
      "kind": "positional",
      "value_type": "string",
      "required": true,
      "default": null,
      "choices": [],
      "help": "Person to greet"
    }]
  }]
}
```

The platform list declares the tool's distribution targets, not all framework
platforms. This example declares Linux x86_64; before distributing on other
platforms, update it to your tested targets using the
[contract platform vocabulary](contracts.md). Local generation is platform-independent.
The entrypoint must be `package.module:function`.

```sh
mkdir hello-tool
scripteer new-tool hello-tool --spec tool-spec.json
```

The first command previews file names and diffs without writing the scaffold.
Inspect it, then apply:

```sh
scripteer new-tool hello-tool --spec tool-spec.json --apply
```

The result includes:

| Location | Purpose |
| --- | --- |
| `src/hello_tool/cli.py` | Generated entrypoint and command wiring |
| `src/hello_tool/_handlers.py` | Your handwritten behavior |
| `tool.json` | Generated, validated tool specification |
| `pyproject.toml` | Package metadata and console entrypoint |
| `tests/`, `.github/` | Starter tests and CI |
| `README.md`, `AUTHORING.md` | Project-specific usage and ownership guidance |
| `.scripteer-generator/` | Ownership hashes and transaction state; retain this |

## Implement the command

Open `hello-tool/src/hello_tool/_handlers.py` and replace the placeholder `run`
function with:

```python
def run(command, arguments):
    if command == "greet":
        return {"message": f"Hello, {arguments['name']}!"}
    raise NotImplementedError(command)
```

The runtime passes the selected command name and parsed arguments to `run`. Returning data lets the scaffold runtime
render it for humans or put it in the JSON envelope. Handlers may also return
integer exit codes or a `CommandResult`; see [scaffolds](scaffolds.md).
Place your logic here, not in the generated entrypoint. Placeholder handlers
intentionally fail until implemented.

```sh
python -m pip install -e ./hello-tool
hello-tool --help
hello-tool greet World
hello-tool --json greet World
hello-tool doctor
scripteer validate hello-tool
```

The greeting contains `Hello, World!`; JSON output has `ok: true` and the greeting
in `data`. Global flags precede the subcommand. `doctor` is read-only; static
`validate` checks conventions and generated-file drift without importing your code.
It is not a substitute for tests or security review.

## Add a command and keep edits safe

Save `command-spec.json` next to the original specification:

```json
{"schema_version":1,"name":"status","help":"Show tool status","arguments":[]}
```

```sh
scripteer add-command hello-tool --spec command-spec.json
scripteer add-command hello-tool --spec command-spec.json --apply
```

Add a `status` branch to `run` in `_handlers.py` yourself, before the final
`raise`; existing handwritten files are preserved:

```python
    if command == "status":
        return {"status": "ready"}
```
Commit the project before upgrades. `scripteer template-upgrade hello-tool`
previews a supported template update; `--apply` writes it and `--check` checks
for drift. Modified generated files cause conflicts rather than force overwrites.
See [upgrade/recovery guidance](generator-upgrades.md).

## Package and share

```sh
python -m pip install build
python -m build hello-tool
```

This produces a wheel and source archive in `hello-tool/dist/`. Install the wheel
in a fresh environment to verify its commands independently of your checkout.
Generated projects pin the generating Scripteer version; dependency installation
may contact a package index unless you supply a complete local wheelhouse.

For a curated collection with verified artifacts and isolated tool installs,
continue with [tool management](tool-management.md) and
[registry authoring](registry-author.md). You do not need a registry to use a
normal wheel with pip or pipx.

## Common first-run problems

- **Command not found:** activate the environment where you installed the package.
  `python -m scripteer` also avoids a missing console-script PATH entry.
- **Project directory missing:** create it first; generation does not create the
  target root for you.
- **Spec rejected:** use schema version 1, a package-qualified entrypoint, and
  supported [contract values](contracts.md). `doctor` and `config` are reserved
  command names; `command`, `config` and `json` are reserved argument names.
- **Handler not implemented:** replace the placeholder in `_handlers.py`, not
  the generated CLI. New commands need branches in `run` too.
- **Drift/conflict:** restore or reconcile generated files using version control
  and preview again. Do not delete ownership state to bypass the check.
- **Configuration:** generated tools accept a JSON object with
  `hello-tool --config settings.json greet World`; handlers receive it at
  `arguments["config"]`. Never commit secrets or print them through `config`.

For configuration persistence, subprocess cancellation and platform paths see
[runtime IO](runtime-io.md); for consistent human/JSON output see [output](output.md).
