"""Rename contracts: retained user state, receipts, credentials and v2 scaffolds."""

import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from scripteer import bootstrap as b
from scripteer.ai import providers
from scripteer.entrypoint import main
from scripteer.generator import apply, preview
from scripteer.generator.scaffolds import existing, tool
from test_bootstrap import wheel_bytes


def test_root_precedence(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("SCRIPTEER_ROOT", raising=False)
    monkeypatch.delenv("SCRIPTKIT_ROOT", raising=False)
    assert b.default_root() == tmp_path / ".scripteer"
    (tmp_path / ".scriptkit").mkdir()
    assert b.default_root() == tmp_path / ".scriptkit"
    (tmp_path / ".scripteer").mkdir()
    assert b.default_root() == tmp_path / ".scriptkit"
    monkeypatch.setenv("SCRIPTKIT_ROOT", str(tmp_path / "old"))
    assert b.default_root() == tmp_path / "old"
    monkeypatch.setenv("SCRIPTEER_ROOT", str(tmp_path / "new"))
    assert b.default_root() == tmp_path / "new"


def test_explicit_root_overrides_environment(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SCRIPTEER_ROOT", str(tmp_path / "unused"))
    assert main(["--root", str(tmp_path), "--json", "doctor"]) == 0
    assert json.loads(capsys.readouterr().out)["data"]["root"] == str(tmp_path)


def test_receipt_module_is_allowlisted():
    assert b.manager_module({}) == "scriptkit"
    assert b.manager_module({"module": "scripteer"}) == "scripteer"
    with pytest.raises(ValueError, match="invalid manager module"):
        b.manager_module({"module": "arbitrary.module"})


@pytest.mark.parametrize("new", [None, "new-credential"])
def test_keyring_read_only_fallback(monkeypatch, new):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    calls = []

    def get(service, account):
        calls.append((service, account))
        return new if service == "scripteer.ai" else "legacy-credential"

    monkeypatch.setattr(
        providers.importlib, "import_module", lambda _: SimpleNamespace(get_password=get)
    )
    assert providers.credential(keyring=True) == (new or "legacy-credential")
    assert calls == [("scripteer.ai", "openai")] + ([] if new else [("scriptkit.ai", "openai")])


def legacy_project(root):
    fixture = json.loads((Path(__file__).parent / "fixtures/legacy-scaffold.json").read_text())
    for name, content in fixture["files"].items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="")
    handler = root / "src/demo/_handlers.py"
    handler.write_text("def run(command, arguments):\n    return 42\n")
    return handler


@pytest.mark.parametrize("template", ["1.0.0", "2.0.0"])
def test_legacy_validation_explains_explicit_upgrade(tmp_path, capsys, template):
    from scripteer.generator import render
    from scripteer.generator.plan import MANIFEST

    legacy_project(tmp_path)
    root = tmp_path
    if template == "1.0.0":
        spec, _ = existing(tmp_path)
        root = tmp_path / "v1"
        root.mkdir()
        apply(root, preview(root, render(spec)))
    before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert main(["--json", "validate", str(root)]) == 1
    report = json.loads(capsys.readouterr().out)
    diagnostics = report["data"]["diagnostics"]
    upgrade = next(d for d in diagnostics if d["code"] == "SKV013" and d["path"] == MANIFEST)
    assert f"legacy template {template}" in upgrade["message"]
    assert "scripteer template-upgrade PROJECT --check" in upgrade["message"]
    assert "scripteer template-upgrade PROJECT --apply" in upgrade["message"]
    assert "re-validate" in upgrade["message"]
    assert before == {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_real_v2_scaffold_upgrade(tmp_path, capsys):
    handler = legacy_project(tmp_path)
    before = handler.read_bytes()
    rendered = tool(*existing(tmp_path))
    with pytest.raises(ValueError, match="explicit supported migration"):
        preview(tmp_path, rendered)
    plan = preview(tmp_path, rendered, upgrade=True)
    assert not plan.conflicts
    apply(tmp_path, plan)
    assert handler.read_bytes() == before
    assert "from scripteer.scaffold_runtime" in (tmp_path / "src/demo/cli.py").read_text()
    assert "scripteer==1.6.0" in (tmp_path / "requirements.txt").read_text()
    assert (
        json.loads((tmp_path / ".scriptkit-generator/manifest.json").read_text())["template"]
        == "3.0.0"
    )
    assert main(["--json", "validate", str(tmp_path)]) == 0
    capsys.readouterr()
    assert not preview(tmp_path, rendered).drift


def test_legacy_upgrade_never_overwrites_modified_owned_file(tmp_path):
    legacy_project(tmp_path)
    project = tmp_path / "pyproject.toml"
    project.write_text(project.read_text() + "\n# user modification\n")
    plan = preview(tmp_path, tool(*existing(tmp_path)), upgrade=True)
    assert any(c.path == "pyproject.toml" for c in plan.conflicts)


def test_install_retains_old_ownership_and_rollback_module(tmp_path):
    from hashlib import sha256

    raw = wheel_bytes()
    ledger = tmp_path / "manager-launchers.json"
    legacy_command = str(tmp_path / "bin/scriptkit")
    b.publish(ledger, {legacy_command: ["a" * 64]})
    old = "a" * 32
    previous = tmp_path / "manager-generations" / old
    previous.mkdir(parents=True)
    b.publish(previous / "manager-receipt.json", {"version": "1.5.0"})
    b.publish(tmp_path / "manager-active.json", {"target": old})
    (tmp_path / "registries.json").write_bytes(b"private state")
    calls = []
    service = b.Manager(tmp_path, download=lambda _: raw, execute=calls.append)
    service.install("https://example.org/new.whl", sha256(raw).hexdigest(), "1.3.0")
    assert b.read(ledger)[legacy_command] == ["a" * 64]
    service.rollback()
    assert calls[-1][-2:] == ["scriptkit", "--version"]
    assert b.read(tmp_path / "manager-active.json")["target"] == old
    assert (tmp_path / "registries.json").read_bytes() == b"private state"


@pytest.mark.parametrize("receipt", [None, [], {"module": "bad"}])
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
