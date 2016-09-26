from crispy_forms.bootstrap import AppendedText, Tab, TabHolder
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Fieldset
from django import forms
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils.text import get_valid_filename
from multiupload.fields import MultiFileField

from skylab.models import MPICluster
from skylab.modules.basetool import MPIModelChoiceField
from validators import pdbqt_file_extension_validator, dpf_file_extension_validator, gpf_file_extension_validator, \
    multi_grid_map_file_validator


class AutodockForm(forms.Form):
    # + ligand .pdbqt + receptor.pdbqt
    param_receptor_file = forms.FileField(label="Receptor", help_text="(.pdbqt)",
                                          validators=[pdbqt_file_extension_validator])
    param_ligand_file = forms.FileField(label="Ligand", help_text="(.pdbqt)",
                                        validators=[pdbqt_file_extension_validator])
    param_dpf_file = forms.FileField(label="Dock parameter", help_text="(.dpf)",
                                     validators=[dpf_file_extension_validator])  # .dpf file
    param_grid_files = MultiFileField(min_num=1, validators=[multi_grid_map_file_validator], label="Grid map files",
                                      help_text="Files generated by AutoGrid (.map, .fld, .xyz)")  # .map, .fld, .xyz
    param_dlg_filename = forms.CharField(required=False, label="Log filename", help_text="default: dpf_filename.dlg",
                                         widget=forms.TextInput(attrs={
                                             'placeholder': 'filename'}))  # default: dpf_filename.dlg   can be ommitted
    param_k = forms.BooleanField(required=False, label="-k",
                                 help_text="Keep original residue numbers")
    param_i = forms.BooleanField(required=False, label="-i",
                                 help_text="Ignore header-checking")
    param_t = forms.BooleanField(required=False, label="-t",
                                 help_text="Parse the PDBQT file to check torsions, then stop.")
    param_d = forms.BooleanField(required=False, label="-d",
                                 help_text="Increment debug level")

    def clean_param_dlg_filename(self):
        output_prefix = self.cleaned_data['param_dlg_filename']
        return get_valid_filename(output_prefix)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(AutodockForm, self).__init__(*args, **kwargs)

        current_user_as_creator = Q(creator=self.user)
        cluster_is_public = Q(shared_to_public=True)
        supports_autodock = Q(toolset__display_name="AutoDock4")
        # is_ready = Q(status=1)
        q = MPICluster.objects.filter(current_user_as_creator | cluster_is_public)
        q = q.filter(supports_autodock).exclude(status=5)  # exclude unusable clusters

        self.fields['mpi_cluster'] = MPIModelChoiceField(queryset=q, label="MPI Cluster",
                                                         help_text="Getting an empty list? Try <a href='{0}'>creating an MPI Cluster</a> first.".format(
                                                             reverse('create_mpi')))

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                # Field('mpi_cluster', wrapper_class='col-xs-5'),
                Field('mpi_cluster', wrapper_class='col-xs-6'),
                css_class="col-sm-12"
            ),
            Fieldset(
                'Input',
                Div(
                    Div('param_receptor_file', css_class='col-xs-6'),
                    Div('param_ligand_file', css_class='col-xs-6'),
                    Div('param_dpf_file', css_class='col-xs-6'),
                    Div('param_grid_files', css_class='col-xs-6'),
                    css_class='row-fluid col-sm-12'
                )
            ),
            Fieldset(
                'Output',
                Div(
                    Div(AppendedText('param_dlg_filename', '.dlg'), css_class='col-xs-5'),
                    css_class='row-fluid col-sm-12'
                ),
            ),
            Fieldset(
                'Other parameters',
                # Div(
                #     Div(AppendedText('param_dlg_filename', '.dlg'),css_class='col-xs-4'),
                #     css_class='row-fluid col-sm-12'
                # ),
                Div(
                    Div('param_k', css_class='col-xs-12'),
                    Div('param_i', css_class='col-xs-12'),
                    Div('param_t', css_class='col-xs-12'),
                    Div('param_d', css_class='col-xs-12'),
                    # Div('param_k', css_class="col-xs-6"),
                    # Div('param_i', css_class="col-xs-6"),
                    # Div('param_t', css_class="col-xs-6"),
                    # Div('param_d', css_class="col-xs-6"),
                    css_class='row-fluid col-xs-12'
                )
            ),
        )



class AutogridForm(forms.Form):
    param_receptor_file = forms.FileField(label="Receptor", help_text="(.pdbqt)",
                                          validators=[pdbqt_file_extension_validator])
    param_ligand_file = forms.FileField(label="Ligand", help_text="(.pdbqt)",
                                        validators=[pdbqt_file_extension_validator])
    param_gpf_file = forms.FileField(label="Grid parameter", help_text="(.gpf)",
                                     validators=[gpf_file_extension_validator])
    param_glg_filename = forms.CharField(label="Output filename", required=False, help_text="default: gpf_filename.glg",
                                         widget=forms.TextInput(attrs={'placeholder': 'filename'}))
    param_d = forms.BooleanField(required=False, label="-d",
                                 help_text="Increment debug level")
    param_use_with_autodock = forms.BooleanField(required=False, label='Use with AutoDock')

    param_dpf_file = forms.FileField(required=False, label="Dock parameter", help_text="(.dpf)",
                                     validators=[dpf_file_extension_validator])  # .dpf file

    param_dlg_filename = forms.CharField(required=False, label="Log filename", help_text="default: dpf_filename.dlg",
                                         widget=forms.TextInput(attrs={
                                             'placeholder': 'filename'}))  # default: dpf_filename.dlg   can be ommitted
    param_k = forms.BooleanField(required=False, label="-k",
                                 help_text="Keep original residue numbers")
    param_i = forms.BooleanField(required=False, label="-i",
                                 help_text="Ignore header-checking")
    param_t = forms.BooleanField(required=False, label="-t",
                                 help_text="Parse the PDBQT file to check torsions, then stop.")
    param_d_dock = forms.BooleanField(required=False, label="-d",
                                      help_text="Increment debug level")

    def clean_param_dlg_filename(self):
        output_prefix = self.cleaned_data['param_dlg_filename']
        return get_valid_filename(output_prefix)

    def clean_param_glg_filename(self):
        output_prefix = self.cleaned_data['param_glg_filename']
        return get_valid_filename(output_prefix)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(AutogridForm, self).__init__(*args, **kwargs)

        current_user_as_creator = Q(creator=self.user)
        cluster_is_public = Q(shared_to_public=True)
        supports_autodock = Q(toolset__display_name="AutoDock4")
        # is_ready = Q(status=1)
        q = MPICluster.objects.filter(current_user_as_creator | cluster_is_public)
        q = q.filter(supports_autodock).exclude(status=5)  # exclude unusable clusters

        self.fields['mpi_cluster'] = MPIModelChoiceField(queryset=q, label="MPI Cluster",
                                                         help_text="Getting an empty list? Try <a href='{0}'>creating an MPI Cluster</a> first.".format(
                                                             reverse('create_mpi')))

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            TabHolder(
                Tab(
                    'AutoGrid4',
                    Div(
                        Field('mpi_cluster', wrapper_class='col-xs-6'),
                        Div('param_use_with_autodock', css_class='col-xs-4 col-xs-offset-1'),
                        css_class="col-sm-12"
                    ),
                    Fieldset(
                        'Input',
                        Div(
                            Div('param_receptor_file', css_class='col-xs-4'),
                            Div('param_ligand_file', css_class='col-xs-4'),
                            Div('param_gpf_file', css_class='col-xs-4'),
                            css_class='row-fluid col-sm-12'
                        )
                    ),
                    Fieldset(
                        'Output',
                        Div(
                            Div(AppendedText('param_glg_filename', '.glg'), css_class='col-xs-6'),
                            css_class='row-fluid col-sm-12'
                        ),
                    ),
                    Fieldset(
                        'Other parameters',
                        Div(
                            Div('param_d', css_class='col-xs-12'),

                            css_class='col-xs-12'
                        )
                    ),
                ),
                Tab(
                    'AutoDock4',
                    Fieldset(
                        'Input',
                        Div(
                            Div('param_dpf_file', css_class='col-xs-6'),
                            css_class='row-fluid col-sm-12'
                        )
                    ),
                    Fieldset(
                        'Output',
                        Div(
                            Div(AppendedText('param_dlg_filename', '.dlg'), css_class='col-xs-6'),
                            css_class='row-fluid col-sm-12'
                        ),
                    ),
                    Fieldset(
                        'Other parameters',
                        Div(
                            Div('param_k', css_class='col-xs-12'),
                            Div('param_i', css_class='col-xs-12'),
                            Div('param_t', css_class='col-xs-12'),
                            Div('param_d_dock', css_class='col-xs-12'),
                            # Div('param_k', css_class="col-xs-6"),
                            # Div('param_i', css_class="col-xs-6"),
                            # Div('param_t', css_class="col-xs-6"),
                            # Div('param_d_dock', css_class="col-xs-6"),
                            css_class='row-fluid col-xs-12'
                        )
                    ),

                )
            )
        )

    def clean(self):
        if self.cleaned_data['param_use_with_autodock']:
            if not self.cleaned_data['param_dpf_file']:
                raise forms.ValidationError(u'Missing dock parameter file', code="missing_dock_parameter")
