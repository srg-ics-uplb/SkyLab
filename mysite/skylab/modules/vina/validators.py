import os.path
from django import forms


def pdbqt_file_extension_validator(file):
    ext = os.path.splitext(file.name)[1]
    if ext.lower() != '.pdbqt':
        raise forms.ValidationError(u'Only .pdbqt file accepted', code="vina_invalid_file_format")
