from os import path
from unittest import TestCase

from babeljs import transformer
from timeit import default_timer
from collections import OrderedDict


ROOT = path.abspath(path.join(path.dirname(__file__), 'files'))


timings = OrderedDict()


class TestInvalidRuntime(TestCase):
    def test_invalid_runtime(self):
        with self.assertRaises(transformer.TransformError):
            transformer.transform_string("var a;", runtime='nonexistent')


class TestMiniRacer(TestCase):
    runtime = 'miniracer'

    def setUp(self):
        self.start_time = default_timer()

    def tearDown(self):
        timings[self.id()] = default_timer() - self.start_time

    def test_transform_string(self):
        code = transformer.transform_string('''
        const a = () => 233;
        const b = <div></div>;
        ''', runtime=self.runtime)
        self.assertEqual(
            '"use strict";\n\nvar a = function a() {\n        return 233;\n};'
            '\nvar b = React.createElement("div", null);',
            code
        )

    def test_transform(self):
        js_path = path.join(ROOT, 'test.js')
        code = transformer.transform(js_path, runtime=self.runtime)
        self.assertEqual('"use strict";\n\nvar a = 1;', code)

    def test_transform_vue_jsx(self):
        js_path = path.join(ROOT, 'test_vue_jsx.js')
        code = transformer.transform(
            js_path,
            runtime=self.runtime,
            **{
                'presets': ['es2015', 'stage-0'],
                'plugins': ['transform-decorators-legacy', 'transform-vue-jsx']
            }
        )
        with open(path.join(ROOT, 'result-test_vue_jsx.js'), 'r') as f:
            expected_code = f.read()
        self.assertEqual(expected_code, code)

    def test_invalid_js(self):
        with self.assertRaises(transformer.TransformError):
            transformer.transform_string('''
                invalid CODE; test(] /
            ''', runtime=self.runtime)

    def test_large_file(self):
        js_path = path.join(ROOT, 'large.js')
        code = transformer.transform(js_path, runtime=self.runtime)
        self.assertEqual(
            code[:22],
            '"use strict";var foo="'
        )

    def test_jquery(self):
        js_path = path.join(ROOT, 'jquery.js')
        transformer.transform(js_path, runtime=self.runtime)

    @classmethod
    def tearDownClass(cls):
        compare_timings()


class TestNode(TestMiniRacer):
    runtime = 'node'


def compare_timings():
    timing_header = False
    for test_id in timings:
        if 'MiniRacer' not in test_id:
            continue
        node_test_id = test_id.replace('MiniRacer', 'Node')
        if node_test_id not in timings:
            continue

        if not timing_header:
            timing_header = True
            print()
            print()
            print("PyMiniRacer speedup over Node.js subprocess:")

        name = test_id.split('.')[-1]
        label = name[:25] + (" " * (25 - len(name)))
        mini_racer_time = timings[test_id]
        node_time = timings[node_test_id]

        rel_s = mini_racer_time - node_time
        rel_pct = rel_s / node_time * 100
        if rel_pct > 0:
            msg = "{test_label}: {rel_pct}% slower (+{rel_ms}ms)"
        else:
            msg = "{test_label}: {rel_pct}% faster (-{rel_ms}ms)"

        print(msg.format(
            test_label=label,
            rel_pct=abs(round(rel_pct, 2)),
            rel_ms=abs(round(rel_s * 1000))
        ))
