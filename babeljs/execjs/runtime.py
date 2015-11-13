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
import io
import json
import re
import os
from subprocess import Popen, PIPE, STDOUT
import tempfile
from .exceptions import RuntimeError, ProgramError, RuntimeUnavailable
from .utils import json2_source, which


def encode_unicode_codepoints(str):
    r"""
    >>> encode_unicode_codepoints("a") == 'a'
    True
    >>> ascii = ''.join(chr(i) for i in range(0x80))
    >>> encode_unicode_codepoints(ascii) == ascii
    True
    >>> encode_unicode_codepoints('\u4e16\u754c') == '\\u4e16\\u754c'
    True
    """
    codepoint_format = '\\u{0:04x}'.format

    def codepoint(m):
        return codepoint_format(ord(m.group(0)))

    return re.sub('[^\x00-\x7f]', codepoint, str)


class Runtime(object):
    def __init__(self, name, command, runner_source, encoding='utf8'):
        self._name = name
        if isinstance(command, str):
            command = [command]
        self._command = command
        self._runner_source = runner_source
        self._encoding = encoding

    def __str__(self):
        return "{class_name}({runtime_name})".format(
            class_name=type(self).__name__,
            runtime_name=self._name,
        )

    @property
    def name(self):
        return self._name

    def exec_(self, source):
        if not self.is_available():
            raise RuntimeUnavailable()
        return self.Context(self).exec_(source)

    def eval(self, source):
        if not self.is_available():
            raise RuntimeUnavailable()
        return self.Context(self).eval(source)

    def compile(self, source):
        if not self.is_available():
            raise RuntimeUnavailable()
        return self.Context(self, source)

    def is_available(self):
        return self._binary() is not None

    def runner_source(self):
        return self._runner_source

    def _binary(self):
        """protected"""
        if not hasattr(self, "_binary_cache"):
            self._binary_cache = which(self._command)
        return self._binary_cache

    def _execfile(self, filename):
        """protected"""
        cmd = self._binary() + [filename]

        p = None
        try:
            p = Popen(cmd, stdout=PIPE, stderr=STDOUT)
            stdoutdata, stderrdata = p.communicate()
            ret = p.wait()
        finally:
            del p

        if ret == 0:
            return stdoutdata
        else:
            raise RuntimeError(stdoutdata)

    class Context(object):
        def __init__(self, runtime, source=''):
            self._runtime = runtime
            self._source = source

        def eval(self, source):
            if not source.strip():
                data = "''"
            else:
                data = "'('+" + json.dumps(source, ensure_ascii=True) + "+')'"

            code = 'return eval({data})'.format(data=data)
            return self.exec_(code)

        def exec_(self, source):
            if self._source:
                source = self._source + '\n' + source

            (fd, filename) = tempfile.mkstemp(prefix='babeljs', suffix='.js')
            os.close(fd)
            try:
                with io.open(filename, "w+", encoding=self._runtime._encoding) as fp:
                    fp.write(self._compile(source))
                output = self._runtime._execfile(filename)
            finally:
                os.remove(filename)

            output = output.decode(self._runtime._encoding)
            output = output.replace("\r\n", "\n").replace("\r", "\n")
            output = self._extract_result(output.split("\n")[-2])

            return output

        def call(self, identifier, *args):
            args = json.dumps(args)
            return self.eval("{identifier}.apply(this, {args})".format(identifier=identifier, args=args))

        def _compile(self, source):
            """protected"""
            runner_source = self._runtime.runner_source()

            replacements = {
                '#{source}': lambda: source,
                '#{encoded_source}': lambda: json.dumps(
                    "(function(){ " +
                    encode_unicode_codepoints(source) +
                    " })()"
                ),
                '#{json2_source}': json2_source,
            }

            pattern = "|".join(re.escape(k) for k in replacements)

            runner_source = re.sub(pattern, lambda m: replacements[m.group(0)](), runner_source)

            return runner_source

        def _extract_result(self, output_last_line):
            """protected"""
            if not output_last_line:
                status = value = None
            else:
                ret = json.loads(output_last_line)
                if len(ret) == 1:
                    ret = [ret[0], None]
                status, value = ret

            if status == "ok":
                return value
            elif value and value.startswith('SyntaxError:'):
                raise RuntimeError(value)
            else:
                raise ProgramError(value)


class PyV8Runtime(object):
    def __init__(self):
        try:
            import PyV8
        except ImportError:
            self._is_available = False
        else:
            self._is_available = True

    @property
    def name(self):
        return "PyV8"

    def exec_(self, source):
        return self.Context().exec_(source)

    def eval(self, source):
        return self.Context().eval(source)

    def compile(self, source):
        return self.Context(source)

    def is_available(self):
        return self._is_available

    class Context:
        def __init__(self, source=""):
            self._source = source

        def exec_(self, source):
            source = '''\
            (function() {{
                {0};
                {1};
            }})()'''.format(
                encode_unicode_codepoints(self._source),
                encode_unicode_codepoints(source)
            )
            source = str(source)

            import PyV8
            import contextlib
            #backward compatibility
            with contextlib.nested(PyV8.JSContext(), PyV8.JSEngine()) as (ctxt, engine):
                js_errors = (PyV8.JSError, IndexError, ReferenceError, SyntaxError, TypeError)
                try:
                    script = engine.compile(source)
                except js_errors as e:
                    raise RuntimeError(e)
                try:
                    value = script.run()
                except js_errors as e:
                    raise ProgramError(e)
                return self.convert(value)

        def eval(self, source):
            return self.exec_('return ' + encode_unicode_codepoints(source))

        def call(self, identifier, *args):
            args = json.dumps(args)
            return self.eval("{identifier}.apply(this, {args})".format(identifier=identifier, args=args))

        @classmethod
        def convert(cls, obj):
            from PyV8 import _PyV8
            if isinstance(obj, bytes):
                return obj.decode('utf8')
            if isinstance(obj, _PyV8.JSArray):
                return [cls.convert(v) for v in obj]
            elif isinstance(obj, _PyV8.JSFunction):
                return None
            elif isinstance(obj, _PyV8.JSObject):
                ret = {}
                for k in obj.keys():
                    v = cls.convert(obj[k])
                    if v is not None:
                        ret[cls.convert(k)] = v
                return ret
            else:
                return obj
