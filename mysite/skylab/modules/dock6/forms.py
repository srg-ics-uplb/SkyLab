from crispy_forms.bootstrap import AppendedText
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Fieldset
from django import forms
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils.text import get_valid_filename
from multiupload.fields import MultiFileField

from skylab.forms import MPIModelChoiceField
from skylab.models import MPICluster, ToolSet
from validators import multi_dock6_other_resources_validator, dock6_in_extension_validator, \
    multi_grid_other_resources_validator


class GridForm(forms.Form):
    param_input_file = forms.FileField(label="Input file (.in)",
                                       help_text="All input files and produced files other than .out files are stored in a single directory during execution.",
                                       validators=[dock6_in_extension_validator])
    param_other_files = MultiFileField(label="Other input resources", help_text="(.pdb), (.sph), (.mol2)", min_num=1,
                                       validators=[multi_grid_other_resources_validator])
    param_output_prefix = forms.CharField(required=False, label="Output file prefix",
                                          help_text="default: input_filename",
                                          widget=forms.TextInput(attrs={'placeholder': 'filename'}))
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

        user_allowed = Q(allowed_users=self.user)
        cluster_is_public = Q(is_public=True)

        q = MPICluster.objects.filter(user_allowed | cluster_is_public)
        q = q.exclude(status=5).exclude(queued_for_deletion=True)
        toolset = ToolSet.objects.get(p2ctool_name="dock6")

        self.fields['mpi_cluster'] = MPIModelChoiceField(queryset=q, label="MPI Cluster",
                                                         toolset=toolset,
                                                         help_text="Getting an empty list? Try <a href='{0}'>creating an MPI Cluster</a> first.".format(
                                                             reverse('create_mpi')))

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Field('mpi_cluster', wrapper_class='col-xs-12'),
                css_class="col-xs-12"
            ),
            Fieldset(
                'Input',
                Div(
                    Div('param_input_file', css_class='col-xs-12'),
                    Div('param_other_files', css_class='col-xs-12 col-md-8'),
                    css_class='row-fluid col-sm-12'
                ),

            ),
            Fieldset(
                'Output',
                Div(
                    Div(AppendedText('param_output_prefix', '.out'), css_class='col-xs-12 col-md-8'),
                    css_class='row-fluid col-xs-12'
                )
            ),
            Fieldset(
                'Other parameters',

                Div(
                    Div('param_terse', css_class='col-xs-12'),
                    Div('param_verbose', css_class='col-xs-12'),
                    css_class='row-fluid col-xs-12'
                )
            )
        )


class Dock6Form(forms.Form):
    param_input_file = forms.FileField(label="Input file (.in)",
                                       help_text="All input files and produced files other than .out files are stored in a single directory during execution.",
                                       validators=[dock6_in_extension_validator])
    param_other_files = MultiFileField(label="Other input resources", min_num=1,
                                       help_text="(.pdb), (.sph), (.mol2), (.nrg), (.bmp)",
                                       validators=[multi_dock6_other_resources_validator])
    param_output_prefix = forms.CharField(required=False, label="Output file prefix",
                                          help_text="Optional",
                                          widget=forms.TextInput(attrs={'placeholder': 'filename'}))

    def clean_param_output_prefix(self):
        output_prefix = self.cleaned_data['param_output_prefix']
        return get_valid_filename(output_prefix)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(Dock6Form, self).__init__(*args, **kwargs)

        user_allowed = Q(allowed_users=self.user)
        cluster_is_public = Q(is_public=True)

        q = MPICluster.objects.filter(user_allowed | cluster_is_public)
        q = q.exclude(status=5).exclude(queued_for_deletion=True)
        toolset = ToolSet.objects.get(p2ctool_name="dock6")

        self.fields['mpi_cluster'] = MPIModelChoiceField(queryset=q, label="MPI Cluster",
                                                         toolset=toolset,
                                                         help_text="Getting an empty list? Try <a href='{0}'>creating an MPI Cluster</a> first.".format(
                                                             reverse('create_mpi')))
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Field('mpi_cluster', wrapper_class='col-xs-12'),
                css_class="col-sm-12"
            ),
            Fieldset(
                'Input',
                Div(
                    Div('param_input_file', css_class='col-xs-12'),
                    Div('param_other_files', css_class='col-xs-12 col-md-8'),
                    css_class='row-fluid col-sm-12'
                ),
            ),
            Fieldset(
                'Output',
                Div(
                    Div(AppendedText('param_output_prefix', '.out'), css_class='col-xs-12 col-md-8'),
                    css_class='row-fluid col-sm-12'
                )
            ),
        )
