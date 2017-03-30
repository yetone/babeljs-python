from os import path
from unittest import TestCase

from babeljs import transformer


ROOT = path.abspath(path.join(path.dirname(__file__), 'files'))


class TestTransformer(TestCase):
    def test_transform_string(self):
        code = transformer.transform_string('''
        const a = () => 233;
        const b = <div></div>;
        ''')
        self.assertEqual(
            '"use strict";\n\nvar a = function a() {\n        return 233;\n};'
            '\nvar b = React.createElement("div", null);',
            code
        )

    def test_transform(self):
        js_path = path.join(ROOT, 'test.js')
        code = transformer.transform(js_path)
        self.assertEqual('"use strict";\n\nvar a = 1;', code)

    def test_transform_vue_jsx(self):
        js_path = path.join(ROOT, 'test_vue_jsx.js')
        code = transformer.transform(js_path, **{
            'presets': ['es2015', 'stage-0'],
            'plugins': ['transform-decorators-legacy', 'transform-vue-jsx']}
        )
        self.assertEqual(open(
            path.join(ROOT, 'result-test_vue_jsx.js'), 'r'
        ).read(), code)
