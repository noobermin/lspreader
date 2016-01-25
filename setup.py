from setuptools import setup

setup(name='lspreader',
      version='0.0r1',
      description='A set of python readers for the code LSP',
      url='http://github.com/noobermin/lspreader',
      author='noobermin',
      author_email='ngirmang.1@osu.com',
      license='MIT',
      packages=['lspreader'],
      install_requires=[
          'numpy>=1.10.1',
          'scipy>=0.16.0'
      ],
      zip_safe=False)