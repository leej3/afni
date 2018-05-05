from setuptools import setup

setup(name='afnipython',
      version='0.0.1',
      description='AFNI python packages',
      url='git+https://github.com/leej3/template_making.git',
      author='AFNI team',
      author_email='afni.bootcamp@gmail.com',
      license='Public Domain',
      packages=['afnipython'],
      install_requires=[
          'numpy'
      ],
      zip_safe=False)