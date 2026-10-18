"""
Exercise staged pre-commit enforcement and preservation of existing hooks.
Use temporary Git repositories and the trusted framework installer/checker.
Only fixture commits are attempted; no user repository is modified.
"""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import yaml


FRAMEWORK = Path(__file__).resolve().parents[1]
HEADER = '"""\nFixture responsibility and interface.\nNo side effects.\n"""\n'


class SourceHookTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.git('init', '-q')
        (self.root / 'src').mkdir()
        config = yaml.safe_load((FRAMEWORK / 'api.sample.yaml').read_text(encoding='utf-8'))['code']
        config['roots'] = ['src']
        (self.root / 'api.sample.yaml').write_text(yaml.safe_dump({'code': config}), encoding='utf-8')
        (self.root / 'src/README.md').write_text('- `module.py`: Fixture value.\n', encoding='utf-8')
        self.module = self.root / 'src/module.py'
        self.module.write_text(HEADER + 'value = 1\n', encoding='utf-8')

    def git(self, *args):
        return subprocess.run(
            ['git', '-C', str(self.root), *args], capture_output=True, text=True, timeout=20,
        )

    def installer(self, *args):
        return subprocess.run(
            [sys.executable, str(FRAMEWORK / 'scripts/install_source_governance_hook.py'), '--repo-root', str(self.root), *args],
            capture_output=True, text=True, timeout=20,
        )

    def commit(self):
        return self.git('-c', 'user.name=Governance Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')

    def test_hook_blocks_invalid_staged_source(self):
        self.assertEqual(0, self.installer().returncode)
        self.module.write_text(HEADER + 'value = 1\n' * 401, encoding='utf-8')
        self.assertEqual(0, self.git('add', '.').returncode)
        result = self.commit()
        self.assertNotEqual(0, result.returncode)
        self.assertIn('401', result.stderr)
        self.assertNotEqual(0, self.git('rev-parse', '--verify', 'HEAD').returncode)

    def test_valid_commit_and_idempotent_install(self):
        self.assertNotEqual(0, self.installer('--check').returncode)
        self.assertEqual(0, self.installer().returncode)
        hook = self.root / '.git/hooks/pre-commit'
        timestamp = hook.stat().st_mtime_ns
        self.assertEqual(0, self.installer().returncode)
        self.assertEqual(timestamp, hook.stat().st_mtime_ns)
        self.assertEqual(0, self.installer('--check').returncode)
        self.git('add', '.')
        result = self.commit()
        self.assertEqual(0, result.returncode, result.stderr)

    def test_existing_hook_is_preserved_and_chained(self):
        hook = self.root / '.git/hooks/pre-commit'
        original = '#!/bin/sh\nprintf existing-hook >&2\nexit 7\n'
        hook.write_text(original, encoding='utf-8', newline='\n')
        hook.chmod(hook.stat().st_mode | 0o111)
        self.assertEqual(0, self.installer().returncode)
        saved = hook.with_name('pre-commit.before-source-governance')
        self.assertEqual(original, saved.read_text(encoding='utf-8'))
        self.git('add', '.')
        result = self.commit()
        self.assertNotEqual(0, result.returncode)
        self.assertIn('existing-hook', result.stderr)

    def test_custom_hooks_path_is_respected(self):
        self.git('config', 'core.hooksPath', '.custom-hooks')
        self.assertEqual(0, self.installer().returncode)
        self.assertTrue((self.root / '.custom-hooks/pre-commit').exists())
        self.assertEqual(0, self.installer('--check').returncode)
