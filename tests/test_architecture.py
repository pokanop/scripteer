"""Executable ownership graph; runs on source installs AND installed wheels."""

import ast
import importlib.util
from pathlib import Path
import subprocess
import sys

import scripteer


LAYERS = {"contracts", "registry", "manager", "generator", "ai", "conformance"}
ALLOWED = {
    "runtime": {"runtime"},
    "contracts": {"contracts"},
    "registry": {"registry", "contracts", "state"},
    "manager": {"manager", "contracts", "state", "execution"},
    "generator": {"generator", "contracts"},
    "ai": {"ai", "contracts"},
    "conformance": {"conformance", "contracts", "generator", "output", "command", "execution"},
}


def layer(module):
    parts = module.split(".")
    return parts[1] if len(parts) > 1 and parts[1] in LAYERS else "runtime"


def imports(text, module, is_package=False):
    package = module if is_package else module.rpartition(".")[0]
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            yield from ((alias.name, False) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = (
                importlib.util.resolve_name("." * node.level + (node.module or ""), package)
                if node.level
                else node.module
            )
            yield base, True
            yield from ((base + "." + alias.name, True) for alias in node.names)
        elif isinstance(node, ast.Call) and (
            isinstance(node.func, ast.Name)
            and node.func.id in {"__import__", "import_module"}
            or isinstance(node.func, ast.Attribute)
            and node.func.attr == "import_module"
        ):
            # No hidden/computed dynamic edges in protected layers.
            if (
                not node.args
                or not isinstance(node.args[0], ast.Constant)
                or not isinstance(node.args[0].value, str)
            ):
                yield "FORBIDDEN_COMPUTED_IMPORT", False
            else:
                yield importlib.util.resolve_name(node.args[0].value, package), False


# AI's project adapters compose established generator/conformance primitives.
# Provider/contracts modules still cannot access these layers (or manager/registry/runtime).
AI_PROJECT_PORTS = {
    "scripteer.ai.context": {
        "scripteer.generator.plan": {"MANIFEST", "Manifest", "read", "target"},
        "scripteer.generator.scaffolds": {"existing"},
    },
    "scripteer.ai.review": {
        "scripteer.conformance.ownership": {"metadata_extension"},
        "scripteer.conformance.static": {"validate"},
        "scripteer.generator.plan": {
            "MANIFEST",
            "Manifest",
            "Change",
            "Plan",
            "preview",
            "read",
            "target",
        },
        "scripteer.generator.render": {"sha256", "canonical"},
        "scripteer.generator.scaffolds": {"existing", "tool"},
        "scripteer.generator.transaction": {"Writer", "apply"},
    },
}


def violations(text, module, is_package=False):
    source = layer(module)
    errors = []
    for target, from_import in imports(text, module, is_package):
        if from_import and any(
            target == port or target in {port + "." + name for name in symbols}
            for port, symbols in AI_PROJECT_PORTS.get(module, {}).items()
        ):
            continue
        # Bootstrap must remain independently downloadable, so the shared stdlib
        # cmd template lives there. Only the launchers adapter may import it;
        # importing Manager or another bootstrap symbol is still forbidden.
        if module == "scripteer.manager.launchers" and target in {
            "scripteer.bootstrap",
            "scripteer.bootstrap.cmd_launcher",
        }:
            continue
        if target.startswith("scripteer.") or target == "scripteer":
            # Narrow reusable IO adapters, never the whole runtime or provider layer.
            target_layer = layer(target)
            for adapter in ("state", "execution", "output", "command"):
                if source in {"registry", "manager", "conformance"} and (
                    target == f"scripteer.{adapter}" or target.startswith(f"scripteer.{adapter}.")
                ):
                    target_layer = adapter
            if target_layer not in ALLOWED[source]:
                errors.append(f"{module} -> {target}")
        elif source == "contracts" and target.split(".")[0] not in sys.stdlib_module_names | {
            "__future__"
        }:
            errors.append(f"{module} -> external {target}")
        elif target == "FORBIDDEN_COMPUTED_IMPORT":
            errors.append(f"{module} -> computed import")
    return errors


def test_ownership_graph():
    root = Path(scripteer.__file__).parent
    errors = []
    for path in root.rglob("*.py"):
        relative = path.relative_to(root).with_suffix("")
        parts = list(relative.parts)
        is_package = parts[-1] == "__init__"
        if is_package:
            parts.pop()
        module = ".".join(["scripteer", *parts])
        if module in {"scripteer.entrypoint", "scripteer.__main__", "scripteer.manager_cli"}:
            continue  # composition roots alone may wire upper layers
        errors.extend(violations(path.read_text(encoding="utf-8"), module, is_package))
    assert not errors, "\n".join(errors)


def test_checker_detects_regressions():
    for code, module in [
        ("from .manager import install", "scripteer.app"),
        ("from . import ai", "scripteer.app"),
        ("import scripteer.generator", "scripteer.contracts.models"),
        ("from .. import manager", "scripteer.contracts.models"),
        ("import requests", "scripteer.contracts.models"),
        ("import scripteer.console", "scripteer.registry.cache"),
        ("import scripteer.manager", "scripteer.conformance.static"),
        ("import scripteer.conformance", "scripteer.app"),
        ("import scripteer.ai", "scripteer.conformance.static"),
        ("import scripteer.generator", "scripteer.ai.provider"),
        ("import scripteer.generator", "scripteer.ai.contracts"),
        ("import scripteer.manager", "scripteer.ai.review"),
        ("import scripteer.execution", "scripteer.ai.review"),
        ("import scripteer.registry", "scripteer.ai.context"),
        ("from scripteer.generator.scaffolds import installer", "scripteer.ai.review"),
        ("import scripteer.generator.transaction", "scripteer.ai.review"),
        ("import scripteer.generator.transaction as transaction", "scripteer.ai.review"),
        ("importlib.import_module('scripteer.generator.transaction')", "scripteer.ai.review"),
        ("import scripteer.state", "scripteer.contracts.models"),
        ("import scripteer.registry", "scripteer.manager.service"),
        ("import scripteer.console", "scripteer.manager.service"),
        ("from scripteer.bootstrap import Manager", "scripteer.manager.launchers"),
        ("from scripteer.bootstrap import cmd_launcher", "scripteer.manager.service"),
        ("import scripteer.execution", "scripteer.registry.cache"),
        ("importlib.import_module('scripteer.ai')", "scripteer.app"),
        ("__import__(computed)", "scripteer.app"),
        ("from importlib import import_module; import_module('scripteer.ai')", "scripteer.app"),
    ]:
        assert violations(code, module), code


def test_core_imports_without_upper_layers():
    subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            """
import sys
class BlockUpperLayers:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'requests', 'openai', 'anthropic', 'pydantic', 'jsonschema'} or any(fullname == 'scripteer.' + name or fullname.startswith('scripteer.' + name + '.') for name in ('manager', 'registry', 'generator', 'ai', 'conformance')):
            raise AssertionError('Forbidden core dependency: ' + fullname)
sys.meta_path.insert(0, BlockUpperLayers())
import scripteer
import scripteer.contracts
import scripteer.safe_config
import scripteer.state
import scripteer.paths
import scripteer.regions
import scripteer.execution
from scripteer.contracts import ToolSpec, resource_text
ToolSpec.from_json(resource_text('ToolSpec.example.json'))
""",
        ],
        check=True,
    )
