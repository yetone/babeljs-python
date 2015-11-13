__author__ = 'yetone'

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.abspath(__file__))))

from os.path import abspath, join, dirname

from unittest import TestCase

from babeljs import transformer

ROOT = abspath(join(dirname(__file__), 'files'))


class TestTransformer(TestCase):
    def test_transform_string(self):
        code = transformer.transform_string('const a = () => 233')
        self.assertEqual(
            '"use strict";\n\nvar a = function a() {\n  return 233;\n};',
            code
        )

    def test_transform(self):
        path = join(ROOT, 'test.js')
        code = transformer.transform(path)
        self.assertEqual('"use strict";\n\nvar a = 1;', code)
