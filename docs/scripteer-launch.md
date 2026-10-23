# Scripteer: identity, migration and human-controlled launch

Sahel selected **Scripteer** on POK-645 on 2026-10-11. Repository:
<https://github.com/pokanop/scripteer>. Distribution, import and command are all
`scripteer`. Candidate version **1.6.0** continues the framework's version lineage.
This document does **not** claim a published PyPI release. No final merge or release
is automatically authorized. The POK-614 delivery controller was deleted before
naming research; it must not be recreated to merge this work.

## Try the candidate without a nonexistent index/release pin

From the reviewed checkout, with Python 3.11+ and build tooling installed:

```sh
python -m build
python -m venv candidate-env
candidate-env/bin/python -m pip install --no-index dist/scripteer-1.6.0-py3-none-any.whl
candidate-env/bin/python -m scripteer --version
candidate-env/bin/python -m scripteer --help
```

On Windows use `candidate-env/Scripts/python.exe`. Run these smoke commands from
outside the checkout as well. The installed console command is `scripteer`.
There is no `scriptkit` import/console alias in the new distribution: that import
also belongs to an unrelated PyPI project. Change consumer imports explicitly.
The public Python API/return semantics remain equivalent; namespace migration is
an explicit opt-in rather than a transparent upgrade of `pokanop-scriptkit`.

After the release is genuinely published and verified, public instructions become:

```sh
python -m pip install scripteer==1.6.0
uv tool install scripteer==1.6.0
pipx install scripteer==1.6.0
# For Python-library consumers instead of isolated CLI installation:
uv add scripteer==1.6.0
```

Do not advertise these as working until real clean pip/uv/pipx installation has
been recorded on POK-645. All package extras, dependency declarations, lockfiles,
PyPI links and generated tools use `scripteer`. Never publish placeholder packages
or claim the name by speculative uploads.

## Preserve user state and rollback

No data directories, credentials, trusted catalogs, caches, receipts or installed
tool environments are moved, copied or deleted during the rename.

- Root precedence is explicit `--root`, then `SCRIPTEER_ROOT`, then legacy
  `SCRIPTKIT_ROOT`, then `~/.scriptkit` if it exists, otherwise `~/.scripteer`.
  When both default directories exist the old root wins; select the other with
  `--root`. This avoids silently abandoning an existing installation.
- New receipts record `module: scripteer`. Historical receipts without that field
  mean `scriptkit`. The stable dispatcher/rollback allowlist only those two modules.
- Use the **new independently verified standalone bootstrap** to install Scripteer
  into the existing root. The old `scriptkit self-update` only accepts the old
  distribution and must not be used to cross the rename boundary.
- The new dispatcher can run either old or new generations. An existing,
  receipt-owned `scriptkit` wrapper remains untouched and continues through the
  shared dispatcher; new installs expose only `scripteer`. Neither foreign
  commands nor user-modified launchers are overwritten. Ownership ledger entries
  for old wrappers remain available for recovery.
- `scripteer self-rollback` or the new bootstrap's `--rollback` returns to the old
  generation without rewriting its environment. The `scripteer` wrapper then
  dispatches the old manager and reports its old identity/version. To move forward
  again, rerun the **new** bootstrap, not the old generation's self-update command.
- Keyring access stays opt-in. Read `scripteer.ai` / `openai` first, then legacy
  `scriptkit.ai` / `openai`; `OPENAI_API_KEY` still takes precedence. No automatic
  secret migration/deletion and no key material in logs.
- File-region markers `# >>> scriptkit:...`, `.scriptkit-lock` lock names,
  `.scriptkit-generator` ownership/journal directories and `urn:scriptkit:contracts:*:1`
  schema IDs intentionally retain their on-disk/wire identity. Renaming a lock
  would let old and new processes bypass each other's serialization. These are
  compatibility protocol identifiers, not stale product branding.

Keep the verified old bootstrap/wheel and its hashes for emergency rollback if you
retained them locally; the pre-rename GitHub releases themselves were removed by
owner decision (POK-696), and the historical onboarding and release pins were
removed with them. Attestations for the removed assets retain their original
signer identity. Do not create a new repository at the old path: GitHub redirects
from it must keep working.

## Generated projects

The immutable v1 template resource is retained byte-for-byte. New public scaffolds
use **template 3.0.0**, with Scripteer imports, dependency pins and authoring docs.
Existing v1/v2 projects require an explicit upgrade:

```sh
scripteer template-upgrade PROJECT --check
scripteer template-upgrade PROJECT --apply
scripteer validate PROJECT
```

Inspect the preview first and use version control. The upgrade validates old
ownership hashes, replaces only owned files and refuses modified/foreign files.
User-owned handlers, README, configuration and handwritten imports are preserved.
Update any user-owned `scriptkit` imports and `[tool.scriptkit.*]` settings to
`scripteer` manually; never blanket-replace user secrets or configuration. If a
user extended a generated pyproject, reconcile the conflict manually using the
preview rather than force overwrite. Pending legacy AI approvals must be rebuilt
against the new hashes; AI authoring requires an upgraded v3 project.

## Scripts collection consumer update

`pokanop/scripts` consumes the independently verified pre-rename wheel it already
pinned. Keep that consumer functional until a verified Scripteer release exists.
The framework's preserved historical consumer inventory describes
all imports, lock/bootstrap metadata, docs and tests requiring migration.

Sequence (no invented release URLs/hashes):

1. Review this candidate independently and verify current-head CI on all supported
   platforms, including installed wheel/sdist, bootstrap/rollback and
   generated-project upgrade evidence. Get human merge/release approval.
2. Publish/sign verified Scripteer 1.6.0 artifacts from the approved main commit.
3. In the coordinated consumer update, switch imports and runtime distribution to
   `scripteer`, advance its compatible range and exact wheel URL/SHA-256 together,
   update bootstrap/catalog/docs/fixtures, and rehearse legacy migration, generated
   tool registration and rollback. Do not merge a consumer with an unavailable pin.
4. Review that release's provenance, advance the consumer revision to it, and
   re-run certification with consumer rehearsal restored. Historical signatures and
   hashes are not mechanically renamed.

Thus the candidate PR is not a claim that publication or the consumer-pin phase
has finished. Existing immutable release hashes and tests remain real inputs.

## Owner-side PyPI setup (no API token to share)

1. Sign into PyPI, verify your email and enable 2FA. Recheck the selected project's
   eligibility. An HTTP 404 does not guarantee that PyPI will permit the upload.
2. In **Publishing**, add the GitHub OpenID Connect publisher (a pending
   publisher while the project page is still empty) with:
   - PyPI project: **scripteer**
   - GitHub owner: **pokanop**
   - Repository: **scripteer**
   - Workflow filename: **release.yml** (not a path)
   - Environment: **pypi**
3. The PyPI project has been registered by the owner (2026-10-23); the first
   successful authorized upload publishes 1.6.0. Do not upload an empty
   placeholder. No long-lived PyPI API token is needed. TestPyPI, if wanted,
   requires its own separate publisher.
4. Retain the GitHub `pypi` environment's independent approval, self-review
   prevention, admin-bypass prohibition and `v*` tag restriction. The sole reviewer
   is currently Sahel's shared GitHub identity; a run triggered by that identity
   cannot be self-approved. Add a distinct trusted human reviewer with repository
   access, or arrange a distinct authorized trigger identity and retain approval
   separation. Never turn off self-review prevention to get a release through.
5. Only after reviewed CI and explicit human merge/release approval, confirm the
   publisher/protections and enable `PYPI_PUBLISH_ENABLED=true`. Until then keep it
   unset. An approved `v1.6.0` tag on main triggers gated publication; manual workflow
   dispatch is a rehearsal and **cannot publish**.
6. Verify uploaded hashes, exact source/ref-bound GitHub provenance and release
   URLs, then execute real clean pip, uv and pipx installs. Record exact version,
   hashes and evidence on POK-645. If an upload fails, inspect before retrying;
   never overwrite release assets or bypass the environment gate.

No namesake was found on PyPI/npm/crates or as an established CLI in the 2026-10-11
preflight. Two older unrelated Java/JavaScript repository namesakes exist. These
checks are not domain/trademark clearance or a reservation.
