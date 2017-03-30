__author__ = 'yetone'

from babeljs import execjs
from babeljs.source import get_abspath


class TransformError(Exception):
    pass


class Transformer(object):

    def __init__(self):
        path = get_abspath('babeljs/browser.js')
        try:
            self.context = execjs.compile(
                'var babel = require("{}");'.format(path)
            )
        except:
            raise TransformError()

    def transform_string(self, js_content, **opts):
        _opts = {
            'presets': ['es2015', 'stage-0', 'react']
        }
        _opts.update(opts)
        try:
            return self.context.call('babel.transform', js_content, _opts)
        except execjs.ProgramError as e:
            raise TransformError(e.message[7:])

    def transform(self, js_path, **opts):
        with open(js_path, 'r') as f:
            return self.transform_string(f.read(), **opts)


def transform(js_path, **opts):
    return Transformer().transform(js_path, **opts)


def transform_string(js_content, **opts):
    return Transformer().transform_string(js_content, **opts)
