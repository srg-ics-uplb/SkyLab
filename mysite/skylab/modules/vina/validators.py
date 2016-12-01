import os.path

from django import forms

# used to validate form input

def pdbqt_file_extension_validator(file):
    ext = os.path.splitext(file.name)[1]
    if ext.lower() != '.pdbqt':
        raise forms.ValidationError(u'Only .pdbqt file accepted', code="vina_invalid_file_format")


def multi_pdbqt_file_validator(files):
    for file in files:
        pdbqt_file_extension_validator(file)
