# -*- coding:  utf-8 -*-
"""
Test suite specifically targeting JPX box layout.
"""

import os
import shutil
import struct
import sys
import tempfile
import unittest
import warnings
import xml.etree.cElementTree as ET

import glymur
from glymur import Jp2k


@unittest.skipIf(os.name == "nt", "Temporary file issue on window.")
class TestJPXWrap(unittest.TestCase):
    """Test suite for wrapping JPX files."""

    def setUp(self):
        self.jp2file = glymur.data.nemo()

        raw_xml = b"""<?xml version="1.0"?>
        <data>
            <country name="Liechtenstein">
                <rank>1</rank>
                <year>2008</year>
                <gdppc>141100</gdppc>
                <neighbor name="Austria" direction="E"/>
                <neighbor name="Switzerland" direction="W"/>
            </country>
        </data>"""
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tfile:
            tfile.write(raw_xml)
            tfile.flush()
        self.xmlfile = tfile.name

    def tearDown(self):
        os.unlink(self.xmlfile)

    def test_ftbl(self):
        """Write a fragment table box."""
        # Add a negative test where offset < 0
        # Add a negative test where length < 0
        # Add a negative test where ref > 0 but no data reference box.
        # Add a negative test where more than one flst
        # Add negative test where ftbl contained in a superbox.
        jp2 = Jp2k(self.jp2file)
        boxes = [jp2.box[idx] for idx in [0, 1, 2, 4]]

        # The ftyp box must be modified to jpx.
        boxes[1].brand = 'jpx '
        boxes[1].compatibility_list = ['jp2 ', 'jpxb']

        offset = [89]
        length = [1132288]
        reference = [0]
        flst = glymur.jp2box.FragmentListBox(offset, length, reference)
        ftbl = glymur.jp2box.FragmentTableBox(box=[flst])
        boxes.append(ftbl)

        with tempfile.NamedTemporaryFile(suffix=".jpx") as tfile:
            jpx = jp2.wrap(tfile.name, boxes=boxes)

            self.assertEqual(jpx.box[1].compatibility_list, ['jp2 ', 'jpxb'])
            self.assertEqual(jpx.box[-1].box_id, 'ftbl')
            self.assertEqual(jpx.box[-1].box[0].box_id, 'flst')

    def test_jpxb_compatibility(self):
        """Wrap JP2 to JPX, state jpxb compatibility"""
        jp2 = Jp2k(self.jp2file)
        boxes = [jp2.box[idx] for idx in [0, 1, 2, 4]]

        # The ftyp box must be modified to jpx with jp2 compatibility.
        boxes[1].brand = 'jpx '
        boxes[1].compatibility_list = ['jp2 ', 'jpxb']

        numbers = (0, 1)
        nlst = glymur.jp2box.NumberListBox(numbers)
        the_xml = ET.fromstring('<?xml version="1.0"?><data>0</data>')
        xmlb = glymur.jp2box.XMLBox(xml=the_xml)
        asoc = glymur.jp2box.AssociationBox([nlst, xmlb])
        boxes.append(asoc)

        with tempfile.NamedTemporaryFile(suffix=".jpx") as tfile:
            jpx = jp2.wrap(tfile.name, boxes=boxes)

            self.assertEqual(jpx.box[1].compatibility_list, ['jp2 ', 'jpxb'])
            self.assertEqual(jpx.box[-1].box_id, 'asoc')
            self.assertEqual(jpx.box[-1].box[0].box_id, 'nlst')
            self.assertEqual(jpx.box[-1].box[1].box_id, 'xml ')
            self.assertEqual(jpx.box[-1].box[0].associations, numbers)
            self.assertEqual(ET.tostring(jpx.box[-1].box[1].xml.getroot()),
                             b'<data>0</data>')

    def test_association_label_box(self):
        """Wrap JP2 to JPX with asoc, label, and nlst boxes"""
        jp2 = Jp2k(self.jp2file)
        boxes = [jp2.box[idx] for idx in [0, 1, 2, 4]]

        # The ftyp box must be modified to jpx with jp2 compatibility.
        boxes[1].brand = 'jpx '
        boxes[1].compatibility_list = ['jp2 ', 'jpx ']

        label = 'this is a test'
        lblb = glymur.jp2box.LabelBox(label)
        numbers = (0, 1)
        nlst = glymur.jp2box.NumberListBox(numbers)
        the_xml = ET.fromstring('<?xml version="1.0"?><data>0</data>')
        xmlb = glymur.jp2box.XMLBox(xml=the_xml)
        asoc = glymur.jp2box.AssociationBox([nlst, xmlb, lblb])
        boxes.append(asoc)

        with tempfile.NamedTemporaryFile(suffix=".jpx") as tfile:
            jpx = jp2.wrap(tfile.name, boxes=boxes)

            self.assertEqual(jpx.box[1].compatibility_list, ['jp2 ', 'jpx '])
            self.assertEqual(jpx.box[-1].box_id, 'asoc')
            self.assertEqual(jpx.box[-1].box[0].box_id, 'nlst')
            self.assertEqual(jpx.box[-1].box[0].associations, numbers)
            self.assertEqual(jpx.box[-1].box[1].box_id, 'xml ')
            self.assertEqual(ET.tostring(jpx.box[-1].box[1].xml.getroot()),
                             b'<data>0</data>')
            self.assertEqual(jpx.box[-1].box[2].box_id, 'lbl ')
            self.assertEqual(jpx.box[-1].box[2].label, label)

    def test_only_one_data_reference(self):
        """Data reference boxes cannot be inside a superbox ."""
        jp2 = Jp2k(self.jp2file)
        boxes = [jp2.box[idx] for idx in [0, 1, 2, 4]]

        flag = 0
        version = (0, 0, 0)
        url = 'file:////usr/local/bin'
        deurl = glymur.jp2box.DataEntryURLBox(flag, version, url)
        dref = glymur.jp2box.DataReferenceBox([deurl])
        boxes.append(dref)
        boxes.append(dref)

        with tempfile.NamedTemporaryFile(suffix=".jpx") as tfile:
            with self.assertRaises(IOError):
                jpx = jp2.wrap(tfile.name, boxes=boxes)

    def test_lbl_at_top_level(self):
        """Label boxes can only be inside a asoc box ."""
        jp2 = Jp2k(self.jp2file)
        boxes = [jp2.box[idx] for idx in [0, 1, 2, 4]]

        flag = 0
        version = (0, 0, 0)
        url = 'file:////usr/local/bin'
        lblb = glymur.jp2box.LabelBox('hi there')

        # Put it inside the jp2 header box.
        boxes[2].box.append(lblb)

        with tempfile.NamedTemporaryFile(suffix=".jpx") as tfile:
            with self.assertRaises(IOError):
                jpx = jp2.wrap(tfile.name, boxes=boxes)

    def test_data_reference_not_at_top_level(self):
        """Data reference boxes cannot be inside a superbox ."""
        jp2 = Jp2k(self.jp2file)
        boxes = [jp2.box[idx] for idx in [0, 1, 2, 4]]

        flag = 0
        version = (0, 0, 0)
        url = 'file:////usr/local/bin'
        deurl = glymur.jp2box.DataEntryURLBox(flag, version, url)
        dref = glymur.jp2box.DataReferenceBox([deurl])

        # Put it inside the jp2 header box.
        boxes[2].box.append(dref)

        with tempfile.NamedTemporaryFile(suffix=".jpx") as tfile:
            with self.assertRaises(IOError):
                jpx = jp2.wrap(tfile.name, boxes=boxes)

    def test_jp2_to_jpx_sans_jp2_compatibility(self):
        """jp2 wrapped to jpx not including jp2 compatibility is wrong."""
        jp2 = Jp2k(self.jp2file)
        boxes = [jp2.box[idx] for idx in [0, 1, 2, 4]]
        boxes[1].compatibility_list.append('jp2 ')
        numbers = [0, 1]
        nlst = glymur.jp2box.NumberListBox(numbers)
        the_xml = ET.fromstring('<?xml version="1.0"?><data>0</data>')
        xmlb = glymur.jp2box.XMLBox(xml=the_xml)
        asoc = glymur.jp2box.AssociationBox([nlst, xmlb])
        boxes.append(asoc)

        with tempfile.NamedTemporaryFile(suffix=".jpx") as tfile:
            with self.assertRaises(RuntimeError):
                jpx = jp2.wrap(tfile.name, boxes=boxes)

    def test_jp2_to_jpx_sans_jpx_brand(self):
        """Verify error when jp2 wrapped to jpx does not include jpx brand."""
        jp2 = Jp2k(self.jp2file)
        boxes = [jp2.box[idx] for idx in [0, 1, 2, 4]]
        boxes[1].brand = 'jpx '
        numbers = [0, 1]
        nlst = glymur.jp2box.NumberListBox(numbers)
        the_xml = ET.fromstring('<?xml version="1.0"?><data>0</data>')
        xmlb = glymur.jp2box.XMLBox(xml=the_xml)
        asoc = glymur.jp2box.AssociationBox([nlst, xmlb])
        boxes.append(asoc)

        with tempfile.NamedTemporaryFile(suffix=".jpx") as tfile:
            with self.assertRaises(RuntimeError):
                jpx = jp2.wrap(tfile.name, boxes=boxes)


@unittest.skipIf(os.name == "nt", "Temporary file issue on window.")
class TestJPX(unittest.TestCase):
    """Test suite for other JPX boxes."""

    def setUp(self):
        self.jpxfile = glymur.data.jpxfile()

    def tearDown(self):
        pass

    def test_flst_lens_not_the_same(self):
        """A fragment list box items must be the same length."""
        offset = [89]
        length = [1132288]
        reference = [0, 0]
        flst = glymur.jp2box.FragmentListBox(offset, length, reference)
        with self.assertRaises(IOError):
            with tempfile.TemporaryFile() as tfile:
               flst.write(tfile) 

    def test_flst_offsets_not_positive(self):
        """A fragment list box offsets must be positive."""
        offset = [0]
        length = [1132288]
        reference = [0]
        flst = glymur.jp2box.FragmentListBox(offset, length, reference)
        with self.assertRaises(IOError):
            with tempfile.TemporaryFile() as tfile:
               flst.write(tfile) 

    def test_flst_lengths_not_positive(self):
        """A fragment list box lengths must be positive."""
        offset = [89]
        length = [0]
        reference = [0]
        flst = glymur.jp2box.FragmentListBox(offset, length, reference)
        with self.assertRaises(IOError):
            with tempfile.TemporaryFile() as tfile:
               flst.write(tfile) 

    def test_ftbl_boxes_empty(self):
        """A fragment table box must have at least one child box."""
        ftbl = glymur.jp2box.FragmentTableBox()
        with self.assertRaises(IOError):
            with tempfile.TemporaryFile() as tfile:
                ftbl.write(tfile) 

    def test_ftbl_child_not_flst(self):
        """A fragment table box can only contain a fragment list."""
        free = glymur.jp2box.FreeBox()
        ftbl = glymur.jp2box.FragmentTableBox(box=[free])
        with self.assertRaises(IOError):
            with tempfile.TemporaryFile() as tfile:
                ftbl.write(tfile) 

    def test_jpx_rreq_mask_length_3(self):
        """There are some JPX files with rreq mask length of 3."""
        jpx = Jp2k(self.jpxfile)
        self.assertEqual(jpx.box[2].box_id, 'rreq')
        self.assertEqual(type(jpx.box[2]),
                         glymur.jp2box.ReaderRequirementsBox)
        self.assertEqual(jpx.box[2].standard_flag,
                         (5, 42, 45, 2, 18, 19, 1, 8, 12, 31, 20))

    @unittest.skipIf(sys.hexversion < 0x03000000, "Needs unittest in 3.x.")
    def test_unknown_superbox(self):
        """Verify that we can handle an unknown superbox."""
        with tempfile.NamedTemporaryFile(suffix='.jpx') as tfile:
            with open(self.jpxfile, 'rb') as ifile:
                tfile.write(ifile.read())
            
            # Add the header for an unknwon superbox.
            write_buffer = struct.pack('>I4s', 20, 'grp '.encode())
            tfile.write(write_buffer)
            write_buffer = struct.pack('>I4sI', 12, 'free'.encode(), 0)
            tfile.write(write_buffer)
            tfile.flush()

            with self.assertWarns(UserWarning):
                jpx = Jp2k(tfile.name)
            self.assertEqual(jpx.box[-1].box_id, 'grp ')
            self.assertEqual(jpx.box[-1].box[0].box_id, 'free')

    def test_free_box(self):
        """Verify that we can handle a free box."""
        j = Jp2k(self.jpxfile)
        self.assertEqual(j.box[16].box[0].box_id, 'free')
        self.assertEqual(type(j.box[16].box[0]), glymur.jp2box.FreeBox)

    def test_dtbl(self):
        """Verify that we can interpret Data Reference boxes."""
        # Copy the existing JPX file, add a data reference box onto the end.
        flag = 0
        version = (0, 0, 0)
        url1 = 'file:////usr/local/bin'
        url2 = 'http://glymur.readthedocs.org' + chr(0) * 3
        with tempfile.NamedTemporaryFile(suffix='.jpx') as tfile:
            with open(self.jpxfile, 'rb') as ifile:
                tfile.write(ifile.read())

                deurl1 = glymur.jp2box.DataEntryURLBox(flag, version, url1)
                deurl2 = glymur.jp2box.DataEntryURLBox(flag, version, url2)
                dref = glymur.jp2box.DataReferenceBox([deurl1, deurl2])
                dref.write(tfile)

            tfile.flush()

            jpx = Jp2k(tfile.name)

            self.assertEqual(jpx.box[-1].box_id, 'dtbl')
            self.assertEqual(len(jpx.box[-1].DR), 2)
            self.assertEqual(jpx.box[-1].DR[0].url, url1)
            self.assertEqual(jpx.box[-1].DR[1].url, url2.rstrip('\0'))

    def test_ftbl(self):
        """Verify that we can interpret Fragment Table boxes."""
        # Copy the existing JPX file, add a fragment table box onto the end.
        with tempfile.NamedTemporaryFile(suffix='.jpx') as tfile:
            with open(self.jpxfile, 'rb') as ifile:
                tfile.write(ifile.read())
            write_buffer = struct.pack('>I4s', 32, b'ftbl')
            tfile.write(write_buffer)

            # Just one fragment list box
            write_buffer = struct.pack('>I4s', 24, b'flst')
            tfile.write(write_buffer)

            # Simple offset, length, reference
            write_buffer = struct.pack('>HQIH', 1, 4237, 170246, 3)
            tfile.write(write_buffer)

            tfile.flush()

            jpx = Jp2k(tfile.name)

            self.assertEqual(jpx.box[-1].box_id, 'ftbl')
            self.assertEqual(jpx.box[-1].box[0].box_id, 'flst')
            self.assertEqual(jpx.box[-1].box[0].fragment_offset, (4237,))
            self.assertEqual(jpx.box[-1].box[0].fragment_length, (170246,))
            self.assertEqual(jpx.box[-1].box[0].data_reference, (3,))

    def test_nlst(self):
        """Verify that we can handle a free box."""
        j = Jp2k(self.jpxfile)
        self.assertEqual(j.box[16].box[1].box[0].box_id, 'nlst')
        self.assertEqual(type(j.box[16].box[1].box[0]),
                         glymur.jp2box.NumberListBox)

        # Two associations.
        self.assertEqual(len(j.box[16].box[1].box[0].associations), 2)

        # Codestream 0
        self.assertEqual(j.box[16].box[1].box[0].associations[0], 1 << 24)

        # Compositing Layer 0
        self.assertEqual(j.box[16].box[1].box[0].associations[1], 2 << 24)
