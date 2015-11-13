#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2007-2015, Raffaele Salmaso <raffaele@salmaso.org>
# Copyright (c) 2012 Omoto Kenji
# Copyright (c) 2011 Sam Stephenson
# Copyright (c) 2011 Josh Peek
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from __future__ import absolute_import, division, print_function, unicode_literals
import sys
import io
from argparse import ArgumentParser, Action, SUPPRESS
from babeljs import execjs


class PrintRuntimes(Action):
    def __init__(self, option_strings, dest=SUPPRESS, default=SUPPRESS, help=None):
        super(PrintRuntimes, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )

    def __call__(self, parser, namespace, values, option_string=None):
        buffer = io.StringIO()
        for name, runtime in sorted(execjs.runtimes().items()):
            if runtime.is_available():
                buffer.write(name + "\n")
        parser.exit(message=buffer.getvalue())


def main():
    parser = ArgumentParser()
    parser.add_argument('--print-available-runtimes', action=PrintRuntimes)
    parser.add_argument('-r', '--runtime', action='store', dest='runtime')
    parser.add_argument('-e', '--eval', action='store', dest='expr')
    parser.add_argument("--encoding", action="store", dest="files_encoding", default="utf8")
    parser.add_argument(nargs="*", action='store', dest='files')

    opts = parser.parse_args()

    runtime = execjs.get(opts.runtime)

    codes = []
    for f in opts.files:
        with io.open(f, encoding=opts.files_encoding) as fp:
            codes.append(fp.read())

    context = runtime.compile("\n".join(codes))
    if opts.expr:
        if isinstance(opts.expr, bytes):
            expr = opts.expr.decode()
        else:
            expr = opts.expr
        sys.stdout.write(repr(context.eval(expr)) + "\n")
    else:
        ret = context.eval(sys.stdin.read())
        sys.stdout.write(repr(ret) + "\n")

if "__main__" == __name__:
    main()
