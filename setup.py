from setuptools import setup, find_packages
from babeljs import VERSION

version = VERSION

setup(
    name='PyBabeljs',
    version=version,
    keywords=('babel', 'babeljs', 'ES', 'JavaScript',
              'ES2015', 'ES2016', 'ES2017'),
    description='The python binding for babel compiler',
    url='http://github.com/yetone/bablejs-python',
    license='MIT License',
    author='yetone',
    author_email='i@yetone.net',
    packages=find_packages(),
    platforms='any',
    include_package_data=True,
    tests_require=(
        'pytest',
    )
)
