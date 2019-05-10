from setuptools import setup

setup(name='lspreader',
      version='0.1.7r2',
      description='A set of python readers for the code LSP',
      url='http://github.com/noobermin/lspreader',
      author='noobermin',
      author_email='ngirmang.1@osu.com',
      license='MIT',
      packages=['lspreader'],
      install_requires=[
          'numpy>=1.13.1',
          'scipy>=0.19.1',
          'pys>=0.0.10',
          'docopt>=0.6.2',
      ],
      scripts=[
          'bin/p4read.py',
          'bin/split-pext.py',
          'bin/simple-pext.py',
          'bin/p4header.py'
      ],
      zip_safe=False)
