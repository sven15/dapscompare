`dapscompare` compares DAPS documentation output.

`dapscompare` searches in all subdirectories of a testcases folder for DC
files and builds PDFs and HTML from those. It starts as many threads as
there are CPU cores available.

It is used in two steps:

1. Build reference images (`dapscmp reference`): build the initial set of images
2. Build comparison images (`dapscmp compare`): build the set of comparison
   images and compare to the reference set

Differences between sets of images can be viewed in small Qt-based image viewer.


### Installation on openSUSE

To install the package on recent versions of openSUSE Leap/Tumbleweed, use the
[package from OBS](https://build.opensuse.org/package/show/Documentation:Tools/dapscompare).


### Installation Using `pip`

`dapscompare` requires DAPS and Python 3. Additionally, use pip or the package
manager of your operating system to install:

- PyQt4
- SciPy
- NumPy
- Pillow (PIL fork)
- PSUtil

If you install with `pip`, you will need additional packages. For openSUSE,
you need to install:

- libtiff-devel
- libpng12-devel
- libjpeg8-devel


To install the requirements on openSUSE Leap 42.2/42.3, run:

```
zypper in python3-tk python3-qt4 python3-Pillow
pip3 install Pillow scipy numpy
```

### Licensing

The MIT License (MIT)

Copyright (c) 2017,
Sven Seeberg-Elverfeldt <sseebergelverfeldt@suse.com>

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files 
(the "Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish, 
distribute, sublicense, and/or sell copies of the Software, and to 
permit persons to whom the Software is furnished to do so, subject to 
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

