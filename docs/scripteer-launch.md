# Installation and identity migration

The distribution, Python import and console command are all `scripteer`.
Version **2.0.0** is the first published release under this identity. See
[getting started](getting-started.md) for a complete tutorial.

```sh
python -m pip install scripteer==2.0.0
```

For standalone CLI installation, use `pipx install scripteer==2.0.0` or
`uv tool install scripteer==2.0.0`. Library users need the package in their
application's environment. Verified manager bootstrap is documented in
[bootstrap](bootstrap.md); maintainers should use the [release runbook](RELEASING.md).

## Migrating pre-release installations

Scripteer makes an explicit identity break from pre-rename development builds.
There are no legacy import aliases. Old environment variables, home-directory
names, receipts, keyring services, region markers and schema identifiers are not
automatically migrated. Nothing is moved, copied or deleted for you.

- Update application imports and dependency declarations to `scripteer`.
  Public runtime return semantics are described in [compatibility](compatibility.md).
- Root precedence is `--root`, then `SCRIPTEER_ROOT`, then `~/.scripteer`.
  To adopt old tool data, explicitly choose the old root or move the directory
  yourself after backing it up.
- Manager receipts accept `module: scripteer` only. Re-run the independently
  verified current bootstrap against your chosen root. Foreign commands and
  user-modified launchers are not overwritten. Keep old environments separate
  if you still need to run them.
- `self-rollback` and bootstrap `--rollback` work between compatible Scripteer
  generations, not across the rename boundary. Keep independently verified old
  bootstrap/wheel inputs if you need to restore a pre-release installation;
  retired pre-rename GitHub assets are no longer available.
- Optional keyring access uses service `scripteer.ai` and account `openai`.
  `OPENAI_API_KEY` takes precedence. Re-save credentials manually; no secret is
  copied or deleted during migration.
- Managed-region markers, `.scripteer-lock`, `.scripteer-generator` and
  `urn:scripteer:contracts:*:1` use the current identity. Do not edit receipts
  or rename control directories to trick the new tooling into accepting them.

## Generated projects

Current scaffolds use template **3.0.0**. Projects produced by the supported v1
renderer can preview and apply an explicit migration:

```sh
scripteer template-upgrade PROJECT
scripteer template-upgrade PROJECT --apply
scripteer validate PROJECT
```

Commit or back up the entire project first. Upgrades replace only hash-matching
owned files; handwritten handlers, docs, config, tests and CI are preserved.
Modified generated files require manual reconciliation, not force overwrite.
See [generator upgrades](generator-upgrades.md).

Projects created before the identity change are not recognized. Generate into a
fresh directory and copy your handwritten handlers, initializers, docs, config,
tests and CI across deliberately. Update handwritten imports and dependency
metadata, but never blanket-replace secrets or local configuration. Rebuild any
pending AI proposals against the new project hashes.

## Collection consumers

When migrating a collection, advance imports, compatible dependency ranges,
wheel URLs and SHA-256 pins together. Publish and independently verify the new
artifacts before referencing them. Rehearse install, update, rollback and removal
with a separate root, retaining verified recovery inputs. Historical signatures
and hashes must never be mechanically renamed or replaced.
