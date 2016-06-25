from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Fieldset, HTML
from multiupload.fields import MultiFileField
from validators import pdbqt_file_extension_validator
from skylab.models import MPI_Cluster
from django.db.models import Q


# for value type reference:  https://github.com/ryancoleman/autodock-vina/blob/master/src/main/main.cpp
# see line 459 onward

class VinaBasicForm(forms.Form):

    # Input (receptor and ligand(s) are required)
    param_receptor = forms.FileField(validators=[pdbqt_file_extension_validator])
    param_flex = forms.FileField(validators=[pdbqt_file_extension_validator], required=False)
    param_ligands = MultiFileField(min_num=1)

    # Search space (required)
    param_center_x = forms.DecimalField()
    param_center_y = forms.DecimalField()
    param_center_z = forms.DecimalField()

    param_size_x = forms.DecimalField()
    param_size_y = forms.DecimalField()
    param_size_z = forms.DecimalField()

    # Output (optional)
    param_out = forms.CharField(required=False)
    param_log = forms.CharField(required=False)

    # Misc (optional)
    # param_cpu = forms.IntegerField(required=False) removed since default setting detects current number of CPUs
    param_seed = forms.IntegerField(required=False)
    param_exhaustiveness = forms.IntegerField(required=False)  # 1-8 default 8
    param_num_modes = forms.IntegerField(required=False)  # 1-10 default 9
    param_energy_range = forms.DecimalField(required=False)  # 1-3 default 3.0 float-value in cpp

    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('user')
        super(VinaBasicForm, self).__init__(*args, **kwargs)

        current_user_as_creator = Q(creator=self.user)
        cluster_is_public = Q(shared_to_public=True)
        supports_vina = Q(supported_tools="vina")
        # is_ready = Q(status=1)
        q = MPI_Cluster.objects.filter(current_user_as_creator | cluster_is_public)
        q = q.filter(supports_vina).exclude(status=4)  # exclude unusable clusters

        self.fields['mpi_cluster'] = forms.ModelChoiceField(queryset=q,
                                                            help_text="Getting a blank list? Try <a href='../create-mpi-cluster'>creating an MPI Cluster</a> first.")

        self.helper = FormHelper()
        self.helper.form_tag = False
        # self.helper.form_id = 'id-rayForm'
        # self.helper.form_class = 'use-tool-forms'
        # self.helper.form_method = 'post'
        # self.helper.form_action = ''
        self.helper.layout = Layout(  # crispy_forms layout
            Div(
                Field('mpi_cluster', wrapper_class='col-xs-5'),
                css_class="col-sm-12"
            ),
            Fieldset(
                'Input',
                Div(
                    Div('param_receptor', css_class='col-xs-4'),
                    Div('param_flex', css_class='col-xs-4'),
                    Div('param_ligands', css_class='col-xs-4'),
                    css_class='row-fluid col-sm-12'
                )
            ),
            Fieldset(
                'Input',
                Div(
                    Div('param_receptor', css_class='col-xs-4'),
                    Div('param_flex', css_class='col-xs-4'),
                    Div('param_ligands', css_class='col-xs-4'),
                    css_class='row-fluid col-sm-12'
                )
            ),

        )

# add cripsy form helper

class VinaAdvancedForm(forms.Form):
    param_score_only = forms.BooleanField()
    param_local_only = forms.BooleanField()
    param_randomize_only = forms.BooleanField()

    param_weight_gauss1 = forms.DecimalField()
    param_weight_gauss2 = forms.DecimalField()
    param_weight_repulsion = forms.DecimalField()
    param_weight_hydrophobic = forms.DecimalField()
    param_weight_hydrogen = forms.DecimalField()
    param_weight_rot = forms.DecimalField()

    def __init__(self, *args, **kwargs):
        super(VinaAdvancedForm, self).__init__(*args, **kwargs)


# add crispy form helper

class VinaSplitForm(forms.Form):
    param_input = forms.FileField(validators=[pdbqt_file_extension_validator])
    param_ligand_prefix = forms.CharField()
    param_flex_prefix = forms.CharField()

    def __init__(self, *args, **kwargs):
        super(VinaSplitForm, self).__init__(*args, **kwargs)

        #       add crispy form helper
