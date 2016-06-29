import os.path
from django import forms


def pdbqt_file_extension_validator(file):
    ext = os.path.splitext(file.name)[1]
    if ext.lower() != '.pdbqt':
        raise forms.ValidationError(u'Only .pdbqt file accepted', code="vina_invalid_file_format")


def dpf_file_extension_validator(file):
    ext = os.path.splitext(file.name)[1]
    if ext.lower() != '.dpf':
        raise forms.ValidationError(u'Only .dpf file accepted', code="autodock_invalid_file_format")


def gpf_file_extension_validator(file):
    ext = os.path.splitext(file.name)[1]
    if ext.lower() != '.gpf':
        raise forms.ValidationError(u'Only .gpf file accepted', code="autogrid_invalid_file_format")
