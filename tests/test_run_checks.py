#!/usr/bin/env python3
"""
test_run_checks.py — Tests unitarios para scripts/run_checks.py en Luna Builder Fast.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "skills" / "luna-builder-fast" / "scripts"
RUN_CHECKS_SCRIPT = SCRIPT_DIR / "run_checks.py"
GUARD_SCRIPT = SCRIPT_DIR / "guard.py"


class TestRunChecksScript(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="run_checks_test_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_run_checks_success(self):
        cmd = [
            sys.executable, str(RUN_CHECKS_SCRIPT),
            "-c", f"TestEcho:{sys.executable} -c \"print('CHECK_SUCCESS')\"",
            "--cwd", self.test_dir
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("RESULTADO GLOBAL: EXITOSO (PASS)", res.stdout)
        # Verificar que se creó el directorio de logs
        runs_dir = Path(self.test_dir) / ".luna" / "runs"
        self.assertTrue(runs_dir.exists())

    def test_run_checks_failure_stops_cleanly(self):
        cmd = [
            sys.executable, str(RUN_CHECKS_SCRIPT),
            "-c", f"FailingTest:{sys.executable} -c \"import sys; sys.exit(2)\"",
            "--cwd", self.test_dir
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 1)
        self.assertIn("FAIL (code 2", res.stdout)
        self.assertIn("FALLIDO (FAIL)", res.stdout)

    def test_run_checks_multiple_steps_sequential(self):
        cmd = [
            sys.executable, str(RUN_CHECKS_SCRIPT),
            "-c", f"Step1:{sys.executable} -c \"print('Step 1 complete')\"",
            "-c", f"Step2:{sys.executable} -c \"print('Step 2 complete')\"",
            "--cwd", self.test_dir
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("Step1 ... PASS", res.stdout)
        self.assertIn("Step2 ... PASS", res.stdout)

    def test_run_checks_with_guard_verification(self):
        # Inicializar git repo para probar guard integrado
        subprocess.run(["git", "init"], cwd=self.test_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Tester"], cwd=self.test_dir, check=True)
        subprocess.run(["git", "config", "user.email", "tester@test.local"], cwd=self.test_dir, check=True)

        target_file = Path(self.test_dir) / "app.py"
        target_file.write_text("print('hello')", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.test_dir, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=self.test_dir, check=True)

        snap_file = Path(self.test_dir) / ".luna" / "baseline.json"
        subprocess.run([sys.executable, str(GUARD_SCRIPT), "snapshot", "-f", str(snap_file), "--cwd", self.test_dir], check=True, capture_output=True)

        # Modificar archivo permitido
        target_file.write_text("print('hello modified')", encoding="utf-8")

        cmd = [
            sys.executable, str(RUN_CHECKS_SCRIPT),
            "-c", f"TestApp:{sys.executable} -c \"print('App test OK')\"",
            "--guard-allow", "app.py",
            "--guard-snapshot", str(snap_file),
            "--cwd", self.test_dir
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("[GUARD] Verificando frontera de archivos ... PASS", res.stdout)


if __name__ == "__main__":
    unittest.main()
