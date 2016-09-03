from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Fieldset, HTML
from django import forms
from django.db.models import Q
from django.core.validators import MinValueValidator, MaxValueValidator
from multiupload.fields import MultiFileField
from validators import odd_number_validator, txt_file_validator, tsv_file_validator, ray_file_extension_validator, \
    multi_graph_files_validator, multi_ray_files_validator
from skylab.models import MPI_Cluster
from skylab.modules.base_tool import MPIModelChoiceField


class SelectMPIFilesForm(forms.Form):
    param_pseudopotentials = forms.CharField(label="Pseudopotentials", required=False,
                                             help_text="Name of pseudopotentials needed separated by commas. (xx.UPF, yy.UPF)")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('user')
        super(SelectMPIFilesForm, self).__init__(*args, **kwargs)
        # self.fields['mpi_cluster'].queryset = MPI_Cluster.objects.filter(creator=self.user)
        current_user_as_creator = Q(creator=self.user)
        cluster_is_public = Q(shared_to_public=True)
        supports_qe = Q(supported_tools="quantum espresso")
        # is_ready = Q(status=1)
        q = MPI_Cluster.objects.filter(current_user_as_creator | cluster_is_public)
        q = q.filter(supports_qe).exclude(status=4)  # exclude unusable clusters

        self.fields['mpi_cluster'] = MPIModelChoiceField(queryset=q, label="MPI Cluster",
                                                         help_text="Getting an empty list? Try <a href='../create_mpi_cluster'>creating an MPI Cluster</a> first.")

        self.helper = FormHelper()
        self.helper.form_tag = False
        # self.helper.form_id = 'id-rayForm'
        # self.helper.form_class = 'use-tool-forms'
        # self.helper.form_method = 'post'
        # self.helper.form_action = ''
        self.helper.layout = Layout(  # crispy_forms layout


            Div(
                Field('mpi_cluster'),
                css_class="col-sm-12"
            ),

            Div(
                Div('param_pseudopotentials'),
                css_class='row-fluid col-sm-12'
            )
            ,

        )

        # def clean(self):
        #     if self.cleaned_data:
        #         if self.cleaned_data['param_mini_ranks']:
        #             if not self.cleaned_data["param_mini_ranks"]:
        #                 raise forms.ValidationError(u'-mini-ranks-per-rank: No value provided',
        #                                             code="mini_ranks_no_value_set")


class InputParameterForm(forms.Form):
    EXECUTABLE_CHOICES = (  # input parameter args
        ('', '---------'),
        ('pw.x', 'pw.x'),
    )
    executable = forms.ChoiceField(choices=EXECUTABLE_CHOICES, required=False)
    input_file = forms.FileField(label="Input file", validators=[ray_file_extension_validator], required=False)

    def __init__(self, *args, **kwargs):
        super(InputParameterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.disable_csrf = True
        self.helper.form_tag = False  # remove form headers

        # self.helper.form_id = 'id-rayForm'
        # self.helper.form_class = 'use-tool-forms'
        # self.helper.form_method = 'post'

        self.helper.layout = Layout(  # layout using crispy_forms
            Div(
                Div(Field('executable', css_class='parameter'), css_class='col-xs-5'),
                Div(Field('input_file'), css_class='col-xs-5 col-xs-offset-1'),

                css_class='row-fluid col-sm-12 form-container'
            ),
        )

    def clean(self):
        if self.cleaned_data:
            executable = self.cleaned_data["executable"]
            input_file1 = self.cleaned_data.get('input_file1')

            # print parameter, input_file1

            # if parameter == '-p':  # -p needs two input files
            #
            #     if not input_file1 or not input_file2:
            #         raise forms.ValidationError(
            #             '-p parameter requires two input files',
            #             code='-p_incomplete_input_files'
            #         )
            #
            # elif parameter == '-i' or parameter == '-s':  # -i and -s needs one input file
            #     if not input_file1:
            #         raise forms.ValidationError(
            #             '%s parameter requires one input file' % parameter,
            #             code='%s_incomplete_input_files' % parameter
            #         )
