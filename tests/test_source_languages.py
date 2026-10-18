"""
Exercise language accounting at the 400-line boundary and adversarial literals.
Test parser-only validation of comments, docstrings and combined statements.
Fixtures remain in memory and never execute inspected source.
"""

import unittest

from source_governance.configuration import mapping
from source_governance.python_source import inspect_python
from source_governance.text_source import inspect_text


PATTERN = r'(?:#[^\n]*|(?s:""".*"""|\x27\x27\x27.*\x27\x27\x27))'
HEADER = '"""\nExplain module responsibilities.\nNo runtime effects.\n"""\n'


class SourceLanguageTests(unittest.TestCase):
    def test_boundary_400_and_401_counts(self):
        for expected in (400, 401):
            count, issues = inspect_python(HEADER + "value = 1\n" * expected, PATTERN)
            self.assertEqual(expected, count)
            self.assertEqual([], issues)

    def test_comments_blank_lines_and_inline_code(self):
        text = HEADER + '# ignored\n\nvalue = "# not a comment"  # inline\n'
        self.assertEqual((1, []), inspect_python(text, PATTERN))

    def test_sql_is_code_and_function_docstring_is_not(self):
        text = HEADER + 'query = """\nSELECT 1;\n\nSELECT 2;\n"""\n'
        self.assertEqual(5, inspect_python(text, PATTERN)[0])
        function = 'def example():\n    """\n    Function documentation.\n    """\n    return 1\n'
        self.assertEqual((2, []), inspect_python(HEADER + function, PATTERN))

    def test_broad_pattern_cannot_hide_code(self):
        self.assertEqual(401, inspect_python(HEADER + 'value = 1\n' * 401, '.*')[0])

    def test_pattern_must_match_before_comments_are_excluded(self):
        self.assertGreater(inspect_python(HEADER + '# not matched\n', 'NEVER')[0], 1)

    def test_combined_python_actions_fail(self):
        cases = ['x = 1; y = 2\n', 'a = b = 1\n', 'if (x := 1):\n    pass\n', 'if True: pass\n']
        for source in cases:
            with self.subTest(source=source):
                self.assertTrue(inspect_python(HEADER + source, PATTERN)[1])

    def test_normal_assignment_unpacking_and_semicolon_in_string_pass(self):
        text = HEADER + 'a, b = (1, 2)\nvalue = str(a)\nmessage = ";"\n'
        self.assertEqual((3, []), inspect_python(text, PATTERN))

    def test_header_is_mandatory_and_multiline(self):
        self.assertTrue(inspect_python('value = 1\n', PATTERN)[1])
        self.assertTrue(inspect_python('"""One line."""\nvalue = 1\n', PATTERN)[1])

    def test_cstyle_comments_inside_strings_remain_code(self):
        text = '/*\nModule responsibilities.\n*/\nconst char *s = "/* string */";\n'
        self.assertEqual((1, []), inspect_text(text, 'cstyle', r'(?s:/\*.*\*/|//[^\n]*)'))

    def test_cstyle_inline_comment_line_counts(self):
        text = '/*\nHeader.\n*/\nint x; /* comment\nend */\n'
        self.assertEqual(1, inspect_text(text, 'cstyle', r'(?s:/\*.*\*/|//[^\n]*)')[0])

    def test_powershell_block_and_inline_body(self):
        header = '<#\nResponsibilities.\n#>\n'
        pattern = r'(?s:<#.*#>|#[^\n]*)'
        self.assertEqual((1, []), inspect_text(header + '$value = 1\n', 'powershell', pattern))
        self.assertTrue(inspect_text(header + 'if ($true) { exit 1 }\n', 'powershell', pattern)[1])

    def test_unknown_adapters_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'unsupported'):
            inspect_text('source', 'unknown', '.*')

    def test_invalid_yaml_does_not_echo_private_values(self):
        with self.assertRaises(ValueError) as caught:
            mapping('secret: PRIVATE_SECRET\ncode: [unterminated')
        self.assertNotIn('PRIVATE_SECRET', str(caught.exception))
