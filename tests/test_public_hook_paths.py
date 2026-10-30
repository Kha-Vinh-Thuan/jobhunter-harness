"""Verify shipped hook commands work in a relocated checkout with spaces."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PublicHookPathTests(unittest.TestCase):
    def test_hook_resolves_the_git_root_from_a_relocated_subdirectory(self):
        with tempfile.TemporaryDirectory(prefix="public checkout ", dir=ROOT / ".state") as folder:
            checkout = Path(folder)
            subprocess.run(["git", "init", "--quiet", str(checkout)], check=True, capture_output=True)
            (checkout / ".venv/bin").mkdir(parents=True)
            try:
                (checkout / ".venv/bin/python").symlink_to(sys.executable)
            except OSError:  # Windows without symlink privilege
                self.skipTest("symlinks unavailable; POSIX hook command not exercised")
            scripts = checkout / "scripts"
            scripts.mkdir()
            (scripts / "harness.py").write_text(
                "import json, sys\n"
                "print(json.dumps({'script': __file__, 'args': sys.argv[1:]}))\n"
            )
            nested = checkout / "nested folder"
            nested.mkdir()
            config = json.loads((ROOT / ".codex/hooks.json").read_text())
            command = config["hooks"]["SessionStart"][0]["hooks"][0]["command"]
            result = subprocess.run(command, shell=True, cwd=nested, capture_output=True,
                                    text=True, input="{}", check=True)
            observed = json.loads(result.stdout)
            self.assertEqual(str(scripts / "harness.py"), observed["script"])
            self.assertEqual(["hook", "SessionStart", "--native"], observed["args"])
