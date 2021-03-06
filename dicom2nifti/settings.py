# allow to disable validations
validate_slicecount = True
validate_orientation = True
validate_orthogonal = True
validate_sliceincrement = True
validate_multiframe_implicit = True
gdcmconv_path = None


def disable_validate_sliceincrement():
    """
    Disable the validation of the slice increment.
    This allows for converting data where the slice increment is not consistent.
    USE WITH CAUTION!
    """
    global validate_sliceincrement
    validate_sliceincrement = False


def disable_validate_orientation():
    """
    Disable the validation of the slice orientation.
    This validation checks that all slices have the same orientation (are parallel).
    USE WITH CAUTION!
    """
    global validate_orientation
    validate_orientation = False


def disable_validate_orthogonal():
    """
    Disable the validation whether the volume is orthogonal (so without gantry tilting or alike).
    This allows for converting gantry tilted data.
    The gantry tilting will be reflected in the affine matrix and not in the data
    USE WITH CAUTION!
    """
    global validate_orthogonal
    validate_orthogonal = False


def disable_validate_slicecount():
    """
    Disable the validation of the minimal slice count of 4 slices.
    This allows for converting data with less slices.
    Usually less than 4 could be considered localizer or similar thus ignoring these scans by default
    USE WITH CAUTION!
    """
    global validate_slicecount
    validate_slicecount = False

def disable_validate_multiframe_implicit():
    """
    Disable the validation that checks that data is not multiframe implicit
    This allows to sometimes convert Philips Multiframe with implicit transfer syntax
    """
    global validate_multiframe_implicit
    validate_multiframe_implicit = False

def enable_validate_sliceincrement():
    """
    Enable the slice increment validation again (DEFAULT ENABLED)
    """
    global validate_sliceincrement
    validate_sliceincrement = True


def enable_validate_orientation():
    """
    Enable the slice orientation validation again (DEFAULT ENABLED)
    """
    global validate_orientation
    validate_orientation = True


def enable_validate_orthogonal():
    """
    Enable the validation whether the volume is orthogonal again (DEFAULT ENABLED)
    """
    global validate_orthogonal
    validate_orthogonal = True


def enable_validate_slicecount():
    """
    Enable the validation of the minimal slice count of 4 slices again (DEFAULT ENABLED)
    """
    global validate_slicecount
    validate_slicecount = True

def enable_validate_multiframe_implicit():
    """
    Enable the validation that checks that data is not multiframe implicit again (DEFAULT ENABLED)
    """
    global validate_multiframe_implicit
    validate_multiframe_implicit = True

def set_gdcmconv_path(path):
    """
    Set where the filepath to the gdcmconv executable (needed is it is not found in your PATH)

    :param path: the file path to the gdcmconv executable
    """
    global gdcmconv_path
    gdcmconv_path = path