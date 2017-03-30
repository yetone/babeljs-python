PyBabeljs
============

[![Build Status](https://api.travis-ci.org/yetone/babeljs-python.svg?branch=master)](https://travis-ci.org/yetone/babeljs-python)

PyBabeljs is a python bindings to [Babel](https://babeljs.io/).

## Installation

    $ pip install PyBabeljs

## Usage

```python
from babeljs import transformer

transformer.transform_string('const a = () => 233')
transformer.transform('path/to/test.js')
```

## License

MIT
