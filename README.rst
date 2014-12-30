=============
diff-annotate
=============

Generates a HTML file from a diff file and some annotations.

Example
=======

.. code:: bash

    $ diff -u filea fileb
    --- filea       2014-12-30 18:39:18.682725526 +0100
    +++ fileb       2014-12-30 18:39:30.212509006 +0100
    @@ -1,5 +1,4 @@
     foo
     bar
    -some line to remove
    -this one too
    +this is a new line
     baz

    $ diff-annotate <(diff -u filea fileb) review.html
    # A wild editor appears!
    # Add something like "> Oh noes, you should not remove this line" 
    # below the line "-some line to remove".

    # You can then see the result in your favorite browser:
    $ firefox review.html

.. image:: example.png

.. code:: bash

    # You can edit annotation if you execute the same command (annotations are
    # store in the output file)
    $ diff-annotate <(diff -u filea fileb) review.html

Installation
============

With pip and python 3::

    $ pip install https://github.com/BenoitZugmeyer/diff-annotate/archive/master.zip
