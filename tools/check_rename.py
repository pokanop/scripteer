"""Exercise the candidate against an already verified real ScriptKit manager root.

Run with the candidate's installed Python, never a source-tree import. The caller
certifies the old wheel/bootstrap before creating this root. No network required.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from scripteer import __version__
from scripteer.bootstrap import Manager, read


def output(*argv):
    # Both legacy and new launchers force UTF-8, including Windows cmd wrappers.
    return subprocess.check_output([str(arg) for arg in argv], text=True, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("wheel", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()  # Match bootstrap ledger keys (macOS /var → /private/var).
    old_pointer = read(root / "manager-active.json")
    old_receipt = read(
        root / "manager-generations" / old_pointer["target"] / "manager-receipt.json"
    )
    assert "module" not in old_receipt  # Actual pre-rename receipt format.
    suffix = ".cmd" if os.name == "nt" else ""
    old_command = root / "bin" / ("scriptkit" + suffix)
    old_wrapper = old_command.read_bytes()
    assert "scriptkit " + old_receipt["version"] in output(old_command, "--version")
    private = root / "rename-user-config.json"
    private.write_bytes(b'{"keep":"user state"}\n')
    raw = args.wheel.read_bytes()
    service = Manager(root, download=lambda _: raw)

    def install():
        service.install(
            "https://example.invalid/verified-local-candidate.whl",
            hashlib.sha256(raw).hexdigest(),
            __version__,
        )

    install()
    new_command = root / "bin" / ("scripteer" + suffix)
    for command in (old_command, new_command):
        assert "scripteer " + __version__ in output(command, "--version")
        doctor = json.loads(output(command, "--json", "doctor"))
        assert Path(doctor["data"]["root"]).samefile(root)
    assert old_command.read_bytes() == old_wrapper
    service.rollback()
    assert read(root / "manager-active.json")["target"] == old_pointer["target"]
    assert "scriptkit " + old_receipt["version"] in output(new_command, "--version")
    install()  # Forward repair after rollback uses the NEW bootstrap/service.
    assert "scripteer " + __version__ in output(new_command, "--version")
    assert private.read_bytes() == b'{"keep":"user state"}\n'
    assert str(old_command) in read(root / "manager-launchers.json")
    print(
        "Real ScriptKit -> Scripteer -> ScriptKit -> Scripteer: state and legacy wrapper preserved"
    )


if __name__ == "__main__":
    main()
