#!/usr/bin/env python3
"""
test_guard.py — Tests unitarios para scripts/guard.py en Luna Builder Fast.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "skills" / "luna-builder-fast" / "scripts"
GUARD_SCRIPT = SCRIPT_DIR / "guard.py"


class TestGuardScript(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="guard_test_")
        # Inicializar repositorio git temporal
        subprocess.run(["git", "init"], cwd=self.test_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Luna Tester"], cwd=self.test_dir, check=True)
        subprocess.run(["git", "config", "user.email", "tester@luna.local"], cwd=self.test_dir, check=True)

        # Crear archivo inicial
        self.initial_file = Path(self.test_dir) / "src" / "initial.txt"
        self.initial_file.parent.mkdir(parents=True, exist_ok=True)
        self.initial_file.write_text("line 1\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.test_dir, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=self.test_dir, check=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_guard_passes_when_changes_within_allowlist(self):
        snap_file = Path(self.test_dir) / ".luna" / "baseline.json"
        # Tomar snapshot
        res_snap = subprocess.run(
            [sys.executable, str(GUARD_SCRIPT), "snapshot", "-f", str(snap_file), "--cwd", self.test_dir],
            capture_output=True,
            text=True
        )
        self.assertEqual(res_snap.returncode, 0)
        self.assertTrue(snap_file.exists())

        # Modificar archivo permitido
        self.initial_file.write_text("line 1 modified\n", encoding="utf-8")

        # Verificar guard
        res_check = subprocess.run(
            [sys.executable, str(GUARD_SCRIPT), "check", "-a", "src/initial.txt", "-s", str(snap_file), "--cwd", self.test_dir],
            capture_output=True,
            text=True
        )
        self.assertEqual(res_check.returncode, 0)
        self.assertIn("GUARD PASÓ", res_check.stdout)

    def test_guard_fails_when_unauthorized_file_created(self):
        snap_file = Path(self.test_dir) / ".luna" / "baseline.json"
        subprocess.run(
            [sys.executable, str(GUARD_SCRIPT), "snapshot", "-f", str(snap_file), "--cwd", self.test_dir],
            check=True,
            capture_output=True
        )

        # Crear archivo prohibido fuera de lista
        unauthorized = Path(self.test_dir) / "src" / "forbidden.txt"
        unauthorized.write_text("forbidden content", encoding="utf-8")

        # Verificar guard permitiendo solo src/initial.txt
        res_check = subprocess.run(
            [sys.executable, str(GUARD_SCRIPT), "check", "-a", "src/initial.txt", "-s", str(snap_file), "--cwd", self.test_dir],
            capture_output=True,
            text=True
        )
        self.assertEqual(res_check.returncode, 1)
        self.assertIn("VIOLACIÓN", res_check.stdout)
        self.assertIn("GUARD FALLIDO", res_check.stderr)

    def test_guard_ignores_luna_metadata_and_snapshot(self):
        snap_file = Path(self.test_dir) / ".luna" / "baseline.json"
        subprocess.run(
            [sys.executable, str(GUARD_SCRIPT), "snapshot", "-f", str(snap_file), "--cwd", self.test_dir],
            check=True,
            capture_output=True
        )

        # Crear archivos dentro de .luna/
        luna_meta = Path(self.test_dir) / ".luna" / "runs" / "run_001.log"
        luna_meta.parent.mkdir(parents=True, exist_ok=True)
        luna_meta.write_text("log content", encoding="utf-8")

        # Modificar archivo permitido
        self.initial_file.write_text("line 1 updated\n", encoding="utf-8")

        # Verificar guard sin listar .luna
        res_check = subprocess.run(
            [sys.executable, str(GUARD_SCRIPT), "check", "-a", "src/initial.txt", "-s", str(snap_file), "--cwd", self.test_dir],
            capture_output=True,
            text=True
        )
        self.assertEqual(res_check.returncode, 0)
        self.assertIn("GUARD PASÓ", res_check.stdout)


if __name__ == "__main__":
    unittest.main()
