from crispy_forms.bootstrap import AppendedText
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Fieldset
from django import forms
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils.text import get_valid_filename
from multiupload.fields import MultiFileField

from skylab.forms import MPIModelChoiceField, get_mpi_queryset_all
from skylab.models import MPICluster, ToolSet
from validators import multi_dock6_other_resources_validator, dock6_in_extension_validator, \
    multi_grid_other_resources_validator


class GridForm(forms.Form):
    param_input_file = forms.FileField(label="Input file (.in)",
                                       help_text="Please set receptor_file and box_file parameters to ./[filename]<br>"
                                                 "Please set vdw_definition_file parameter to /mirror/dock6/parameters/[vdw_definition_file]",
                                       validators=[dock6_in_extension_validator])
    param_other_files = MultiFileField(label="Other input resources", help_text="These are files specified in your (.in) input file.<br>File types: (.pdb, .mol2)", min_num=1,
                                       validators=[multi_grid_other_resources_validator])
    param_output_prefix = forms.CharField(required=False, label="Output file prefix",
                                          help_text="If specified, the output file will be named as [output_prefix].out",
                                          widget=forms.TextInput(attrs={'placeholder': 'output_prefix'}))
    param_terse = forms.BooleanField(required=False, label="-t",
                                     help_text='Terse program output')
    param_verbose = forms.BooleanField(required=False, label="-v",
                                       help_text="Verbose program output")

    def clean_param_output_prefix(self):
        output_prefix = self.cleaned_data['param_output_prefix']
        return get_valid_filename(output_prefix)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(GridForm, self).__init__(*args, **kwargs)
        toolset = ToolSet.objects.get(p2ctool_name="dock6")

        self.fields['mpi_cluster'] = MPIModelChoiceField(queryset=get_mpi_queryset_all(self.user), label="MPI Cluster",
                                                         toolset=toolset,
                                                         help_text="Getting an empty list? Try <a href='{0}'>creating an MPI Cluster</a> first.".format(
                                                             reverse('create_mpi')))

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(

            Field('mpi_cluster', wrapper_class='col-xs-12'),

            Fieldset(
                'Input',
                Field('param_input_file', wrapper_class='col-xs-12'),
                Field('param_other_files', wrapper_class='col-xs-12 col-md-8'),
                css_class='col-xs-12'
            ),
            Fieldset(
                'Output',
                AppendedText('param_output_prefix', '.out', wrapper_class='col-xs-12 col-md-8'),
                css_class='col-xs-12'
            ),
            Fieldset(
                'Other parameters',
                Field('param_terse', wrapper_class='col-xs-12'),
                Field('param_verbose', wrapper_class='col-xs-12'),
                css_class=' col-xs-12'
            )

        )


class Dock6Form(forms.Form):
    param_input_file = forms.FileField(label="Input file (.in)",
                                       help_text="All input files and produced files other than .out files are stored in a single directory during execution.<br>"
                                                 "Please change file location parameters accordingly.",
                                       validators=[dock6_in_extension_validator])
    param_other_files = MultiFileField(label="Other input resources", min_num=1,
                                       help_text="These are files specified in your (.in) input file.<br>File types: (.pdb, .sph, .mol2, .nrg, .bmp",
                                       validators=[multi_dock6_other_resources_validator])
    param_output_prefix = forms.CharField(required=False, label="Output file prefix",
                                          help_text="If specified, your output file will be named as [output_prefix].out",
                                          widget=forms.TextInput(attrs={'placeholder': 'output_prefix'}))

    def clean_param_output_prefix(self):
        output_prefix = self.cleaned_data['param_output_prefix']
        return get_valid_filename(output_prefix)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(Dock6Form, self).__init__(*args, **kwargs)

        toolset = ToolSet.objects.get(p2ctool_name="dock6")

        self.fields['mpi_cluster'] = MPIModelChoiceField(queryset=get_mpi_queryset_all(self.user), label="MPI Cluster",
                                                         toolset=toolset,
                                                         help_text="Getting an empty list? Try <a href='{0}'>creating an MPI Cluster</a> first.".format(
                                                             reverse('create_mpi')))
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('mpi_cluster', wrapper_class='col-xs-12'),
            Fieldset(
                'Input parameters',
                Field('param_input_file', wrapper_class='col-xs-12'),
                Field('param_other_files', wrapper_class='col-xs-12 col-md-8'),
                css_class='col-xs-12'
            ),
            Fieldset(
                'Output parameters',
                AppendedText('param_output_prefix', '.out', wrapper_class='col-xs-12 col-md-8'),
                css_class='col-xs-12'
            ),
        )
