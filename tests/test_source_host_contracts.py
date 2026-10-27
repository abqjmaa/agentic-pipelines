"""
Test exact root-entrypoint contracts and HTML source-accounting enforcement.
Reuse isolated Git fixtures to check staged and working-tree behavior.
Exercise valid dispatchers, real comments and adversarial executable content.
"""

from source_governance.html_source import inspect_html
from tests.test_source_repository import SourceRepositoryTests


HTML_HEADER = '<!--\nLocal document and its dependencies.\nNo network side effects.\n-->\n'
HTML_PATTERN = r'<!--[\s\S]*?-->'
SHELL_HEADER = '#!/bin/sh\n# Stable dispatcher.\n# Delegates to governed source.\n'


class HostContractTests(SourceRepositoryTests):
    def entrypoint(self):
        self.config['languages']['.sh'] = {'adapter': 'shell', 'comment_pattern': r'#[^\n]*'}
        self.config['entrypoints'] = {
            'bootstrap.sh': {'purpose': 'Stable host bootstrap', 'delegate': 'src/module.py'},
        }
        self.write_config()
        self.write('bootstrap.sh', SHELL_HEADER + 'exec python3 src/module.py "$@"\n')
        self.write('README.md', '# Host\n\n- `bootstrap.sh`: Delegate to governed bootstrap.\n')

    def html(self, body):
        self.config['languages']['.html'] = {'adapter': 'html', 'comment_pattern': HTML_PATTERN}
        self.write_config()
        self.write('src/index.html', HTML_HEADER + body)
        self.write('src/README.md', '# Source\n\n- `module.py`: Test module.\n- `index.html`: Local page.\n')

    def test_exact_entrypoint_passes_worktree_and_index(self):
        self.entrypoint()
        self.assertEqual([], self.inspect()[1])
        self.git('add', '.')
        self.assertEqual([], self.inspect(staged=True)[1])
        self.write('other.sh', SHELL_HEADER)
        self.assertTrue(any('other.sh: source is outside' in issue for issue in self.inspect()[1]))

    def test_entrypoint_size_inventory_and_language_still_enforced(self):
        self.entrypoint()
        self.write('bootstrap.sh', SHELL_HEADER + 'echo value\n' * 401)
        self.assertTrue(any('bootstrap.sh: 401' in issue for issue in self.inspect()[1]))
        self.write('README.md', '# Missing inventory\n')
        self.assertTrue(any('missing description for bootstrap.sh' in issue for issue in self.inspect()[1]))
        del self.config['languages']['.sh']
        self.write_config()
        self.assertTrue(any('bootstrap.sh: no configured language' in issue for issue in self.inspect()[1]))

    def test_entrypoint_contract_refuses_broad_or_missing_targets(self):
        self.entrypoint()
        contract = self.config['entrypoints']['bootstrap.sh']
        for name in ('*.sh', '../bootstrap.sh', 'dir/boot.sh', '.hidden.sh'):
            self.config['entrypoints'] = {name: contract}
            self.write_config()
            with self.assertRaises(ValueError):
                self.inspect()
        self.config['entrypoints'] = {'bootstrap.sh': contract}
        for target in ('../src/module.py', '/tmp/other.py', 'other.py', 'src/missing.py'):
            contract['delegate'] = target
            self.write_config()
            with self.assertRaises(ValueError):
                self.inspect()

    def test_html_real_comments_and_inline_content(self):
        text = '<!doctype html>\n' + HTML_HEADER + '<p>Hello</p><!-- ignored -->\n'
        self.assertEqual((2, []), inspect_html(text, HTML_PATTERN))
        self.assertEqual(400, inspect_html(HTML_HEADER + '<p>Text</p>\n' * 400, '.*')[0])
        self.assertGreater(inspect_html(HTML_HEADER, 'NEVER')[0], 0)
        self.assertTrue(inspect_html('<p>No header</p>', HTML_PATTERN)[1])

    def test_html_comments_in_script_and_attributes_are_code(self):
        text = HTML_HEADER + '<script>\nconst text = "<!--\\nnot a comment\\n-->";\n</script>\n'
        self.assertEqual((3, []), inspect_html(text, HTML_PATTERN))
        text = HTML_HEADER + '<p title="<!-- not a comment -->">Text</p>\n'
        self.assertEqual((1, []), inspect_html(text, HTML_PATTERN))

    def test_html_executable_violations_fail(self):
        for body in ('<script>\na(); b();\n</script>', '<p onclick="a(); b()">Click</p>',
                     '<a href="javascript:a()">Click</a>', '<p style="color:red">Text</p>'):
            self.assertTrue(inspect_html(HTML_HEADER + body, HTML_PATTERN)[1])
        for body in ('<!-- unfinished', '<script>\na();'):
            with self.assertRaises(ValueError):
                inspect_html(HTML_HEADER + body, HTML_PATTERN)

    def test_html_limit_blocks_build_and_staged_cannot_hide_violation(self):
        self.html('<p>Text</p>\n' * 401)
        self.git('add', '.')
        self.write('src/index.html', HTML_HEADER + '<p>Fixed worktree only</p>\n')
        self.assertTrue(any('401' in issue for issue in self.inspect(staged=True)[1]))
        self.assertEqual([], self.inspect()[1])
        self.html('<p>Text</p>\n' * 401)
        result = self.invoke('governed_build.py', '--', 'echo', 'SHOULD_NOT_RUN')
        self.assertNotEqual(0, result.returncode)
        self.assertNotIn('SHOULD_NOT_RUN', result.stdout)

    def test_rcdata_comment_like_text_is_counted(self):
        for tag in ('textarea', 'title'):
            body = f'<{tag}>\n<!--\ntext, not comment\n-->\n</{tag}>\n'
            self.assertEqual((5, []), inspect_html(HTML_HEADER + body, HTML_PATTERN))
        with self.assertRaises(ValueError):
            inspect_html(HTML_HEADER + '<plaintext><!-- hidden', HTML_PATTERN)

    def test_entrypoint_layout_and_staged_failure_block(self):
        self.entrypoint()
        self.write('bootstrap.sh', SHELL_HEADER + 'echo a; echo b\n')
        self.git('add', '.')
        self.write('bootstrap.sh', SHELL_HEADER + 'echo repaired\n')
        self.assertTrue(any('split shell actions' in issue for issue in self.inspect(staged=True)[1]))
        self.assertEqual([], self.inspect()[1])

    def test_html_inventory_and_unknown_language_remain_required(self):
        self.html('<p>Text</p>\n')
        self.write('src/README.md', '# Source\n\n- `module.py`: Test module.\n')
        self.assertTrue(any('missing description for index.html' in issue for issue in self.inspect()[1]))
        self.config['languages']['.html']['adapter'] = 'unknown'
        self.write_config()
        with self.assertRaises(ValueError):
            self.inspect()

    def test_embedded_multiline_literal_blank_lines_still_count(self):
        body = '<script>\nconst text = `one\n\nthree`;\n</script>\n'
        self.assertEqual((5, []), inspect_html(HTML_HEADER + body, HTML_PATTERN))

    def test_entrypoint_invalid_language_map_fails_closed(self):
        self.entrypoint()
        self.config['languages'] = None
        self.write_config()
        with self.assertRaises(ValueError):
            self.inspect()
