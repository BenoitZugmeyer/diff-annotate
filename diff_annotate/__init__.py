import sys
import os.path
import re
import json
import shlex
from collections import namedtuple, defaultdict

import docutils.core
import click
from pygments import highlight, token
from pygments.lexers import DiffLexer
from pygments.formatters import HtmlFormatter


class Lexer(DiffLexer):

    tokens = {
        'root': (
            [(r'(?:>[^\n]*\n)+', token.Comment.Multiline)] +
            DiffLexer.tokens['root']
        ),
    }


class Formatter(HtmlFormatter):

    def _format_lines(self, tokensource):
        for ttype, value in tokensource:
            if ttype == token.Comment.Multiline:
                value = re.sub(r'^> ?', '', value, flags=re.M)
                fragments = docutils.core.publish_parts(value,
                                                        writer_name='html')
                value = fragments['html_body']
                yield 1, '<div class="annotation-comment">' + value + \
                    '</div>'
            else:
                yield from super()._format_lines(((ttype, value),))


def formatHTML(diff, annotations):
    formatter = Formatter(lineanchors='line')

    diff = highlight(diff, Lexer(), formatter)

    return r'''
<!DOCTYPE html>
<html>
<head>
    <title></title>
    <meta charset="utf-8" />
    <style type="text/css">
        body {{
            margin: 0;
        }}

        h1 {{
            font-size: 1.5em;
        }}

        h2 {{
            font-size: 1.3em;
        }}

        .highlight {{
            max-width: 50em;
            margin: 0 auto;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
            padding: 5px 10px;
            background-color: #eee;
            white-space: pre-wrap;
            height: 100vh;
            overflow: auto;
            box-sizing: border-box;
        }}

        .highlight pre {{
            margin: 0;
        }}

        {style}

        .annotation-comment {{
            display: block;
            background-color: #FEFAAD;
            white-space: normal;
            padding: 5px 10px;
            margin: 5px -10px;
        }}

        .annotation-comment .document > * {{
            margin: 0;
        }}

        .annotation-comment .document > * + * {{
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    {diff}
    <script type="text/annotations">
    {annotations}
    </script>
</body>
</html>
'''.format(style=formatter.get_style_defs(),
           diff=diff,
           annotations=encode_annotations(annotations))


chunk_re = re.compile(r'@@\s*-(\d+),\d+\s+\+(?:(\d+),)?\d+\s*@@')


Annotation = namedtuple('Annotation', ['file', 'add', 'line', 'comment'])


def parse_file_name(line):
    lex = shlex.shlex(line, posix=True)
    return next(lex)


def iter_diff(diff):
    add_file = None
    del_file = None
    chunk = None
    extra_index = del_index = add_index = 0

    for line in diff.split('\n'):

        if line.startswith('--- '):
            del_file = parse_file_name(line[4:])
            yield ('filename', line, (False, del_file))
            chunk = None

        elif line.startswith('+++ '):
            add_file = parse_file_name(line[4:])
            yield ('filename', line, (True, add_file))
            chunk = None

        elif line.startswith('@@'):
            chunk = tuple(int(l) if l else 0
                          for l in chunk_re.match(line).groups())
            yield ('chunk', line, (chunk,))
            add_index = del_index = 0

        elif chunk and line.startswith('+'):
            yield ('diffline', line, (add_file, True, chunk[1] + add_index))
            add_index += 1

        elif chunk and (line.startswith(' ') or line.startswith('-')):
            yield ('diffline', line, (del_file, False, chunk[0] + del_index))
            del_index += 1
            if line.startswith(' '):
                add_index += 1

        elif line.startswith('>'):
            yield ('comment', line, (line[1:].strip(),))

        else:
            yield ('extra', line, (extra_index,))
            extra_index += 1


def parse_annotations_in_diff(diff):
    result = []

    diffline = (None, False, -1)

    for type, line, infos in iter_diff(diff):

        if type == 'diffline':
            diffline = infos

        elif type == 'extra':
            diffline = (None, False, infos[0])

        elif type == 'comment':
            result.append(Annotation(
                file=diffline[0],
                add=diffline[1],
                line=diffline[2],
                comment=infos[0],
            ))

    return result


def parse_annotations_in_html(html):
    match = re.search(r'<script type="text/annotations">(.*?)</script>',
                      html,
                      re.S)
    return decode_annotations(match.group(1)) if match else []


def decode_annotations(annotations):
    annotations = annotations.strip()
    return [Annotation(*a) for a in json.loads(annotations)]\
        if annotations else []


def encode_annotations(annotations):
    return json.dumps(annotations, indent=2)


def sort_annotations(annotations):
    result = defaultdict(list)

    for a in annotations:
        result[(a.file, a.add, a.line)].append(a.comment)

    return result


def insert_annotations(diff, annotations):
    annotations = sort_annotations(annotations)
    lines = []

    def add_annotations(key):
        if key in annotations:
            for comment in annotations[key]:
                lines.append('> ' + comment)

    add_annotations((None, False, -1))

    for type, line, infos in iter_diff(diff):
        lines.append(line)

        if type == 'diffline':
            add_annotations(infos)

        elif type == 'extra':
            add_annotations((None, False, infos[0]))

    return '\n'.join(lines)


@click.command(help=r'''
               Generate a HTML file from a diff file and some annotations. It
               needs two arguments:

                 INPUT:  a path to an existing diff file to annotate.

                 OUTPUT: a path to an HTML file.

               The input file will be displayed to the default editor
               ($EDITOR), letting the user to annotate it by inserting lines
               starting with "greater than" character (>).

               Annotations are formatted with reStructuredText.

               The output file will then be written by formatting the diff code
               and inserting the annotations.

               The annotations are stored in the output file in a hidden field.
               If the output file exists, annotations are restored and inserted
               in the diff edition.

               Usages examples:

               $ diff-annotate a_file.diff my_review.html

               In bash and compatible shells, you can use this to create a fake
               diff file from a given command:

               $ diff-annotate <(git diff -w HEAD^) my_review.html

               ''')
@click.argument('input')
@click.argument('output')
def main(input, output):

    with open(input, 'r') as fp:
        diff = fp.read()

    exists = os.path.isfile(output)
    if exists:
        with open(output, 'r') as fp:
            annotations = parse_annotations_in_html(fp.read())

        diff = insert_annotations(diff, annotations)

    mod_diff = click.edit(diff, extension='.diff')

    if not mod_diff:
        if exists:
            click.echo('No change, aborting')
            sys.exit(0)
        mod_diff = diff;

    annotations = parse_annotations_in_diff(mod_diff)
    html = formatHTML(mod_diff, annotations)

    with open(output, 'w') as fp:
        fp.write(html)

if __name__ == '__main__':
    main()
