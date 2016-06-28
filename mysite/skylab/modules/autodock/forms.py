from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Fieldset, HTML, Submit
from crispy_forms.bootstrap import AppendedText, Tab, TabHolder
from multiupload.fields import MultiFileField
from validators import pdbqt_file_extension_validator, multi_pdbqt_file_validator
from skylab.models import MPI_Cluster
from django.db.models import Q
from django.core.validators import MinValueValidator, MaxValueValidator
from skylab.modules.base_tool import MPIModelChoiceField


class AutodockForm(forms.Form):
    # + ligand .pdbqt + receptor.pdbqt
    param_dpf_file = forms.FileField()  # .dpf file
    param_dlg_filename = forms.CharField(required=False)  # default: dpf_filename.dlg   can be ommitted
    param_k = forms.BooleanField(required=False)  # (Keep original residue numbers)
    param_i = forms.BooleanField(required=False)  # (Ignore header-checking)
    param_t = forms.BooleanField(required=False)  # (Parse the PDBQT file to check torsions, then stop.)
    param_d = forms.BooleanField(required=False)  # (Increment debug level)
    param_c = forms.BooleanField(required=False)  # (Print copyright notice)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('user')
        super(AutogridForm, self).__init__(*args, **kwargs)

        current_user_as_creator = Q(creator=self.user)
        cluster_is_public = Q(shared_to_public=True)
        supports_autodock = Q(supported_tools="autodock")
        # is_ready = Q(status=1)
        q = MPI_Cluster.objects.filter(current_user_as_creator | cluster_is_public)
        q = q.filter(supports_autodock).exclude(status=4)  # exclude unusable clusters

        self.fields['mpi_cluster'] = MPIModelChoiceField(queryset=q,
                                                         help_text="Getting an empty list? Try <a href='../create_mpi_cluster'>creating an MPI Cluster</a> first.")

        self.helper = FormHelper()
        self.helper.form_tag = False


class AutogridForm(forms.Form):
    # + ligand .pdbqt + receptor.pdbqt
    param_gpf_file = forms.FileField()
    param_glg_file = forms.CharField(required=False)
    param_d = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('user')
        super(AutogridForm, self).__init__(*args, **kwargs)

        current_user_as_creator = Q(creator=self.user)
        cluster_is_public = Q(shared_to_public=True)
        supports_autodock = Q(supported_tools="autodock")
        # is_ready = Q(status=1)
        q = MPI_Cluster.objects.filter(current_user_as_creator | cluster_is_public)
        q = q.filter(supports_autodock).exclude(status=4)  # exclude unusable clusters

        self.fields['mpi_cluster'] = MPIModelChoiceField(queryset=q,
                                                         help_text="Getting an empty list? Try <a href='../create_mpi_cluster'>creating an MPI Cluster</a> first.")

        self.helper = FormHelper()
        self.helper.form_tag = False
