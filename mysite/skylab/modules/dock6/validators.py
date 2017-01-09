import os.path

from django import forms

#validators used for form inputs

def dock6_in_extension_validator(file):
    ext = os.path.splitext(file.name)[1]

    if ext.lower() != '.in':
        raise forms.ValidationError(u'Only .in file accepted',
                                    code="dock6_invalid_input_file")

def dock6_other_resources_extension_validator(file):
    ext = os.path.splitext(file.name)[1]
    valid_extensions = ['.mol2', '.pdb', '.sph', '.bmp', '.nrg']
    if ext.lower() not in valid_extensions:
        raise forms.ValidationError(u'Only .mol2, .pdb, .sph, .bmp, .nrg files accepted',
                                    code="dock6_invalid_input_file")


def multi_dock6_other_resources_validator(files):
    for file in files:
        dock6_other_resources_extension_validator(file)


def grid_other_resources_extension_validator(file):
    ext = os.path.splitext(file.name)[1]
    valid_extensions = ['.mol2', '.pdb']
    if ext.lower() not in valid_extensions:
        raise forms.ValidationError(u'Only .mol2, .pdb files accepted',
                                    code="dock6_invalid_input_file")


def multi_grid_other_resources_validator(files):
    for file in files:
        grid_other_resources_extension_validator(file)
