"""Rename contracts: clean break from the pre-rename legacy identity."""

import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from scripteer import bootstrap as b
from scripteer.ai import providers
from scripteer.contracts import ToolSpec, resource_text
from scripteer.entrypoint import main
from scripteer.generator import apply, preview, render
from scripteer.generator.scaffolds import existing, tool
from test_bootstrap import wheel_bytes

# Built at runtime so this file itself stays free of the pre-rename identifier;
# the repository-wide absence of that identifier is enforced by the test below.
LEGACY = "script" + "kit"

# The genuine receipt shape written by the pre-rename manager (POK-622): five
# fields and no module key at all — unlike a merely wrong module value, this is
# the shape real pre-rename installs carry on disk.
PRE_RENAME_RECEIPT = {
    "schema_version": 1,
    "version": "1.5.0",
    "sha256": "0" * 64,
    "url": "https://example.org/old.whl",
    "generation": "0" * 32,
}


@pytest.fixture
def spec():
    value = json.loads(resource_text("ToolSpec.example.json"))
    value["entrypoint"] = "demo.cli:main"
    return ToolSpec.from_dict(value)


def test_root_precedence_ignores_legacy_environment_and_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("SCRIPTEER_ROOT", raising=False)
    monkeypatch.delenv(LEGACY.upper() + "_ROOT", raising=False)
    (tmp_path / ("." + LEGACY)).mkdir()
    assert b.default_root() == tmp_path / ".scripteer"
    monkeypatch.setenv(LEGACY.upper() + "_ROOT", str(tmp_path / "old"))
    assert b.default_root() == tmp_path / ".scripteer"
    monkeypatch.setenv("SCRIPTEER_ROOT", str(tmp_path / "new"))
    assert b.default_root() == tmp_path / "new"


def test_explicit_root_overrides_environment(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SCRIPTEER_ROOT", str(tmp_path / "unused"))
    assert main(["--root", str(tmp_path), "--json", "doctor"]) == 0
    assert json.loads(capsys.readouterr().out)["data"]["root"] == str(tmp_path)


def test_receipt_module_allowlist_is_current_identity_only():
    assert b.manager_module({"module": "scripteer"}) == "scripteer"
    for receipt in (
        {},
        PRE_RENAME_RECEIPT,
        {"module": "arbitrary.module"},
        {"module": LEGACY},
    ):
        with pytest.raises(ValueError, match="invalid manager module"):
            b.manager_module(receipt)


def test_keyring_reads_only_current_service(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    calls = []

    def get(service, account):
        calls.append((service, account))
        return "stored-credential" if service == "scripteer.ai" else None

    monkeypatch.setattr(
        providers.importlib, "import_module", lambda _: SimpleNamespace(get_password=get)
    )
    assert providers.credential(keyring=True) == "stored-credential"
    assert calls == [("scripteer.ai", "openai")]


def test_keyring_missing_credential_fails_without_legacy_fallback(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(
        providers.importlib,
        "import_module",
        lambda _: SimpleNamespace(get_password=lambda service, account: None),
    )
    with pytest.raises(providers.ProviderError, match="OPENAI_API_KEY"):
        providers.credential(keyring=True)


def test_repository_contains_no_legacy_identity():
    root = Path(__file__).resolve().parents[1]
    try:
        tracked = subprocess.run(
            ["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True
        ).stdout.splitlines()
        paths = [root / name for name in tracked]
    except (OSError, subprocess.CalledProcessError):
        paths = [path for path in root.rglob("*") if ".git" not in path.parts and path.is_file()]
    offenders = []
    needle = LEGACY.encode()
    for path in paths:
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix().lower()
        if LEGACY in relative or needle in path.read_bytes().lower():
            offenders.append(relative)
    assert not offenders, f"legacy identity references remain: {offenders}"


def test_v1_validation_explains_explicit_upgrade(tmp_path, capsys, spec):
    from scripteer.generator.plan import MANIFEST

    apply(tmp_path, preview(tmp_path, render(spec)))
    handler = tmp_path / "src/demo/_handlers.py"
    handler.write_text("def run(command, arguments):\n    return 42\n")
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert main(["--json", "validate", str(tmp_path)]) == 1
    report = json.loads(capsys.readouterr().out)
    diagnostics = report["data"]["diagnostics"]
    upgrade = next(d for d in diagnostics if d["code"] == "SKV013" and d["path"] == MANIFEST)
    assert "legacy template 1.0.0" in upgrade["message"]
    assert "scripteer template-upgrade PROJECT --check" in upgrade["message"]
    assert "scripteer template-upgrade PROJECT --apply" in upgrade["message"]
    assert "re-validate" in upgrade["message"]
    assert before == {
        p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()
    }


def test_v1_scaffold_upgrade(tmp_path, capsys, spec):
    apply(tmp_path, preview(tmp_path, render(spec)))
    handler = tmp_path / "src/demo/_handlers.py"
    handler.write_text("def run(command, arguments):\n    return 42\n")
    before = handler.read_bytes()
    rendered = tool(*existing(tmp_path))
    with pytest.raises(ValueError, match="explicit supported migration"):
        preview(tmp_path, rendered)
    plan = preview(tmp_path, rendered, upgrade=True)
    assert not plan.conflicts
    apply(tmp_path, plan)
    assert handler.read_bytes() == before
    assert "from scripteer.scaffold_runtime" in (tmp_path / "src/demo/cli.py").read_text()
    assert "scripteer==" in (tmp_path / "requirements.txt").read_text()
    manifest = json.loads((tmp_path / ".scripteer-generator/manifest.json").read_text())
    assert manifest["template"] == "3.0.0"
    assert main(["--json", "validate", str(tmp_path)]) == 0
    capsys.readouterr()
    assert not preview(tmp_path, rendered).drift


def test_v1_upgrade_never_overwrites_modified_owned_file(tmp_path, spec):
    apply(tmp_path, preview(tmp_path, render(spec)))
    project = tmp_path / "pyproject.toml"
    project.write_text(project.read_text() + "\n# user modification\n")
    plan = preview(tmp_path, tool(*existing(tmp_path)), upgrade=True)
    assert any(c.path == "pyproject.toml" for c in plan.conflicts)


def test_install_retains_retired_ownership_and_rollback_module(tmp_path):
    from hashlib import sha256

    raw = wheel_bytes()
    ledger = tmp_path / "manager-launchers.json"
    retired_command = str(tmp_path / "bin/retired-wrapper")
    b.publish(ledger, {retired_command: ["a" * 64]})
    old = "a" * 32
    previous = tmp_path / "manager-generations" / old
    previous.mkdir(parents=True)
    b.publish(previous / "manager-receipt.json", {"module": "scripteer", "version": "1.5.0"})
    b.publish(tmp_path / "manager-active.json", {"target": old})
    (tmp_path / "registries.json").write_bytes(b"private state")
    calls = []
    service = b.Manager(tmp_path, download=lambda _: raw, execute=calls.append)
    service.install("https://example.org/new.whl", sha256(raw).hexdigest(), "1.3.0")
    assert b.read(ledger)[retired_command] == ["a" * 64]
    service.rollback()
    assert calls[-1][-2:] == ["scripteer", "--version"]
    assert b.read(tmp_path / "manager-active.json")["target"] == old
    assert (tmp_path / "registries.json").read_bytes() == b"private state"


@pytest.mark.parametrize(
    "receipt",
    [
        {"version": "1.5.0", "module": LEGACY},
        PRE_RENAME_RECEIPT,
    ],
    ids=["wrong-module", "module-less-pre-rename"],
)
def test_rollback_rejects_pre_rename_receipt_module(tmp_path, receipt):
    old = "a" * 32
    previous = tmp_path / "manager-generations" / old
    previous.mkdir(parents=True)
    b.publish(previous / "manager-receipt.json", receipt)
    b.publish(tmp_path / "manager-active.json", {"target": "b" * 32, "previous": old})
    calls = []
    service = b.Manager(tmp_path, execute=calls.append)
    with pytest.raises(ValueError, match="invalid manager module"):
        service.rollback()
    assert not calls


@pytest.mark.parametrize(
    "receipt",
    [None, [], {}, {"module": "bad"}, PRE_RENAME_RECEIPT],
    ids=["absent", "non-object", "empty", "wrong-module", "module-less-pre-rename"],
)
def test_dispatcher_rejects_invalid_receipt(tmp_path, receipt):
    target = "a" * 32
    base = tmp_path / "manager-generations" / target
    python = b.python_at(base)
    python.parent.mkdir(parents=True)
    python.touch()
    b.publish(tmp_path / "manager-active.json", {"target": target})
    if receipt is not None:
        (base / "manager-receipt.json").write_text(json.dumps(receipt))
    files = b.launcher_files(tmp_path)
    loader = tmp_path / "manager-launch.py"
    loader.write_bytes(files[loader])
    result = subprocess.run([sys.executable, str(loader), "--json"], capture_output=True, text=True)
    assert result.returncode == 1
    assert json.loads(result.stdout)["ok"] is False
    assert "invalid manager" in result.stderr
    assert "Traceback" not in result.stderr
