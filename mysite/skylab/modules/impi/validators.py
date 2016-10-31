import os.path

from django import forms


def impi_files_validator(files):
    for f in files:
        jpeg_file_extension_validator(f)


def jpeg_file_extension_validator(f):
    ext = os.path.splitext(f.name)[1]
    print ext
    if ext.lower() not in ['.jpeg', '.jpg']:
        raise forms.ValidationError(u'Only JPEG (.jpeg, .jpg) file accepted',
                                    code="impi_invalid_input_file")
