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

'''
    Run JavaScript code from Python.

    PyExecJS is a porting of ExecJS from Ruby.
    PyExecJS automatically picks the best runtime available to evaluate your JavaScript program,
    then returns the result to you as a Python object.

    A short example:

>>> import reactjs.execjs
>>> execjs.eval("'red yellow blue'.split(' ')")
['red', 'yellow', 'blue']
>>> ctx = execjs.compile("""
...     function add(x, y) {
...         return x + y;
...     }
... """)
>>> ctx.call("add", 1, 2)
3
'''

# changes from PyExecJS:
# * in javascript bootstrap do
#     result = program().code;
#   instead of
#     result = program();
#   so result is the transpiled code
#   (untested on all platform but nodejs)
# * the temp js file is prefixed as babeljs and not execjs

from __future__ import absolute_import, division, print_function, unicode_literals
import os
import os.path
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
from .exceptions import Error, RuntimeError, ProgramError, RuntimeUnavailable
from .runtime import Runtime, PyV8Runtime

__all__ = [
    "get", "register", "runtimes", "get_from_environment", "exec_", "eval", "compile",
    "Runtime", "Context",
    "Error", "RuntimeError", "ProgramError", "RuntimeUnavailable",
]


def register(name, runtime):
    '''Register a JavaScript runtime.'''
    _runtimes[name] = runtime


def get(name=None):
    """
    Return a appropriate JavaScript runtime.
    If name is specified, return the runtime.
    """
    if name is None:
        return _auto_detect()

    try:
        runtime = runtimes()[name]
    except KeyError:
        raise RuntimeUnavailable("{name} runtime is not defined".format(name=name))
    else:
        if not runtime.is_available():
            raise RuntimeUnavailable(
                "{name} runtime is not available on this system".format(name=runtime.name))
        return runtime


def runtimes():
    """return a dictionary of all supported JavaScript runtimes."""
    return dict(_runtimes)


def available_runtimes():
    """return a dictionary of all supported JavaScript runtimes which is usable"""
    return dict((name, runtime) for name, runtime in _runtimes.items() if runtime.is_available())


def _auto_detect():
    runtime = get_from_environment()
    if runtime is not None:
        return runtime

    for runtime in _runtimes.values():
        if runtime.is_available():
            return runtime

    raise RuntimeUnavailable("Could not find a JavaScript runtime.")


def get_from_environment():
    '''
        Return the JavaScript runtime that is specified in EXECJS_RUNTIME environment variable.
        If EXECJS_RUNTIME environment variable is empty or invalid, return None.
    '''
    try:
        name = os.environ["EXECJS_RUNTIME"]
    except KeyError:
        return None

    if not name:
        #name is None or empty str
        return None
    return get(name)


def eval(source):
    return get().eval(source)


def exec_(source):
    return get().exec_(source)


def compile(source):
    return get().compile(source)


_runtimes = OrderedDict()
_runtimes['PyV8'] = PyV8Runtime()

for command in ["nodejs", "node"]:
    _runtimes["Node"] = runtime = Runtime(
        name="Node.js (V8)",
        command=[command],
        encoding='UTF-8',
        runner_source=r"""(function(program, execJS) { execJS(program) })(function() { #{source}
}, function(program) {
  var output;
  var print = function(string) {
    process.stdout.write('' + string + '\n');
  };
  try {
    result = program().code;
    print('');
    if (typeof result == 'undefined' && result !== null) {
      print('["ok"]');
    } else {
      try {
        print(JSON.stringify(['ok', result]));
      } catch (err) {
        print(err);
        print('["err"]');
      }
    }
  } catch (err) {
    print(JSON.stringify(['err', '' + err]));
  }
});""",
    )
    if runtime.is_available():
        break


_runtimes['JavaScriptCore'] = Runtime(
    name="JavaScriptCore",
    command=["/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Resources/jsc"],
    runner_source=r"""(function(program, execJS) { execJS(program) })(function() {
  return eval(#{encoded_source});
}, function(program) {
  var output;
  try {
    result = program().code;
    print("");
    if (typeof result == 'undefined' && result !== null) {
      print('["ok"]');
    } else {
      try {
        print(JSON.stringify(['ok', result]));
      } catch (err) {
        print('["err"]');
      }
    }
  } catch (err) {
    print(JSON.stringify(['err', '' + err]));
  }
});
"""
)


_runtimes['SpiderMonkey'] = _runtimes['Spidermonkey'] = Runtime(
    name="SpiderMonkey",
    command=["js"],
    runner_source=r"""(function(program, execJS) { execJS(program) })(function() { #{source}
}, function(program) {
  #{json2_source}
  var output;
  try {
    result = program().code;
    print("");
    if (typeof result == 'undefined' && result !== null) {
      print('["ok"]');
    } else {
      try {
        print(JSON.stringify(['ok', result]));
      } catch (err) {
        print('["err"]');
      }
    }
  } catch (err) {
    print(JSON.stringify(['err', '' + err]));
  }
});
""")


_runtimes['JScript'] = Runtime(
    name="JScript",
    command=["cscript", "//E:jscript", "//Nologo"],
    encoding="ascii",
    runner_source=r"""(function(program, execJS) { execJS(program) })(function() {
  return eval(#{encoded_source});
}, function(program) {
  #{json2_source}
  var output, print = function(string) {
    string = string.replace(/[^\x00-\x7f]/g, function(ch){
      return '\\u' + ('0000' + ch.charCodeAt(0).toString(16)).slice(-4);
    });
    WScript.Echo(string);
  };
  try {
    result = program().code;
    print("")
    if (typeof result == 'undefined' && result !== null) {
      print('["ok"]');
    } else {
      try {
        print(JSON.stringify(['ok', result]));
      } catch (err) {
        print('["err"]');
      }
    }
  } catch (err) {
    print(JSON.stringify(['err', err.name + ': ' + err.message]));
  }
});
"""
)


for _name, _command in [
    ['PhantomJS', 'phantomjs'],
    ['SlimerJS', 'slimerjs'],
]:
    _runtimes[_name] = Runtime(
        name=_name,
        command=[_command],
        runner_source=r"""
(function(program, execJS) { execJS(program) })(function() {
  return eval(#{encoded_source});
}, function(program) {
  var output;
  var print = function(string) {
    console.log('' + string);
  };
  try {
    result = program().code;
    print('')
    if (typeof result == 'undefined' && result !== null) {
      print('["ok"]');
    } else {
      try {
        print(JSON.stringify(['ok', result]));
      } catch (err) {
        print('["err"]');
      }
    }
  } catch (err) {
    print(JSON.stringify(['err', '' + err]));
  }
});
phantom.exit();
""")
