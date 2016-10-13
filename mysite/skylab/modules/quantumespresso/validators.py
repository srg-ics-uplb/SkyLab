import os.path

from django import forms


def in_file_extension_validator(file):
    ext = os.path.splitext(file.name)[1]

    if ext.lower() != '.in':
        raise forms.ValidationError(u'Only .in file accepted',
                                    code="quantum_espresso_invalid_input_file")
