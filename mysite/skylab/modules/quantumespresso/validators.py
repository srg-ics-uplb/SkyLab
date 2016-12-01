import os.path

from django import forms

#used to validate form inputs

def in_files_validator(files):
    for f in files:
        in_file_extension_validator(f)


def in_file_extension_validator(f):
    ext = os.path.splitext(f.name)[1]

    if ext.lower() != '.in':
        raise forms.ValidationError(u'Only .in f accepted',
                                    code="quantum_espresso_invalid_input_file")
