#!/usr/bin/env python3
"""
test_hook_pretool.py — Tests unitarios para scripts/hook_pretool.py en Luna Builder Fast.
"""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "skills" / "luna-builder-fast" / "scripts"
HOOK_SCRIPT = SCRIPT_DIR / "hook_pretool.py"


class TestHookPreTool(unittest.TestCase):
    def test_passive_mode_allows_anything(self):
        env = os.environ.copy()
        env.pop("LUNA_GUARD_ALLOW", None)

        payload = json.dumps({
            "toolCall": {
                "name": "edit_file",
                "args": {"Path": "any_file.py"}
            }
        })
        res = subprocess.run([sys.executable, str(HOOK_SCRIPT)], input=payload, capture_output=True, text=True, env=env)
        self.assertEqual(res.returncode, 0)
        out = json.loads(res.stdout)
        self.assertEqual(out.get("decision"), "allow")

    def test_active_mode_allows_authorized_file(self):
        env = os.environ.copy()
        env["LUNA_GUARD_ALLOW"] = "src/allowed.py;tests/test_allowed.py"

        payload = json.dumps({
            "toolCall": {
                "name": "edit_file",
                "args": {"Path": "src/allowed.py"}
            }
        })
        res = subprocess.run([sys.executable, str(HOOK_SCRIPT)], input=payload, capture_output=True, text=True, env=env)
        self.assertEqual(res.returncode, 0)
        out = json.loads(res.stdout)
        self.assertEqual(out.get("decision"), "allow")

    def test_active_mode_denies_unauthorized_file(self):
        env = os.environ.copy()
        env["LUNA_GUARD_ALLOW"] = "src/allowed.py"

        payload = json.dumps({
            "toolCall": {
                "name": "write_file",
                "args": {"Path": "forbidden/secret.py"}
            }
        })
        res = subprocess.run([sys.executable, str(HOOK_SCRIPT)], input=payload, capture_output=True, text=True, env=env)
        self.assertEqual(res.returncode, 0)
        out = json.loads(res.stdout)
        self.assertEqual(out.get("decision"), "deny")
        self.assertIn("Acceso bloqueado", out.get("reason", ""))

    def test_graceful_on_empty_or_malformed_input(self):
        env = os.environ.copy()
        res = subprocess.run([sys.executable, str(HOOK_SCRIPT)], input="INVALID_NOT_JSON", capture_output=True, text=True, env=env)
        self.assertEqual(res.returncode, 0)
        out = json.loads(res.stdout)
        self.assertEqual(out.get("decision"), "allow")


if __name__ == "__main__":
    unittest.main()
