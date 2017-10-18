#!/usr/bin/env python
#

from setuptools import setup, find_packages

setupdict = dict(
   name='dapscompare',
   version='0.4.2',
   description='dapscompare is a tool for comparing documentation output',
   url='https://github.com/openSUSE/dapscompare',
   # Author details
   author='Sven Seeberg-Elverfeldt',
   author_email='sseebergelverfeldt AT suse.com',
   license='MIT',
   # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
   classifiers=[
      #
      'Development Status :: 4 - Beta',
      'Topic :: Documentation',
      'Topic :: Software Development :: Documentation',
      'Topic :: Software Development :: Testing',
      'Intended Audience :: Developers',
      # The license:
      'License :: OSI Approved :: MIT License',
      # Supported Python versions:
      'Programming Language :: Python :: 3.3',
      'Programming Language :: Python :: 3.4',
      'Programming Language :: Python :: 3.5',
      'Programming Language :: Python :: 3.6',
   ],
   keywords='daps testing',
   include_package_data=True,
   # You can just specify the packages manually here if your project is
   # simple. Or you can use find_packages().
   packages=find_packages('src'),
   package_dir={'': 'src'},
   install_requires=['PyQt4','scipy', 'numpy', 'Pillow'],
   # have to be included in MANIFEST.in as well.
   package_data={
        '': ['src/dapscompare/README'],
   },
   # TODO: Check, if entry_points is a better alternative
   scripts=['bin/dapscmp'],
)

setup(**setupdict)
