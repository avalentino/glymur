"""
ICC profile tests.
"""

# unittest doesn't work well with R0904.
# pylint: disable=R0904

# unittest2 is python2.6 only (pylint/python-2.7)
# pylint: disable=F0401

import datetime
import os
import sys

if sys.hexversion < 0x02070000:
    import unittest2 as unittest
else:
    import unittest

import numpy as np

from glymur import Jp2k
from .fixtures import OPJ_DATA_ROOT, opj_data_file


@unittest.skipIf(OPJ_DATA_ROOT is None,
                 "OPJ_DATA_ROOT environment variable not set")
class TestICC(unittest.TestCase):
    """ICC profile tests"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_file5(self):
        """basic ICC profile"""
        filename = opj_data_file('input/conformance/file5.jp2')
        j = Jp2k(filename)
        profile = j.box[3].box[1].icc_profile
        self.assertEqual(profile['Size'], 546)
        self.assertEqual(profile['Preferred CMM Type'], 0)
        self.assertEqual(profile['Version'], '2.2.0')
        self.assertEqual(profile['Device Class'], 'input device profile')
        self.assertEqual(profile['Color Space'], 'RGB')
        self.assertEqual(profile['Datetime'],
                         datetime.datetime(2001, 8, 30, 13, 32, 37))
        self.assertEqual(profile['File Signature'], 'acsp')
        self.assertEqual(profile['Platform'], 'unrecognized')
        self.assertEqual(profile['Flags'],
                         'embedded, can be used independently')

        self.assertEqual(profile['Device Manufacturer'], 'KODA')
        self.assertEqual(profile['Device Model'], 'ROMM')

        self.assertEqual(profile['Device Attributes'],
                         'reflective, glossy, positive media polarity, '
                         + 'color media')
        self.assertEqual(profile['Rendering Intent'], 'perceptual')

        np.testing.assert_almost_equal(profile['Illuminant'],
                                       (0.964203, 1.000000, 0.824905),
                                       decimal=6)

        self.assertEqual(profile['Creator'], 'JPEG')

    @unittest.skipIf(sys.hexversion < 0x03020000,
                     "Uses features introduced in 3.2.")
    def test_invalid_profile_header(self):
        """invalid ICC header data should cause UserWarning"""
        jfile = opj_data_file('input/nonregression/orb-blue10-lin-jp2.jp2')

        # assertWarns in Python 3.3 (python2.7/pylint issue)
        # pylint: disable=E1101
        with self.assertWarns(UserWarning):
            Jp2k(jfile)

if __name__ == "__main__":
    unittest.main()
