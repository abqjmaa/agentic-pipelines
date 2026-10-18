"""
Verify host software-build VS Code examples and their shared failing gate.
Check task/launch mappings and execute the adapted native Windows wrapper locally.
Use isolated host fixtures; no framework pipeline or hosted workflow is created.
"""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import yaml


FRAMEWORK = Path(__file__).resolve().parents[1]
EXAMPLES = FRAMEWORK / 'templates/vscode'
HEADER = '"""\nHost fixture responsibility and interface.\nTemporary test effects only.\n"""\n'


class SoftwareBuildEntrypointTests(unittest.TestCase):
    def test_task_and_launch_use_same_native_wrapper_once(self):
        tasks = json.loads((EXAMPLES / 'software-build.tasks.example.json').read_text(encoding='utf-8'))
        launch = json.loads((EXAMPLES / 'software-build.launch.example.json').read_text(encoding='utf-8'))
        task = tasks['tasks'][0]
        main = launch['configurations'][0]
        self.assertEqual(task['label'], main['name'])
        self.assertEqual(task['presentation']['reveal'], 'always')
        self.assertNotIn('preLaunchTask', main)
        self.assertIn('PATH_TO_SOFTWARE_BUILD.sh', task['args'][0])
        self.assertEqual(1, main['command'].count('PATH_TO_SOFTWARE_BUILD.sh'))
        self.assertIn('${workspaceFolder}\\PATH_TO_SOFTWARE_BUILD.ps1', task['windows']['args'])
        self.assertEqual(1, main['windows']['command'].count('PATH_TO_SOFTWARE_BUILD.ps1'))

    def test_both_native_examples_bootstrap_then_gate_build(self):
        for extension in ('sh', 'ps1'):
            text = (EXAMPLES / f'software-build.example.{extension}').read_text(encoding='utf-8')
            self.assertEqual(1, text.count('bootstrap.py'))
            self.assertEqual(1, text.count('scripts/governed_build.py'))
            self.assertLess(text.index('bootstrap.py'), text.index('scripts/governed_build.py'))
            self.assertLess(text.index('scripts/governed_build.py'), text.index('REPLACE_BUILD_COMMAND'))

    @unittest.skipUnless(shutil.which('powershell.exe'), 'PowerShell example requires Windows PowerShell')
    def test_native_host_path_blocks_invalid_source_and_preserves_build_status(self):
        with tempfile.TemporaryDirectory(prefix='host build ') as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', str(root)], check=True, capture_output=True)
            for folder in ('src', 'scripts', '.vscode'):
                (root / folder).mkdir()
            config = yaml.safe_load((FRAMEWORK / 'api.sample.yaml').read_text(encoding='utf-8'))['code']
            config['roots'] = ['src', 'scripts']
            (root / 'api.sample.yaml').write_text(yaml.safe_dump({'code': config}), encoding='utf-8')
            module = root / 'src/module.py'
            module.write_text(HEADER + 'value = 1\n' * 401, encoding='utf-8')
            (root / 'src/build.py').write_text(HEADER + 'from pathlib import Path\nPath("build-ran").touch()\nraise SystemExit(7)\n', encoding='utf-8')
            (root / 'src/README.md').write_text('- `module.py`: Fixture value.\n- `build.py`: Fixture build with status 7.\n', encoding='utf-8')
            (root / 'scripts/bootstrap.py').write_text(HEADER + 'from pathlib import Path\nPath("bootstrap-ran").touch()\n', encoding='utf-8')
            (root / 'scripts/README.md').write_text('- `bootstrap.py`: Mark prerequisite execution.\n- `build.ps1`: Bootstrap and gate the fixture build.\n', encoding='utf-8')
            text = (EXAMPLES / 'software-build.example.ps1').read_text(encoding='utf-8')
            python = "'" + Path(sys.executable).as_posix().replace("'", "''") + "'"
            wrapper = "'" + (FRAMEWORK / 'scripts/governed_build.py').as_posix().replace("'", "''") + "'"
            text = text.replace('REPLACE_PYTHON_COMMAND', python)
            text = text.replace('REPLACE_BUILD_COMMAND', python)
            text = text.replace('"$PSScriptRoot/../agentic-pipelines/scripts/governed_build.py"', wrapper)
            entry = root / 'scripts/build.ps1'
            entry.write_text(text, encoding='utf-8')
            command = ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(entry), 'src/build.py']
            failed = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=30)
            self.assertNotEqual(0, failed.returncode)
            self.assertIn('401', failed.stderr)
            self.assertTrue((root / 'bootstrap-ran').exists())
            self.assertFalse((root / 'build-ran').exists())
            module.write_text(HEADER + 'value = 1\n', encoding='utf-8')
            built = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=30)
            self.assertEqual(7, built.returncode, built.stderr)
            self.assertTrue((root / 'build-ran').exists())
            (root / 'build-ran').unlink()
            (root / 'scripts/bootstrap.py').write_text(HEADER + 'raise SystemExit(9)\n', encoding='utf-8')
            prerequisite_failure = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=30)
            self.assertEqual(9, prerequisite_failure.returncode)
            self.assertFalse((root / 'build-ran').exists())

    def test_framework_has_no_actions_workflow_or_registry_requirement(self):
        self.assertFalse(list((FRAMEWORK / '.github/workflows').glob('*.yml')))
        self.assertFalse(list((FRAMEWORK / '.github/workflows').glob('*.yaml')))
        code = yaml.safe_load((FRAMEWORK / 'api.sample.yaml').read_text(encoding='utf-8'))['code']
        self.assertNotIn('build_pipelines', code)
        policy = (FRAMEWORK / 'references/source_build_governance.md').read_text(encoding='utf-8')
        self.assertIn('submodule itself is not', policy)
        self.assertIn('canonical ordinary pipeline', policy)
