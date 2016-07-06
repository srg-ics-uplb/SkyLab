from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Fieldset, HTML, Submit
from crispy_forms.bootstrap import AppendedText, Tab, TabHolder
from multiupload.fields import MultiFileField
from validators import multi_dock6_grid_other_resources_validator
from skylab.models import MPI_Cluster
from django.db.models import Q
from skylab.modules.base_tool import MPIModelChoiceField


class GridForm(forms.Form):
    param_input_file = forms.FileField()
    param_other_files = MultiFileField(min_num=1, validators=[multi_dock6_grid_other_resources_validator])
    param_output_prefix = forms.CharField(required=False, label="Output file prefix",
                                          help_text="default: input_filename.out")
    param_terse = forms.BooleanField(required=False, label="-t", help_text="Terse program output")
    param_verbose = forms.BooleanField(required=False, label="-v", help_text="Verbose program output")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(GridForm, self).__init__(*args, **kwargs)

        current_user_as_creator = Q(creator=self.user)
        cluster_is_public = Q(shared_to_public=True)
        supports_autodock = Q(supported_tools="autodock")
        # is_ready = Q(status=1)
        q = MPI_Cluster.objects.filter(current_user_as_creator | cluster_is_public)
        q = q.filter(supports_autodock).exclude(status=4)  # exclude unusable clusters

        self.fields['mpi_cluster'] = MPIModelChoiceField(queryset=q, label="MPI Cluster",
                                                         help_text="Getting an empty list? Try <a href='../create_mpi_cluster'>creating an MPI Cluster</a> first.")

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(

        )


class DockForm(forms.Form):
    param_input_file = forms.FileField()
    param_other_files = MultiFileField(min_num=1, validators=[multi_dock6_grid_other_resources_validator])
    param_output_prefix = forms.CharField(required=False, label="Output file prefix",
                                          help_text="default: input_filename.out")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(DockForm, self).__init__(*args, **kwargs)

        current_user_as_creator = Q(creator=self.user)
        cluster_is_public = Q(shared_to_public=True)
        supports_autodock = Q(supported_tools="autodock")
        # is_ready = Q(status=1)
        q = MPI_Cluster.objects.filter(current_user_as_creator | cluster_is_public)
        q = q.filter(supports_autodock).exclude(status=4)  # exclude unusable clusters

        self.fields['mpi_cluster'] = MPIModelChoiceField(queryset=q, label="MPI Cluster",
                                                         help_text="Getting an empty list? Try <a href='../create_mpi_cluster'>creating an MPI Cluster</a> first.")

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(

        )
