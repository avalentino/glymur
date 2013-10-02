# This file is part of glymur, a Python interface for accessing JPEG 2000.
#
# http://glymur.readthedocs.org
#
# Copyright 2013 John Evans
#
# License:  MIT

import pdb; pdb.set_trace()
import sys
import numpy as np
from distutils.version import LooseVersion

from .lib import openjpeg as opj
from .lib import openjp2 as opj2

version = "0.5.4"
_sv = LooseVersion(version)
version_tuple = _sv.version


if opj.OPENJPEG is None and opj2.OPENJP2 is None:
    openjpeg_version = '0.0.0'
elif opj2.OPENJP2 is None:
    openjpeg_version = opj.version()
else:
    openjpeg_version = opj2.version()

_sv = LooseVersion(openjpeg_version)
openjpeg_version_tuple = _sv.version

__doc__ = """\
This is glymur **{glymur_version}**

* OPENJPEG version:  **{openjpeg}**
""".format(glymur_version=version,
           openjpeg=openjpeg_version)

info = """\
Summary of glymur configuration
-------------------------------

glymur        {glymur}
OPENJPEG      {openjpeg}
Python        {python}
sys.platform  {platform}
sys.maxsize   {maxsize}
numpy         {numpy}
""".format(glymur=version,
           openjpeg=openjpeg_version,
           python=sys.version,
           platform=sys.platform,
           maxsize=sys.maxsize,
           numpy=np.__version__)
