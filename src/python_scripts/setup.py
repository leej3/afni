import sys
from setuptools import setup, find_packages
from distutils.version import LooseVersion

# Do not attempt to install when using an unsupported python
PY_VER = '.'.join(str(n) for n in sys.version_info[:3])
MIN_PY_VER = "3.6"
if LooseVersion(PY_VER) < LooseVersion(MIN_PY_VER):
    err = "The current interpretter {} ({}) is not supported.".format(sys.executable,PY_VER)
    raise EnvironmentError(err)


from pathlib import Path
SCRIPTS = [str(f) for f in Path('scripts').glob('*.py')]

setup(name='afnipy',
      version='0.0.1',
      description='AFNI python code installed as a package. Much of the functionality requires a working installation of AFNI.',
      url='git+https://github.com/afni/afni.git@master#egg=afnipy&subdirectory=src/python_scripts',
      author='AFNI team',
      author_email='afni.bootcamp@gmail.com',
      license='Public Domain',
      packages= find_packages(),
      install_requires=["numpy", "matplotlib"],
      scripts=SCRIPTS,
      zip_safe=False)
