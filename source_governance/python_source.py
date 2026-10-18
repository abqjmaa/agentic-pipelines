"""
Validate Python statement layout and count physical code with tokenize and AST.
Only true docstrings and configured comment tokens are excluded, never SQL/data.
Returns counts and diagnostics without importing or executing inspected modules.
"""

import ast
import io
import re
import tokenize


def inspect_python(text, pattern):
    tree = ast.parse(text)
    tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    comments = set()
    code = set()
    issues = []
    lines = text.splitlines()
    docstrings = set()
    header = ast.get_docstring(tree, clean=False)
    if not header or tree.body[0].end_lineno <= tree.body[0].lineno:
        issues.append("1: missing multiline module responsibility header")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if ast.get_docstring(node, clean=False):
                first = node.body[0]
                docstrings.add((first.lineno, first.col_offset))
        if isinstance(node, ast.NamedExpr):
            issues.append(f"{node.lineno}: assignment expression combines actions")
        if isinstance(node, ast.Assign) and len(node.targets) > 1:
            issues.append(f"{node.lineno}: chained assignment combines actions")
        if isinstance(node, ast.stmt):
            prefix = lines[node.lineno - 1][:node.col_offset]
            if prefix.strip():
                issues.append(f"{node.lineno}: statement shares a line with another action")
            body = getattr(node, "body", None)
            if isinstance(body, list) and body and body[0].lineno == node.lineno:
                issues.append(f"{node.lineno}: put block body on its own line")
    ignored_types = {
        tokenize.ENCODING, tokenize.ENDMARKER, tokenize.NEWLINE,
        tokenize.NL, tokenize.INDENT, tokenize.DEDENT,
    }
    for token in tokens:
        if token.type in ignored_types:
            continue
        rows = set(range(token.start[0], token.end[0] + 1))
        if token.type == tokenize.COMMENT:
            if re.fullmatch(pattern, token.string, re.DOTALL):
                comments.update(rows)
            else:
                code.update(rows)
        elif token.type == tokenize.STRING and token.start in docstrings:
            if re.fullmatch(pattern, token.string, re.DOTALL):
                comments.update(rows)
            else:
                code.update(rows)
        else:
            code.update(rows)
            if token.type == tokenize.OP and token.string == ";":
                issues.append(f"{token.start[0]}: semicolon combines actions")
    # Preserve blank lines inside executable multiline strings as source lines.
    return len(code), issues
