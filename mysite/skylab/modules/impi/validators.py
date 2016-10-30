import os.path

from django import forms


def jpeg_file_extension_validator(file):
    ext = os.path.splitext(file.name)[1]

    if ext.lower() not in ['.jpeg', '.jpg']:
        raise forms.ValidationError(u'Only .in file accepted',
                                    code="impi_invalid_input_file")
