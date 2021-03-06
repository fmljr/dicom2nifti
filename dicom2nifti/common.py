# -*- coding: utf-8 -*-
"""
dicom2nifti

@author: abrys
"""
from __future__ import print_function

import os
import struct

import dicom
import numpy
from dicom.tag import Tag

from dicom2nifti.exceptions import ConversionValidationError


# Disable false positive numpy errors
# pylint: disable=E1101
def read_dicom_directory(dicom_directory, stop_before_pixels=False):
    """
    Read all dicom files in a given directory (stop before pixels)

    :type stop_before_pixels: bool
    :type dicom_directory: six.string_types
    :param stop_before_pixels: Should we stop reading before the pixeldata (handy if we only want header info)
    :param dicom_directory: Directory with dicom data
    :return: List of dicom objects
    """
    dicom_input = []
    for root, _, files in os.walk(dicom_directory):
        for dicom_file in files:
            file_path = os.path.join(root, dicom_file)
            if is_dicom_file(file_path):
                dicom_headers = dicom.read_file(file_path, defer_size=100, stop_before_pixels=stop_before_pixels)
                dicom_input.append(dicom_headers)
    return dicom_input


def get_volume_pixeldata(sorted_slices):
    """
    the slice and intercept calculation can cause the slices to have different dtypes
    we should get the correct dtype that can cover all of them
    
    :type sorted_slices: list of slices
    :param sorted_slices: sliced sored in the correct order to create volume
    """
    slices = []
    combined_dtype = None
    for slice_ in sorted_slices:
        slice_data = _get_slice_pixeldata(slice_)
        slice_data = slice_data[numpy.newaxis, :, :]
        slices.append(slice_data)
        if combined_dtype is None:
            combined_dtype = slice_data.dtype
        else:
            combined_dtype = numpy.promote_types(combined_dtype, slice_data.dtype)
    # create the new volume with with the correct data
    vol = numpy.concatenate(slices, axis=0)

    # Done
    vol = numpy.transpose(vol, (2, 1, 0))
    return vol


def _get_slice_pixeldata(dicom_slice):
    """
    the slice and intercept calculation can cause the slices to have different dtypes
    we should get the correct dtype that can cover all of them

    :type dicom_slice: pydicom object
    :param dicom_slice: slice to get the pixeldata for
    """
    data = dicom_slice.pixel_array
    return apply_scaling(data, dicom_slice)


def _is_float(float_value):
    """
    Check if a number is actually a float

    :type float_value: int or float
    :param float_value: number to check
    :return True if it is not an integer number
    """
    if int(float_value) != float_value:
        return True


def is_dicom_file(filename):
    """
    Util function to check if file is a dicom file
    the first 128 bytes are preamble
    the next 4 bytes should contain DICM otherwise it is not a dicom

    :param filename: file to check for the DICM header block
    :type filename: six.string_types
    :returns: True if it is a dicom file
    """
    file_stream = open(filename, 'rb')
    file_stream.seek(128)
    data = file_stream.read(4)
    file_stream.close()
    if data == b'DICM':
        return True
    return False


def get_numpy_type(dicom_header):
    """
    Make NumPy format code, e.g. "uint16", "int32" etc
    from two pieces of info:
    mosaic.PixelRepresentation -- 0 for unsigned, 1 for signed;
    mosaic.BitsAllocated -- 8, 16, or 32

    :param dicom_header: the read dicom file/headers
    :returns: numpy format string
    """

    format_string = '%sint%d' % (('u', '')[dicom_header.PixelRepresentation], dicom_header.BitsAllocated)
    try:
        numpy.dtype(format_string)
    except TypeError:
        raise TypeError("Data type not understood by NumPy: format='%s', PixelRepresentation=%d, BitsAllocated=%d" %
                        (format_string, dicom_header.PixelRepresentation, dicom_header.BitsAllocated))
    return format_string


def get_fd_array_value(tag, count):
    """
    Getters for data that also work with implicit transfersyntax

    :param count: number of items in the array
    :param tag: the tag to read
    """
    if tag.VR == 'OB' or tag.VR == 'UN':
        values = []
        for i in range(count):
            start = i * 8
            stop = (i + 1) * 8
            values.append(struct.unpack('d', tag.value[start:stop])[0])
        return numpy.array(values)
    return tag.value


def get_fd_value(tag):
    """
    Getters for data that also work with implicit transfersyntax

    :param tag: the tag to read
    """
    if tag.VR == 'OB' or tag.VR == 'UN':
        value = struct.unpack('d', tag.value)[0]
        return value
    return tag.value


def set_fd_value(tag, value):
    """
    Setters for data that also work with implicit transfersyntax

    :param value: the value to set on the tag
    :param tag: the tag to read
    """
    if tag.VR == 'OB' or tag.VR == 'UN':
        value = struct.pack('d', value)
    tag.value = value


def get_fl_value(tag):
    """
    Getters for data that also work with implicit transfersyntax

    :param tag: the tag to read
    """
    if tag.VR == 'OB' or tag.VR == 'UN':
        value = struct.unpack('f', tag.value)[0]
        return value
    return tag.value


def get_is_value(tag):
    """
    Getters for data that also work with implicit transfersyntax

    :param tag: the tag to read
    """
    # data is int formatted as string so convert te string first and cast to int
    if tag.VR == 'OB' or tag.VR == 'UN':
        value = int(tag.value.decode("ascii").replace(" ", ""))
        return value
    return int(tag.value)


def get_ss_value(tag):
    """
    Getters for data that also work with implicit transfersyntax

    :param tag: the tag to read
    """
    # data is int formatted as string so convert te string first and cast to int
    if tag.VR == 'OB' or tag.VR == 'UN':
        value = struct.unpack('h', tag.value)[0]
        return value
    return tag.value


def set_ss_value(tag, value):
    """
    Setter for data that also work with implicit transfersyntax

    :param value: the value to set on the tag
    :param tag: the tag to read
    """
    if tag.VR == 'OB' or tag.VR == 'UN':
        value = struct.pack('h', value)
    tag.value = value


def apply_scaling(data, dicom_headers):
    """
    Rescale the data based on the RescaleSlope and RescaleOffset
    Based on the scaling from pydicomseries

    :param dicom_headers: dicom headers to use to retreive the scaling factors
    :param data: the input data
    """

    # Apply the rescaling if needed
    private_scale_slope_tag = Tag(0x2005, 0x100E)
    private_scale_intercept_tag = Tag(0x2005, 0x100D)
    if 'RescaleSlope' in dicom_headers or 'RescaleIntercept' in dicom_headers \
            or private_scale_slope_tag in dicom_headers or private_scale_intercept_tag in dicom_headers:
        rescale_slope = 1
        rescale_intercept = 0
        private_scale_slope = 1.0
        private_scale_intercept = 0.0
        if 'RescaleSlope' in dicom_headers:
            rescale_slope = dicom_headers.RescaleSlope
        if 'RescaleIntercept' in dicom_headers:
            rescale_intercept = dicom_headers.RescaleIntercept
        try:
            # this section can sometimes fail due to unknown private fields
            if private_scale_slope_tag in dicom_headers:
                private_scale_slope = dicom_headers[private_scale_slope_tag].value
            if private_scale_slope_tag in dicom_headers:
                private_scale_slope = dicom_headers[private_scale_slope_tag].value
        except:
            pass
        return do_scaling(data, rescale_slope, rescale_intercept, private_scale_slope, private_scale_intercept)
    else:
        return data


def do_scaling(data, rescale_slope, rescale_intercept, private_scale_slope=1.0, private_scale_intercept=0.0):
    # Obtain slope and offset
    need_floats = False

    if int(rescale_slope) != rescale_slope or int(rescale_intercept) != rescale_intercept or \
                    private_scale_slope != 1.0 or private_scale_intercept != 0.0:
        need_floats = True

    if not need_floats:
        rescale_slope = int(rescale_slope)
        rescale_intercept = int(rescale_intercept)
    else:
        private_scale_slope = float(private_scale_slope)
        private_scale_intercept = float(private_scale_intercept)

    # Maybe we need to change the datatype?
    if data.dtype in [numpy.float32, numpy.float64]:
        pass
    elif need_floats:
        data = data.astype(numpy.float32)
    else:
        # Determine required range
        minimum_required, maximum_required = data.min(), data.max()
        minimum_required = min([minimum_required, minimum_required * rescale_slope + rescale_intercept,
                                maximum_required * rescale_slope + rescale_intercept])
        maximum_required = max([maximum_required, minimum_required * rescale_slope + rescale_intercept,
                                maximum_required * rescale_slope + rescale_intercept])

        # Determine required datatype from that
        if minimum_required < 0:
            # Signed integer type
            maximum_required = max([-minimum_required, maximum_required])
            if maximum_required < 2 ** 7:
                dtype = numpy.int8
            elif maximum_required < 2 ** 15:
                dtype = numpy.int16
            elif maximum_required < 2 ** 31:
                dtype = numpy.int32
            else:
                dtype = numpy.float32
        else:
            # Unsigned integer type
            if maximum_required < 2 ** 8:
                dtype = numpy.int8
            elif maximum_required < 2 ** 16:
                dtype = numpy.int16
            elif maximum_required < 2 ** 32:
                dtype = numpy.int32
            else:
                dtype = numpy.float32

        # Change datatype
        if dtype != data.dtype:
            data = data.astype(dtype)

    # Apply rescale_slope and rescale_intercept
    # Scaling according to ISMRM2013_PPM_scaling_reminder
    # The actual scaling is not does the scaling the same way as the next code example
    # and https://github.com/fedorov/DICOMPhilipsRescalePlugin/blob/master/DICOMPhilipsRescalePlugin.py
    # FOR DEFAULT DATA
    # RESULT_DATA = (STORED_VALUE * RESCALE_SLOPE) + RESCALE_INTERCEPT
    # FOR PHILIPS DATA
    # RESULT_DATA = (STORED_VALUE * PRIVATE_SCALE_SLOPE) + PRIVATE_SCALE_INTERCEPT
    if private_scale_slope == 1.0 and private_scale_intercept == 0.0:
        data = (data * rescale_slope) + rescale_intercept
    else:
        data = (data * private_scale_slope) + private_scale_intercept

    return data


def write_bvec_file(bvecs, bvec_file):
    """
    Write an array of bvecs to a bvec file

    :param bvecs: array with the vectors
    :param bvec_file: filepath to write to
    """
    print('Saving BVEC file: %s' % bvec_file)
    with open(bvec_file, 'w') as text_file:
        # Map a dicection to string join them using a space and write to the file
        text_file.write('%s\n' % ' '.join(map(str, bvecs[:, 0])))
        text_file.write('%s\n' % ' '.join(map(str, bvecs[:, 1])))
        text_file.write('%s\n' % ' '.join(map(str, bvecs[:, 2])))


def write_bval_file(bvals, bval_file):
    """
    Write an array of bvals to a bval file

    :param bvals: array with the values
    :param bval_file: filepath to write to
    """
    print('Saving BVAL file: %s' % bval_file)
    with open(bval_file, 'w') as text_file:
        # join the bvals using a space and write to the file
        text_file.write('%s\n' % ' '.join(map(str, bvals)))


def create_affine(sorted_dicoms):
    """
    Function to generate the affine matrix for a dicom series
    This method was based on (http://nipy.org/nibabel/dicom/dicom_orientation.html)

    :param sorted_dicoms: list with sorted dicom files
    """

    # Create affine matrix (http://nipy.sourceforge.net/nibabel/dicom/dicom_orientation.html#dicom-slice-affine)
    image_orient1 = numpy.array(sorted_dicoms[0].ImageOrientationPatient)[0:3]
    image_orient2 = numpy.array(sorted_dicoms[0].ImageOrientationPatient)[3:6]

    delta_r = float(sorted_dicoms[0].PixelSpacing[0])
    delta_c = float(sorted_dicoms[0].PixelSpacing[1])

    image_pos = numpy.array(sorted_dicoms[0].ImagePositionPatient)

    last_image_pos = numpy.array(sorted_dicoms[-1].ImagePositionPatient)

    if len(sorted_dicoms) == 1:
        # Single slice
        step = [0, 0, -1]
    else:
        step = (image_pos - last_image_pos) / (1 - len(sorted_dicoms))

    return numpy.matrix([[-image_orient1[0] * delta_r, -image_orient2[0] * delta_c, -step[0], -image_pos[0]],
                         [-image_orient1[1] * delta_r, -image_orient2[1] * delta_c, -step[1], -image_pos[1]],
                         [image_orient1[2] * delta_r, image_orient2[2] * delta_c, step[2], image_pos[2]],
                         [0, 0, 0, 1]])


def validate_orthogonal(dicoms):
    """
    Validate that volume is orthonormal

    :param dicoms: check that we have a volume without skewing
    """
    first_image_orient1 = numpy.array(dicoms[0].ImageOrientationPatient)[0:3]
    first_image_orient2 = numpy.array(dicoms[0].ImageOrientationPatient)[3:6]
    first_image_pos = numpy.array(dicoms[0].ImagePositionPatient)

    last_image_pos = numpy.array(dicoms[-1].ImagePositionPatient)

    first_image_dir = numpy.cross(first_image_orient1, first_image_orient2)
    first_image_dir /= numpy.linalg.norm(first_image_dir)

    combined_dir = last_image_pos - first_image_pos
    combined_dir /= numpy.linalg.norm(combined_dir)

    if not numpy.allclose(first_image_dir, combined_dir, rtol=0.05, atol=0.05) \
            and not numpy.allclose(first_image_dir, -combined_dir, rtol=0.05, atol=0.05):
        print('Orthogonality check failed: non cubical image')
        print('---------------------------------------------------------')
        print(first_image_dir)
        print(combined_dir)
        print('---------------------------------------------------------')
        raise ConversionValidationError('NON_CUBICAL_IMAGE/GANTRY_TILT')


def validate_sliceincrement(dicoms):
    """
    Validate that the distance between all slices is equal (of very close to)

    :param dicoms: list of dicoms
    """
    first_image_position = numpy.array(dicoms[0].ImagePositionPatient)
    previous_image_position = numpy.array(dicoms[1].ImagePositionPatient)
    increment = first_image_position - previous_image_position
    for dicom_ in dicoms[2:]:
        current_image_position = numpy.array(dicom_.ImagePositionPatient)
        current_increment = previous_image_position - current_image_position
        if not numpy.allclose(increment, current_increment, rtol=0.05, atol=0.05):
            print('Slice increment not consistent through all slices')
            print('---------------------------------------------------------')
            print(previous_image_position, increment)
            print(current_image_position, current_increment)
            print('---------------------------------------------------------')
            raise ConversionValidationError('SLICE_INCREMENT_INCONSISTENT')
        previous_image_position = current_image_position


def validate_slicecount(dicoms):
    """
    Validate that volume is big enough to create a meaningfull volume
    This will also skip localizers and alike

    :param dicoms: list of dicoms
    """
    if len(dicoms) <= 3:
        print('At least 4 slices are needed for correct conversion')
        print('---------------------------------------------------------')
        raise ConversionValidationError('TOO_FEW_SLICES/LOCALIZER')


def validate_orientation(dicoms):
    """
    Validate that all dicoms have the same orientation

    :param dicoms: list of dicoms
    """
    first_image_orient1 = numpy.array(dicoms[0].ImageOrientationPatient)[0:3]
    first_image_orient2 = numpy.array(dicoms[0].ImageOrientationPatient)[3:6]
    for dicom_ in dicoms:
        # Create affine matrix (http://nipy.sourceforge.net/nibabel/dicom/dicom_orientation.html#dicom-slice-affine)
        image_orient1 = numpy.array(dicom_.ImageOrientationPatient)[0:3]
        image_orient2 = numpy.array(dicom_.ImageOrientationPatient)[3:6]
        if not numpy.allclose(image_orient1, first_image_orient1, rtol=0.001, atol=0.001) \
                or not numpy.allclose(image_orient2, first_image_orient2, rtol=0.001, atol=0.001):
            print('Image orientations not consistent through all slices')
            print('---------------------------------------------------------')
            print(image_orient1, first_image_orient1)
            print(image_orient2, first_image_orient2)
            print('---------------------------------------------------------')
            raise ConversionValidationError('IMAGE_ORIENTATION_INCONSISTENT')


def set_tr_te(nifti_image, repetition_time, echo_time):
    """
    Set the tr and te in the nifti headers

    :param echo_time: echo time
    :param repetition_time: repetition time
    :param nifti_image: nifti image to set the info to
    """
    # set the repetition time in pixdim
    nifti_image.get_header().structarr['pixdim'][4] = repetition_time / 1000.0

    # set tr and te in db_name field
    nifti_image.get_header().structarr['db_name'] = '?TR:%.3f TE:%d' % (repetition_time, echo_time)

    return nifti_image
