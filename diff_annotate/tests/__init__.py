from unittest import TestCase

import diff_annotate


class TestDiffAnotate(TestCase):

    def test_iter_diff_simple(self):

        result = list(diff_annotate.iter_diff(r'''
--- "file a"       2014-12-30 18:39:18.682725526 +0100
+++ "file \" b"       2014-12-30 18:39:30.212509006 +0100
@@ -1,5 +1,4 @@
 foo
 bar
-some line to remove
-this one too
> this is a comment
+this is a new line
 baz
'''
        ))

        self.assertEqual(result, [
            ('extra', '', tuple()),
            ('filename', '--- "file a"       2014-12-30 18:39:18.682725526 +0100', (False, 'file a')),
            ('filename', '+++ "file \\" b"       2014-12-30 18:39:30.212509006 +0100', (True, 'file " b')),
            ('chunk', '@@ -1,5 +1,4 @@', ((1, 1),)),
            ('diffline', ' foo', ('file a', False, 1)),
            ('diffline', ' bar', ('file a', False, 2)),
            ('diffline', '-some line to remove', ('file a', False, 3)),
            ('diffline', '-this one too', ('file a', False, 4)),
            ('comment', '> this is a comment', ('this is a comment',)),
            ('diffline', '+this is a new line', ('file " b', True, 3)),
            ('diffline', ' baz', ('file a', False, 5)),
            ('extra', '', tuple()),
        ])

    def test_parse_file_name(self):
        self.assertEqual(
            diff_annotate.parse_file_name('"foo bar" blah blih'),
            'foo bar'
        )

        self.assertEqual(
            diff_annotate.parse_file_name('foo blah blih'),
            'foo'
        )

        self.assertEqual(
            diff_annotate.parse_file_name(r'foo\ bar blah blih'),
            'foo bar'
        )


    def test_parse_annotations_in_diff(self):
        annotations = diff_annotate.parse_annotations_in_diff(r'''
> header comment
> this is another one
--- filea       2014-12-30 18:39:18.682725526 +0100
+++ fileb       2014-12-30 18:39:30.212509006 +0100
@@ -1,5 +1,4 @@
 foo
 bar
-some line to remove
-this one too
> this is a comment
+this is a new line
> this is a comment 2
baz
''')

        self.assertEqual(annotations, [
            diff_annotate.Annotation(None, False, 0, 'header comment'),
            diff_annotate.Annotation(None, False, 0, 'this is another one'),
            diff_annotate.Annotation('filea', False, 4, 'this is a comment'),
            diff_annotate.Annotation('fileb', True, 3, 'this is a comment 2'),
        ])

    def test_parse_annotations_in_html(self):
        annotations = diff_annotate.parse_annotations_in_html(r'''
blih
blah
<script>
oeu
</script>

<script type="text/annotations">
    [
  [
    null,
    false,
    0,
    "Hey!"
  ],
  [
    "filea",
    true,
    4,
    "oyo"
  ]
]
</script>
''')
        self.assertEqual(annotations, [
            diff_annotate.Annotation(None, False, 0, 'Hey!'),
            diff_annotate.Annotation('filea', True, 4, 'oyo'),
        ])

    def test_insert_annotations(self):
        annotations = [
            diff_annotate.Annotation(None, False, 0, 'header comment'),
            diff_annotate.Annotation(None, False, 0, 'this is another one'),
            diff_annotate.Annotation('filea', False, 4, 'this is a comment'),
            diff_annotate.Annotation('fileb', True, 3, 'this is a comment 2'),
        ]

        output = diff_annotate.insert_annotations(r'''
--- filea       2014-12-30 18:39:18.682725526 +0100
+++ fileb       2014-12-30 18:39:30.212509006 +0100
@@ -1,5 +1,4 @@
 foo
 bar
-some line to remove
-this one too
+this is a new line
baz
''', annotations)

        self.assertEqual(output, r'''> header comment
> this is another one

--- filea       2014-12-30 18:39:18.682725526 +0100
+++ fileb       2014-12-30 18:39:30.212509006 +0100
@@ -1,5 +1,4 @@
 foo
 bar
-some line to remove
-this one too
> this is a comment
+this is a new line
> this is a comment 2
baz
''')
