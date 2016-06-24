from django import forms
from multiupload.fields import MultiFileField
from validators import pdbqt_file_extension_validator
from skylab.models import MPI_Cluster
from django.db.models import Q


class VinaBasicForm(forms.Form):
    # Input (receptor and ligand(s) are required)
    param_receptor = forms.FileField(validators=[pdbqt_file_extension_validator])
    param_flex = forms.FileField(validators=[pdbqt_file_extension_validator], required=False)
    param_ligands = MultiFileField(min_num=1)

    # Search space (required)
    param_center_x = forms.IntegerField()
    param_center_y = forms.IntegerField()
    param_center_z = forms.IntegerField()

    param_size_x = forms.IntegerField()
    param_size_y = forms.IntegerField()
    param_size_z = forms.IntegerField()

    # Output (optional)
    param_out = forms.CharField(required=False)
    param_log = forms.CharField(required=False)

    # Misc (optional)
    # param_cpu = forms.IntegerField(required=False) removed since default setting detects current number of CPUs
    param_seed = forms.IntegerField(required=False)
    param_exhaustiveness = forms.IntegerField(required=False)
    param_num_modes = forms.IntegerField(required=False)
    param_energy_range = forms.IntegerField(required=False)

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


# add cripsy form helper

class VinaAdvancedForm(forms.Form):
    param_score_only = forms.BooleanField()
    param_local_only = forms.BooleanField()
    param_randomize_only = forms.BooleanField()

    param_weight_gauss1 = forms.IntegerField()
    param_weight_gauss2 = forms.IntegerField()
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
