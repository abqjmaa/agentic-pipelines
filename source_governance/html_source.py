"""
Account for HTML source using the standard-library HTML token parser.
Exclude only real matching HTML comments, never attribute or script literals.
Keep embedded source subject to layout checks and reject unsupported handlers.
"""

from html.parser import HTMLParser
import re

from .text_source import inspect_text


class HTMLSource(HTMLParser):
    def __init__(self, text, pattern):
        super().__init__(convert_charrefs=False)
        self.text = text
        self.pattern = pattern
        self.masked = list(text)
        self.offsets = [0]
        for line in text.splitlines(keepends=True):
            self.offsets.append(self.offsets[-1] + len(line))
        self.headers = []
        self.issues = []
        self.embedded = None
        self.code_rows = set()

    def source_offset(self):
        row, column = self.getpos()
        return self.offsets[row - 1] + column

    def handle_comment(self, data):
        start = self.source_offset()
        end = self.text.find('-->', start + 4)
        if end < 0:
            raise ValueError('unterminated HTML comment')
        end += 3
        comment = self.text[start:end]
        prefix = ''.join(self.masked[:start])
        prefix = re.sub(r'\A\s*<!doctype\s+html\s*>', '', prefix, flags=re.I)
        if not prefix.strip():
            self.headers.append(comment)
        if re.fullmatch(self.pattern, comment, re.DOTALL):
            for index in range(start, end):
                if self.masked[index] != '\n':
                    self.masked[index] = ' '

    def handle_starttag(self, tag, attrs):
        row = self.getpos()[0]
        for name, value in attrs:
            if name.startswith('on') or name == 'style':
                self.issues.append(f'{row}: move inline handler/style to governed source')
            if value and re.match(r'\s*javascript\s*:', value, re.I):
                self.issues.append(f'{row}: move executable URL to governed source')
        if tag in {'xmp', 'iframe', 'noembed', 'noframes', 'plaintext'}:
            raise ValueError('unsupported raw-text HTML element')
        if tag in {'textarea', 'title'}:
            self.set_cdata_mode(tag)
        if tag in {'script', 'style'}:
            if self.embedded is not None:
                raise ValueError('nested embedded source is unsupported')
            self.embedded = (tag, self.source_offset() + len(self.get_starttag_text()))

    def handle_startendtag(self, tag, attrs):
        if tag in {'script', 'style'}:
            raise ValueError('self-closing embedded source is unsupported')
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if self.embedded is None or self.embedded[0] != tag:
            return
        start = self.embedded[1]
        body = self.text[start:self.source_offset()]
        # Embedded bytes count conservatively in the HTML file, including
        # comments. The C-style lexer checks layout without treating HTML
        # delimiters inside JavaScript strings as markup comments.
        rows = set()
        _, findings = inspect_text(body, 'cstyle', r'(?s:/\*.*?\*/|//[^\n]*)', counted_rows=rows)
        base = self.text[:start].count('\n')
        self.code_rows.update(base + row for row in rows)
        for finding in findings:
            if 'missing multiline responsibility header' not in finding:
                line, message = finding.split(':', 1)
                self.issues.append(f'{base + int(line)}:{message}')
        self.embedded = None

    def handle_data(self, data):
        if self.embedded is None and self.cdata_elem is None and '<!--' in data:
            raise ValueError('unterminated or malformed HTML comment')


def inspect_html(text, pattern):
    parser = HTMLSource(text, pattern)
    parser.feed(text)
    parser.close()
    if parser.embedded is not None:
        raise ValueError('unclosed embedded script/style source')
    header = '\n'.join(parser.headers)
    if len(header.splitlines()) < 2 or not any(char.isalpha() for char in header):
        parser.issues.append('1: missing multiline responsibility header')
    for row, line in enumerate(''.join(parser.masked).splitlines(), 1):
        if line.strip():
            parser.code_rows.add(row)
    return len(parser.code_rows), parser.issues
