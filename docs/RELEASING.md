# Releasing Scripteer

This is the runbook for every public release. One release = one PR + one tag.
The whole flow is CI-driven; no one builds or uploads artifacts locally and no
PyPI token exists anywhere (publication uses OpenID Connect trusted publishing).

## Release flow

1. **Version bump PR.** Bump the version in exactly two files:
   `pyproject.toml` (`[project] version`) and `src/scripteer/__init__.py`
   (`__version__`). CI wheel checks accept any version
   (`dist/scripteer-*-py3-none-any.whl`) and installed-artifact tests pin the
   built wheel at `scripteer.__version__`, so no other file carries the version
   number. `check_artifact.py` additionally asserts wheel metadata ==
   `__version__` == `pyproject.toml`, so the two files cannot drift apart
   silently. Choose the number per the SemVer policy in
   [compatibility](compatibility.md) (patches preserve behavior; minors add
   compatible APIs; removals/breaks take a major). Draft the release notes in
   the PR description — they become the GitHub release body.
2. **Review and merge.** The PR goes through the normal required checks and
   Code Reviewer approval; the owner merges it to `main`. Never merge a
   release PR with a red required check.
3. **Tag.** From the merged `main` head, push an annotated tag whose name is
   exactly `v` + the new version (e.g. `v2.0.1`):

   ```sh
   git fetch origin && git checkout origin/main
   git tag -a vX.Y.Z -m "Scripteer vX.Y.Z"
   git push origin vX.Y.Z
   ```

   Never move or reuse an existing tag. `release.yml` rejects a tag that does
   not equal `pyproject.toml`'s version or whose commit is not an ancestor of
   `main`, and it permanently refuses `1.3.0` (that version identifies the
   pre-rename runtime-only wheel).
4. **CI publishes.** The tag run executes `quality` (the full CI matrix via
   `ci.yml`), then `provenance` (build attestations verified against the exact
   source commit), then `publish`. `publish` only runs when the repository
   variable `PYPI_PUBLISH_ENABLED` is `true` **and** a required reviewer
   approves the protected `pypi` environment deployment — the owner opens the
   waiting run and clicks "Review deployments → Approve". Because tag pushes
   come from the shared owner credential, `prevent_self_review` is
   intentionally off (the owner approves a run triggered by their own
   automation); harden by adding a second reviewer and re-enabling it once a
   distinct release credential exists (#29). The upload authenticates as the PyPI
   trusted publisher (owner
   `pokanop`, repo `scripteer`, workflow `release.yml`, environment `pypi`);
   there is no API token to rotate or leak. A manual `workflow_dispatch` run
   is a rehearsal only and can never publish.
5. **Verify the release** (record evidence on the release ticket):

   - The run completed green: `gh run list --workflow release.yml --limit 1`
     (or the Actions URL for the tag).
   - The project page is live: `https://pypi.org/project/scripteer/`.
   - Clean-venv install from the index:

     ```sh
     python -m venv /tmp/relcheck && /tmp/relcheck/bin/python -m pip install scripteer==X.Y.Z
     /tmp/relcheck/bin/scripteer --version   # prints X.Y.Z
     /tmp/relcheck/bin/scripteer --help
     ```

     (CI's certification matrix covers the equivalent installed-artifact
     journeys on Linux/macOS/Windows; this is the index-level spot check.)
   - Create the GitHub release from the tag with the reviewed notes:
     `gh release create vX.Y.Z --title "Scripteer vX.Y.Z" --notes-file notes.md`.

## Failure and rollback

- A red `quality` or `provenance` job means nothing was uploaded; fix forward
  on `main`, then cut a fresh tag (bump the patch if the broken tag was
  already announced).
- A publish failure after environment approval: inspect the run before any
  retry; PyPI files are immutable, so never re-upload the same version.
- A bad release already on the index is **yanked** (`pypi.org/manage`), never
  deleted or overwritten; the fix is the next version.
- `PYPI_PUBLISH_ENABLED` stays `true`; it exists as a kill switch to disable
  tag-driven publication without touching the workflow.

## Reference

- Workflow: [`.github/workflows/release.yml`](../.github/workflows/release.yml)
- Quality contract: [quality-and-release](quality-and-release.md)
- Identity, migration and owner-side PyPI setup:
  [scripteer-launch](scripteer-launch.md)
- Version policy: [compatibility](compatibility.md)
