# PyBabeljs

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
