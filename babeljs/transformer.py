from babeljs import execjs
from babeljs.source import get_abspath


class TransformError(Exception):
    pass


class Transformer(object):

    def __init__(self, **_opts):
        opts = {
            'presets': ['es2015', 'stage-0', 'react']
        }
        opts.update(_opts)
        plugins = opts.get('plugins', [])

        babel_path = get_abspath('babeljs/browser.js')

        codes = [
            'var babel = require("{}");'.format(babel_path)
        ]
        for plugin in plugins:
            if plugin == 'transform-vue-jsx':
                transform_vue_jsx_path = get_abspath('babeljs/babel-plugin-transform-vue-jsx.min.js')  # noqa
                codes.append(
                    'var transformVueJsx = require("{}");'
                    'babel.registerPlugin("{}", transformVueJsx);'.format(
                        transform_vue_jsx_path, plugin
                    )
                )
        try:
            self.opts = opts
            self.context = execjs.compile(''.join(codes))
        except:
            raise TransformError()

    def transform_string(self, js_content, **_opts):
        opts = dict(self.opts, **_opts)
        try:
            return self.context.call('babel.transform', js_content, opts)
        except execjs.ProgramError as e:
            raise TransformError(e.message[7:])

    def transform(self, js_path, **opts):
        with open(js_path, 'r') as f:
            return self.transform_string(f.read(), **opts)


def transform(js_path, **opts):
    return Transformer(**opts).transform(js_path)


def transform_string(js_content, **opts):
    return Transformer(**opts).transform_string(js_content)
