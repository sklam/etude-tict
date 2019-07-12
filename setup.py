try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension

packages = ['tict',
            ]


with open('README.md') as f:
    long_description = f.read()


setup(name='tict',
      description="transactional dictionary",
      version="0.1dev0",
      packages=packages,
      long_description=long_description,
      license="BSD",
      )
