# Scripteer

Build consistent Python command-line tools without assembling a framework from
scratch. Scripteer combines a **zero-dependency runtime**, an **offline project
generator**, and a **transactional tool manager**. Use any one on its own.

Python **3.11+** · Linux, macOS and Windows · MIT · optional Rich rendering

## What can you build?

- **Small automation scripts:** add readable messages, tables, progress, config,
  subprocess handling and predictable exit codes to existing Python code.
- **Installable team CLIs:** generate a package with commands, tests, diagnostics
  and CI, then implement your logic in handwritten handlers. Preview template
  updates without overwriting your edits.
- **A curated tool collection:** publish explicitly versioned catalogs and locked
  artifacts; install each tool in an isolated environment with stable launchers,
  update recovery and rollback.
- **Assisted authoring:** optionally ask an OpenAI or local Ollama provider for a
  proposal, inspect its context and diff, and explicitly approve application.
  No AI account or network access is needed for manual generation.

## Install

In a Python virtual environment:

```sh
python -m pip install scripteer==2.0.0
scripteer --version
scripteer --help
```

For richer terminal output, install `'scripteer[rich]==2.0.0'` instead. To use only
the standalone CLI, `pipx install scripteer==2.0.0` or
`uv tool install scripteer==2.0.0` keeps it separate from your application packages.
Library consumers must install Scripteer in the environment running their code.
See [getting started](docs/getting-started.md) for Windows activation and a complete
first-tool walkthrough; see [bootstrap](docs/bootstrap.md) for verified,
pinned manager installation without automatic PATH changes.

## Add it to an existing script

```python
import scripteer as sk

sk.header("Repository status")
result = sk.run(["git", "status", "--short"])
if result.ok:
    sk.success("Git status collected")
    print(result.out or "Working tree is clean")
else:
    sk.error(result.err)
    raise SystemExit(1)
```

Messages and progress work without Rich. Existing helpers are intentionally
simple; opt into the [structured output API](docs/output.md) when you need
machine-readable JSON, shared progress or automation-safe prompts.

## Generate your first tool

The [step-by-step tutorial](docs/getting-started.md#generate-an-installable-tool)
takes you from a JSON tool specification to an installed `hello-tool greet World`
command. Generation is offline and previews changes by default. You decide when
to apply; handwritten handlers remain yours.

```sh
# With the tutorial's tool-spec.json and an existing empty hello-tool directory:
scripteer new-tool hello-tool --spec tool-spec.json
scripteer new-tool hello-tool --spec tool-spec.json --apply
scripteer validate hello-tool
```

## Choose your next step

| Goal | Guide |
| --- | --- |
| Install, generate, implement and run a first CLI | [Getting started](docs/getting-started.md) |
| Browse by task or component | [Documentation index](docs/README.md) |
| Add config, subprocesses, tables and progress | [Runtime API](docs/runtime.md), [runtime IO](docs/runtime-io.md) |
| Emit JSON and define command results | [Output contracts](docs/output.md), [example](examples/output.py) |
| Add commands or safely upgrade generated files | [Scaffolds](docs/scaffolds.md), [generator upgrades](docs/generator-upgrades.md) |
| Distribute and manage a collection | [Registry authoring](docs/registry-author.md), [tool management](docs/tool-management.md) |
| Review AI proposals without executing them | [AI authoring](docs/ai-proposals.md) |
| Look up commands and versioned data formats | [CLI reference](docs/cli-reference.md), [contracts](docs/contracts.md) |

## Safety and support

Isolation is dependency isolation, **not a sandbox**: installed tools are Python
code running with your permissions. Trust publishers deliberately. Static
validation does not prove code safe, and hashes do not establish publisher trust.
Updates require exact versions; there is no implicit “latest” selection.

See [supported platforms](docs/support.md), [compatibility](docs/compatibility.md),
[migration](docs/scripteer-launch.md), and [security reporting](SECURITY.md).
Contributions are welcome: start with [CONTRIBUTING.md](CONTRIBUTING.md).
Attribution is preserved in [NOTICE.md](NOTICE.md) and [LICENSE](LICENSE).
