from setuptools import setup

setup(name='lspreader',
      version='0.1.6r0',
      description='A set of python readers for the code LSP',
      url='http://github.com/noobermin/lspreader',
      author='noobermin',
      author_email='ngirmang.1@osu.com',
      license='MIT',
      packages=['lspreader'],
      install_requires=[
          'numpy>=1.10.1',
          'scipy>=0.16.0',
          'h5py>=2.5.0',
          'pys>=0.0.9',
      ],
      zip_safe=False)
