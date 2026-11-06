"""Keep the public first-tool tutorial executable without network access."""

import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest


def test_getting_started_tutorial(tmp_path):
    document = Path(__file__).resolve().parents[1] / "docs" / "getting-started.md"
    if not document.exists():
        pytest.skip("Source documentation is not included in installed test copies")
    text = document.read_text(encoding="utf-8")
    specs = re.findall(r"```json\n(.*?)\n```", text, re.S)
    code = re.findall(r"```python\n(.*?)\n```", text, re.S)
    project = tmp_path / "hello-tool"
    project.mkdir()
    spec = tmp_path / "tool-spec.json"
    spec.write_text(specs[0], encoding="utf-8")

    def cli(*args):
        return subprocess.run(
            [sys.executable, "-m", "scripteer", *map(str, args)],
            check=True,
            capture_output=True,
            text=True,
        )

    cli("new-tool", project, "--spec", spec)
    assert not list(project.iterdir())
    cli("new-tool", project, "--spec", spec, "--apply")
    handler = project / "src" / "hello_tool" / "_handlers.py"
    handler.write_text(code[0] + "\n", encoding="utf-8")
    env = dict(os.environ, PYTHONPATH=str(project / "src"))

    def tool(*args):
        return subprocess.run(
            [sys.executable, "-m", "hello_tool.cli", *args],
            cwd=tmp_path,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    assert "Hello, World!" in tool("greet", "World").stdout
    result = json.loads(tool("--json", "greet", "World").stdout)
    assert result["ok"] is True
    assert result["data"] == {"message": "Hello, World!"}
    tool("doctor")
    cli("validate", project)
    spec.write_text(specs[1], encoding="utf-8")
    cli("add-command", project, "--spec", spec, "--apply")
    assert handler.read_text(encoding="utf-8") == code[0] + "\n"
    handler.write_text(
        code[0].replace("    raise NotImplementedError(command)", code[1]) + "\n",
        encoding="utf-8",
    )
    assert "ready" in tool("status").stdout
    cli("validate", project)
