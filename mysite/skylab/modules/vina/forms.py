from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Fieldset
from django import forms
from django.core.urlresolvers import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q
from multiupload.fields import MultiFileField

from skylab.forms import MPIModelChoiceField, get_mpi_queryset_all
from skylab.models import MPICluster, ToolSet
from validators import pdbqt_file_extension_validator, multi_pdbqt_file_validator


# for value type reference:  https://github.com/ryancoleman/autodock-vina/blob/master/src/main/main.cpp
# see line 459 onwards

class VinaForm(forms.Form):
    # Input (receptor and ligand(s) are required)
    param_receptor = forms.FileField(validators=[pdbqt_file_extension_validator], label="Receptor file",
                                     help_text="Rigid part of the receptor (.pdbqt)")
    param_flex = forms.FileField(required=False, validators=[pdbqt_file_extension_validator], label="Flex file",
                                 help_text="Flexible side chains, if any (.pdbqt)")
    param_ligands = MultiFileField(min_num=1, validators=[multi_pdbqt_file_validator],
                                   label="Ligand file(s)",
                                   help_text="(.pdbqt)")

    # Search space (required) IMPORTANT!: if advanced options will be enabled set search space to required=False
    param_center_x = forms.DecimalField(label="Center X coordinate")
    param_center_y = forms.DecimalField(label="Center Y coordinate")
    param_center_z = forms.DecimalField(label="Center Z coordinate")

    param_size_x = forms.DecimalField(label="Size X (Angstroms)")
    param_size_y = forms.DecimalField(label="Size Y (Angstroms)")
    param_size_z = forms.DecimalField(label="Size Z (Angstroms)")

    # Output (optional) removed because of the use-case aims to support multiple ligands
    # param_out = forms.CharField(required=False, label="Output model filename",
    #                             help_text="The default is chosen based on the ligand file name")
    # param_log = forms.CharField(required=False, label="Write a log file",
    #                             help_text="This will output a log file with this filename")
    # Misc (optional)
    # param_cpu = forms.IntegerField(required=False) removed since default setting detects current number of CPUs

    param_seed = forms.IntegerField(required=False, label="Explicit random seed")
    param_exhaustiveness = forms.IntegerField(required=False, label="Exhaustiveness of the global search",
                                              help_text=" (Roughly proportional to time): 1+ .<br>Choose a number from 1 to 8.",
                                              min_value=1, max_value=8,
                                              validators=[MinValueValidator(1), MaxValueValidator(8)],
                                              widget=forms.NumberInput(
                                                  attrs={'placeholder': '8'}))  # 1-8 default 8
    param_num_modes = forms.IntegerField(required=False, label="Max number of binding modes to generate", min_value=1,
                                         max_value=10, validators=[MinValueValidator(1), MaxValueValidator(10)],
                                         help_text="Choose a number from 1 to 10.",
                                         widget=forms.NumberInput(
                                             attrs={'placeholder': '9'}))  # 1-10 default 9
    param_energy_range = forms.DecimalField(required=False, label="Energy range",
                                            help_text="Maximum energy difference between the best binding mode and the worst one displayed (kcal/mol).<br>Choose a decimal from 1.0 to 3.0 .",
                                            min_value=1, max_value=3,
                                            validators=[MinValueValidator(1), MaxValueValidator(3)],

                                            widget=forms.NumberInput(
                                                attrs={
                                                    'placeholder': '3.0'}))  # 1-3 default 3.0 float-value in cpp

    # # Advanced
    # param_score_only = forms.BooleanField(required=False, label="--score_only", help_text="Search space can be omitted")
    # param_local_only = forms.BooleanField(required=False, label="--local_only ", help_text="Do local search only    ")
    # param_randomize_only = forms.BooleanField(required=False, label="--randomize_only",
    #                                           help_text="Randomize input, attempting to avoid clashes")
    #
    # # changed placeholder values to string to prevent rounding
    # param_weight_gauss1 = forms.DecimalField(required=False, label="Gauss 1 weight",
    #                                          widget=forms.NumberInput(attrs={'placeholder': ' -0.035579'}))
    # param_weight_gauss2 = forms.DecimalField(required=False, label="Gauss 2 weight",
    #                                          widget=forms.NumberInput(attrs={'placeholder': '-0.005156'}))
    # param_weight_repulsion = forms.DecimalField(required=False, label="Repulsion weight", widget=forms.NumberInput(
    #     attrs={'placeholder': '0.84024500000000002'}))
    # param_weight_hydrophobic = forms.DecimalField(required=False, label="Hydrophobic weight", widget=forms.NumberInput(
    #     attrs={'placeholder': '-0.035069000000000003'}))
    # param_weight_hydrogen = forms.DecimalField(required=False, label="Hydrogen bond weight", widget=forms.NumberInput(
    #     attrs={'placeholder': '-0.58743900000000004'}))
    # param_weight_rot = forms.DecimalField(required=False, label="N_rot weight", widget=forms.NumberInput(
    #     attrs={'placeholder': '0.058459999999999998'}))


    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(VinaForm, self).__init__(*args, **kwargs)

        toolset = ToolSet.objects.get(p2ctool_name="vina")

        self.fields['mpi_cluster'] = MPIModelChoiceField(queryset=get_mpi_queryset_all(self.user), label="MPI Cluster",
                                                         toolset=toolset,
                                                         help_text="Getting an empty list? Try <a href='{0}'>creating an MPI Cluster</a> first.".format(
                                                             reverse('create_mpi')))

        self.helper = FormHelper()
        self.helper.form_tag = False

        self.helper.layout = Layout(  # crispy_forms layout
            # TabHolder(
            #     Tab('Basic Parameters',

                    Field('mpi_cluster', wrapper_class='col-xs-12'),

                    Fieldset(
                        'Input',
                        Field('param_receptor', wrapper_class='col-xs-12'),
                        Field('param_ligands', wrapper_class='col-xs-12 col-md-8'),
                        Field('param_flex', wrapper_class='col-xs-12'),
                        css_class='col-xs-12'
                    ),
                    Fieldset(
                        'Search space',
                        Field('param_center_x', wrapper_class='col-xs-12 col-md-4'),
                        Field('param_center_y', wrapper_class='col-xs-12 col-md-4'),
                        Field('param_center_z', wrapper_class='col-xs-12 col-md-4'),
                        Field('param_size_x', wrapper_class='col-xs-12 col-md-4'),
                        Field('param_size_y', wrapper_class='col-xs-12 col-md-4'),
                        Field('param_size_z', wrapper_class='col-xs-12 col-md-4'),
                        css_class='col-xs-12'
                    ),
                    Fieldset(
                        'Miscellaneous',
                        Field('param_seed', wrapper_class="col-xs-12 col-md-8"),
                        Field('param_exhaustiveness', wrapper_class="col-xs-12 col-md-8"),
                        Field('param_num_modes', wrapper_class="col-xs-12 col-md-8"),
                        Field('param_energy_range', wrapper_class="col-xs-12 col-md-8"),
                        css_class='col-xs-12'
                    ),

            # ),
            # disabled these features since in vina website : AutoDock Vina's "advanced options"
            # are intended to be primarily used by people interested in methods development rather than the end users.
            # Tab('Advanced Parameters',
            #         Fieldset(
            #             'Experimental options',
            #             Div('param_score_only', css_class='col-xs-12'),
            #             Div('param_local_only', css_class='col-xs-12'),
            #             Div('param_randomize_only', css_class='col-xs-12'),
            #         ),
            #         Fieldset(
            #             'Weights',
            #             Div(
            #                 Field('param_weight_gauss1', wrapper_class='col-xs-10'),
            #                 css_class='col-xs-6'
            #             ),
            #             Div(
            #                 Field('param_weight_gauss2', wrapper_class='col-xs-10'),
            #                 css_class='col-xs-6'
            #             ),
            #             Div(
            #                 Field('param_weight_repulsion', wrapper_class='col-xs-10'),
            #                 css_class='col-xs-6'
            #             ),
            #             Div(
            #                 Field('param_weight_hydrophobic', wrapper_class='col-xs-10'),
            #                 css_class='col-xs-6'
            #             ),
            #             Div(
            #                 Field('param_weight_hydrogen', wrapper_class='col-xs-10'),
            #                 css_class='col-xs-6'
            #             ),
            #             Div(
            #                 Field('param_weight_rot', wrapper_class='col-xs-10'),
            #                 css_class='col-xs-6'
            #             ),
            #         ),
            #
            #         css_class='row-fluid col-sm-12'
            #         ),
            #     css_id="form-tab-holder",
            # )
        )

    # def clean(self):
    #     if self.cleaned_data:
    #         if not self.cleaned_data['param_score_only']:
    #             if not self.cleaned_data.get('param_center_x') or not self.cleaned_data.get(
    #                     'param_center_y') or not self.cleaned_data.get('param_center_z') or not self.cleaned_data.get(
    #                     'param_size_x') or not self.cleaned_data.get('param_size_y') or not self.cleaned_data.get(
    #                     'param_size_z'):
    #                 raise forms.ValidationError(u'Search space fields are required', code="search_space_incomplete")

class VinaSplitForm(forms.Form):
    param_input = forms.FileField(label="Input file (.pdbqt)", help_text="Vina docking result",
                                  validators=[pdbqt_file_extension_validator])

    # param_ligand_prefix = forms.CharField(label="Prefix for ligands", help_text="Optional", required=False)
    # param_flex_prefix = forms.CharField(label="Prefix for side chains", help_text="Optional", required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(VinaSplitForm, self).__init__(*args, **kwargs)

        toolset = ToolSet.objects.get(p2ctool_name="vina")

        self.fields['mpi_cluster'] = MPIModelChoiceField(queryset=get_mpi_queryset_all(self.user), label="MPI Cluster",
                                                         toolset=toolset,
                                                         help_text="Getting an empty list? Try <a href='{0}'>creating an MPI Cluster</a> first.".format(
                                                             reverse('create_mpi')))
        self.helper = FormHelper()
        self.helper.form_tag = False

        self.helper.layout = Layout(
            'mpi_cluster',
            'param_input',
        )
