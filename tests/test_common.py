# -*- coding: utf-8 -*-
"""
dicom2nifti

@author: abrys
"""
import os
import shutil
import tempfile
import unittest

import dicom2nifti
from dicom2nifti.exceptions import ConversionValidationError

from dicom2nifti.common import read_dicom_directory, \
    validate_sliceincrement, \
    validate_slicecount, \
    validate_orthogonal, \
    validate_orientation
from dicom2nifti.convert_generic import dicom_to_nifti
import tests.test_data as test_data


class TestConversionCommon(unittest.TestCase):
    def setUp(self):
        dicom2nifti.enable_validate_sliceincrement()
        dicom2nifti.enable_validate_slicecount()
        dicom2nifti.enable_validate_orientation()
        dicom2nifti.enable_validate_orthogonal()

    def test_validate_sliceincrement(self):
        validate_sliceincrement(read_dicom_directory(test_data.GE_ANATOMICAL))

        self.assertRaises(ConversionValidationError,
                          validate_sliceincrement,
                          read_dicom_directory(test_data.FAILING_SLICEINCREMENT))

    def test_validate_sliceincrement_disabled(self):
        tmp_output_dir = tempfile.mkdtemp()
        try:
            self.assertRaises(ConversionValidationError,
                              dicom_to_nifti,
                              read_dicom_directory(test_data.FAILING_SLICEINCREMENT),
                              os.path.join(tmp_output_dir, 'test.nii.gz'))
            dicom2nifti.disable_validate_sliceincrement()
            dicom_to_nifti(read_dicom_directory(test_data.FAILING_SLICEINCREMENT),
                           os.path.join(tmp_output_dir, 'test.nii.gz'))

        finally:
            shutil.rmtree(tmp_output_dir)

    def test_validate_slicecount(self):
        validate_slicecount(read_dicom_directory(test_data.GE_ANATOMICAL))

        self.assertRaises(ConversionValidationError,
                          validate_slicecount,
                          read_dicom_directory(test_data.FAILING_SLICECOUNT))

    def test_validate_slicecount_disabled(self):
        tmp_output_dir = tempfile.mkdtemp()
        try:
            self.assertRaises(ConversionValidationError,
                              dicom_to_nifti,
                              read_dicom_directory(test_data.FAILING_SLICECOUNT),
                              os.path.join(tmp_output_dir, 'test.nii.gz'))
            dicom2nifti.disable_validate_slicecount()
            dicom_to_nifti(read_dicom_directory(test_data.FAILING_SLICECOUNT),
                           os.path.join(tmp_output_dir, 'test.nii.gz'))

        finally:
            shutil.rmtree(tmp_output_dir)


    def test_validate_orthogonal(self):
        validate_orthogonal(read_dicom_directory(test_data.GE_ANATOMICAL))

        self.assertRaises(ConversionValidationError,
                          validate_orthogonal,
                          read_dicom_directory(test_data.FAILING_ORHTOGONAL))


    def test_validate_orthogonal_disabled(self):
        tmp_output_dir = tempfile.mkdtemp()
        try:
            self.assertRaises(ConversionValidationError,
                              dicom_to_nifti,
                              read_dicom_directory(test_data.FAILING_ORHTOGONAL),
                              os.path.join(tmp_output_dir, 'test.nii.gz'))
            dicom2nifti.disable_validate_orthogonal()
            dicom_to_nifti(read_dicom_directory(test_data.FAILING_ORHTOGONAL),
                           os.path.join(tmp_output_dir, 'test.nii.gz'))

        finally:
            shutil.rmtree(tmp_output_dir)


    def test_validate_orientation(self):
        validate_orientation(read_dicom_directory(test_data.GE_ANATOMICAL))

        self.assertRaises(ConversionValidationError,
                          validate_orientation,
                          read_dicom_directory(test_data.FAILING_ORIENTATION))


    def test_validate_orientation_disabled(self):
        tmp_output_dir = tempfile.mkdtemp()
        try:
            dicom2nifti.disable_validate_orthogonal() #this will also fail on this data
            dicom2nifti.disable_validate_sliceincrement() #this will also fail on this data
            self.assertRaises(ConversionValidationError,
                              dicom_to_nifti,
                              read_dicom_directory(test_data.FAILING_ORIENTATION),
                              os.path.join(tmp_output_dir, 'test.nii.gz'))
            dicom2nifti.disable_validate_orientation()
            dicom_to_nifti(read_dicom_directory(test_data.FAILING_ORIENTATION),
                           os.path.join(tmp_output_dir, 'test.nii.gz'))

        finally:
            shutil.rmtree(tmp_output_dir)


if __name__ == '__main__':
    unittest.main()
