"""Certify candidate artifacts built from the current checkout.

Requires Python 3.11+, git and build tooling. Never publishes, changes trust
settings, or uses PyPI to acquire the framework. Pre-rename release
verification was retired together with those releases (POK-696): this gate
certifies the candidate against itself — strict artifact manifest, clean-room
installed suite, and sdist/wheel package parity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tarfile
import tomllib
import venv
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def run(*args, cwd, env=None):
    subprocess.run([str(arg) for arg in args], cwd=cwd, env=env, check=True)


def verify_assets(directory, pins):
    """Exact manifest membership and bytes; authenticated pins are reviewed in git."""
    expected = pins["assets"]
    if {p.name for p in directory.iterdir()} != set(expected):
        raise ValueError("unexpected/missing asset")
    for name, digest in expected.items():
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
            raise ValueError("asset digest mismatch: " + name)
    manifest = {}
    for line in (directory / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split()
        if name in manifest:
            raise ValueError("duplicate checksum entry")
        manifest[name] = digest
    if manifest != {k: v for k, v in expected.items() if k not in ("SHA256SUMS", "build.json")}:
        raise ValueError("checksum manifest membership mismatch")


def extract_suite(sdist, destination, pins):
    """Extract only authenticated regular sdist contents, never links/devices."""
    with tarfile.open(sdist) as archive:
        if any(not (member.isfile() or member.isdir()) for member in archive.getmembers()):
            raise ValueError("non-regular sdist member")
        archive.extractall(destination, filter="data")
    roots = list(destination.iterdir())
    if len(roots) != 1 or not roots[0].is_dir():
        raise ValueError("expected one sdist root")
    root = roots[0]
    metadata = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    if metadata["name"] != pins["distribution"] or metadata["version"] != pins["version"]:
        raise ValueError("sdist identity mismatch")
    if metadata["scripts"].get(pins["command"]) != pins["module"] + ".entrypoint:main":
        raise ValueError("sdist entrypoint mismatch")
    return root


def package_payload(wheel, module):
    with zipfile.ZipFile(wheel) as archive:
        return {
            name: archive.read(name) for name in archive.namelist() if name.startswith(module + "/")
        }


SMOKE = (
    "from pathlib import Path; import importlib,sys; "
    "runtime = importlib.import_module(sys.argv[1]); "
    "assert Path(runtime.__file__).is_relative_to(sys.prefix); "
    "assert runtime.__version__ == sys.argv[2]; "
    "contracts = importlib.import_module(sys.argv[1] + '.contracts'); "
    "assert contracts.resource_text('ToolSpec.example.json')"
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    command, entrypoint = next(iter(project["scripts"].items()))
    identity = {
        "distribution": project["name"],
        "version": project["version"],
        "module": entrypoint.split(".")[0],
        "command": command,
    }
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME")}
    env.update(PYTHONUTF8="1", PIP_DISABLE_PIP_VERSION_CHECK="1", NO_COLOR="1")
    report = {"identity": identity, "steps": [], "complete": False}
    try:
        with tempfile.TemporaryDirectory(prefix="scripteer-certification-") as temporary:
            work = Path(temporary)
            dist = work / "dist"
            run(sys.executable, "-m", "build", "--outdir", dist, ROOT, cwd=work, env=env)
            wheel = next(dist.glob("*.whl"))
            sdist = next(dist.glob("*.tar.gz"))
            digests = {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(dist.iterdir())
            }
            (dist / "SHA256SUMS").write_text(
                "".join(f"{digest}  {name}\n" for name, digest in digests.items()),
                encoding="utf-8",
            )
            digests["SHA256SUMS"] = hashlib.sha256((dist / "SHA256SUMS").read_bytes()).hexdigest()
            verify_assets(dist, {"assets": digests})
            run(sys.executable, "-m", "twine", "check", "--strict", sdist, wheel, cwd=work, env=env)
            report["steps"].append(
                "candidate sdist+wheel: exact SHA256SUMS manifest, twine --strict"
            )
            suite = extract_suite(sdist, work / "candidate-suite", identity)
            report["suite_source"] = sdist.name
            run(
                sys.executable,
                ROOT / "tools" / "check_artifact.py",
                wheel,
                "--results",
                output / "framework.xml",
                cwd=ROOT,
                env=env,
            )
            run(
                sys.executable,
                ROOT / "tools" / "check_artifact.py",
                wheel,
                "--rich",
                cwd=ROOT,
                env=env,
            )
            report["steps"].append(
                "installed candidate wheel: full suite outside checkout (bare and Rich)"
            )
            rebuilt = work / "rebuilt"
            run(
                sys.executable,
                "-m",
                "build",
                "--wheel",
                "--outdir",
                rebuilt,
                suite,
                cwd=work,
                env=env,
            )
            rebuilt_wheel = next(rebuilt.glob("*.whl"))
            if package_payload(rebuilt_wheel, identity["module"]) != package_payload(
                wheel, identity["module"]
            ):
                raise ValueError("sdist payload drift")
            clean = work / "sdist-env"
            venv.EnvBuilder(with_pip=True).create(clean)
            python = clean / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            run(python, "-m", "pip", "install", "--no-index", rebuilt_wheel, cwd=work, env=env)
            run(python, "-I", "-m", identity["module"], "--help", cwd=work, env=env)
            run(
                python,
                "-I",
                "-c",
                SMOKE,
                identity["module"],
                identity["version"],
                cwd=work,
                env=env,
            )
            report["steps"].append(
                "sdist rebuilt/installed outside checkout offline; all package resources match wheel"
            )
            report["complete"] = True
    finally:
        (output / "certification.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
