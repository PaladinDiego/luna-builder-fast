#!/usr/bin/env python3
"""
test_lf.py — Tests unitarios para scripts/lf.py en Luna Builder Fast.
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
LF_SCRIPT = SCRIPT_DIR / "lf.py"


class TestLFDispatcher(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="lf_test_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_cycle_detection(self):
        tasks = [
            {"id": "A", "depends_on": ["B"], "mode": "codemod", "acceptance": f"{sys.executable} -c \"exit(0)\""},
            {"id": "B", "depends_on": ["A"], "mode": "codemod", "acceptance": f"{sys.executable} -c \"exit(0)\""}
        ]
        tf = Path(self.test_dir) / "tasks_cycle.json"
        tf.write_text(json.dumps(tasks), encoding="utf-8")

        res = subprocess.run([sys.executable, str(LF_SCRIPT), str(tf), "--cwd", self.test_dir], capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("ciclos o dependencias circulares", res.stderr or res.stdout)

    def test_missing_dependency_fails_validation(self):
        tasks = [
            {"id": "A", "depends_on": ["NON_EXISTENT"], "mode": "codemod", "acceptance": f"{sys.executable} -c \"exit(0)\""}
        ]
        tf = Path(self.test_dir) / "tasks_missing_dep.json"
        tf.write_text(json.dumps(tasks), encoding="utf-8")

        res = subprocess.run([sys.executable, str(LF_SCRIPT), str(tf), "--cwd", self.test_dir], capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("no existe en el archivo de tareas", res.stderr or res.stdout)

    def test_dag_linear_execution(self):
        tasks = [
            {
                "id": "task_create",
                "depends_on": [],
                "mode": "codemod",
                "acceptance": f"{sys.executable} -c \"import pathlib; pathlib.Path('marker.txt').write_text('OK')\""
            },
            {
                "id": "task_read",
                "depends_on": ["task_create"],
                "mode": "codemod",
                "acceptance": f"{sys.executable} -c \"import pathlib; assert pathlib.Path('marker.txt').read_text() == 'OK'\""
            }
        ]
        tf = Path(self.test_dir) / "tasks_dag.json"
        tf.write_text(json.dumps(tasks), encoding="utf-8")

        res = subprocess.run([sys.executable, str(LF_SCRIPT), str(tf), "--cwd", self.test_dir, "--workers", "2"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("Tareas completadas: 2/2", res.stdout)

    def test_dag_parallel_speedup(self):
        tasks = [
            {
                "id": "sleep_1",
                "depends_on": [],
                "mode": "codemod",
                "acceptance": f"{sys.executable} -c \"import time; time.sleep(0.2)\""
            },
            {
                "id": "sleep_2",
                "depends_on": [],
                "mode": "codemod",
                "acceptance": f"{sys.executable} -c \"import time; time.sleep(0.2)\""
            }
        ]
        tf = Path(self.test_dir) / "tasks_par.json"
        tf.write_text(json.dumps(tasks), encoding="utf-8")

        res = subprocess.run([sys.executable, str(LF_SCRIPT), str(tf), "--cwd", self.test_dir, "--workers", "2"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("Tareas completadas: 2/2", res.stdout)


if __name__ == "__main__":
    unittest.main()
