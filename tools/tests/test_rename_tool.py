"""Cross-platform rename-rehearsal paths and UTF-8 output are explicit contracts."""

import importlib.util
from pathlib import Path
import sys

import pytest

spec = importlib.util.spec_from_file_location(
    "check_rename", Path(__file__).resolve().parents[1] / "check_rename.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_launcher_output_ignores_parent_locale(monkeypatch):
    monkeypatch.setattr(module.subprocess, "_text_encoding", lambda: "cp1252")
    assert module.output(sys.executable, "-c", "import os; os.write(1, b'caf\\xc3\\xa9')") == "café"


def test_root_canonicalized_before_receipt_and_ledger_access(tmp_path, monkeypatch):
    actual = tmp_path / "actual"
    actual.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(actual, target_is_directory=True)
    monkeypatch.setattr(sys, "argv", ["check_rename.py", str(alias), "candidate.whl"])
    paths = []

    def read(path):
        paths.append(path)
        raise RuntimeError("stop before installation")

    monkeypatch.setattr(module, "read", read)
    with pytest.raises(RuntimeError, match="stop before installation"):
        module.main()
    assert paths == [actual.resolve() / "manager-active.json"]
