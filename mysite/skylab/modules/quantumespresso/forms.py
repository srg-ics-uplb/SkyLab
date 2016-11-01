import json
import re

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field
from django import forms
from django.core.urlresolvers import reverse
from django.db.models import Q
from multiupload.fields import MultiFileField

from skylab.forms import MPIModelChoiceField
from skylab.models import MPICluster, ToolSet
from validators import in_files_validator


class SelectMPIFilesForm(forms.Form):
    param_pseudopotentials = forms.CharField(label="Pseudopotentials", required=False, validators=[],
                                             help_text="UPF files separated by spaces. (xx.UPF yy.UPF)")

    def clean_param_pseudopotentials(self):
        pseudopotentials = self.cleaned_data.get('param_pseudopotentials', None)
        if pseudopotentials:
            # atomic_symbol.description.UPF
            # "^[a-zA-Z]{1,3}\.([a-zA-Z0-9]+\-){1,4}([a-zA-Z0-9]+(_[a-zA-Z0-9]+)?$"

            # description = [field1-][field2-]field3-[field4-]field5[_field6]

            for upf_file in pseudopotentials.replace(' ', '').split(' '):
                p = re.match("^[a-zA-Z]{1,3}\.([a-zA-Z0-9]+\-){1,4}[a-zA-Z0-9]+(_[a-zA-Z0-9]+)?\.UPF$", upf_file)
                if not p:
                    raise forms.ValidationError("Invalid UPF file : {0}".format(upf_file))

            return json.dumps({"pseudopotentials": pseudopotentials.split(' ')})

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(SelectMPIFilesForm, self).__init__(*args, **kwargs)
        # self.fields['mpi_cluster'].queryset = MPICluster.objects.filter(creator=self.user)
        user_allowed = Q(allowed_users=self.user)
        cluster_is_public = Q(is_public=True)

        q = MPICluster.objects.filter(user_allowed | cluster_is_public)
        q = q.exclude(status=5).exclude(queued_for_deletion=True)
        toolset = ToolSet.objects.get(p2ctool_name="quantum-espresso")

        self.fields['mpi_cluster'] = MPIModelChoiceField(queryset=q, label="MPI Cluster",
                                                         toolset=toolset,
                                                         help_text="Getting an empty list? Try <a href='{0}'>creating an MPI Cluster</a> first.".format(
                                                             reverse('create_mpi')))

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


class InputParameterForm(forms.Form):
    EXECUTABLE_CHOICES = (  # input parameter args
        ('', '---------'),
        ('pw.x', 'pw.x'),
    )
    param_executable = forms.ChoiceField(label="Executable", choices=EXECUTABLE_CHOICES, required=False)
    param_input_files = MultiFileField(label="Input files (.in)", validators=[in_files_validator],
                                       required=False,
                                       help_text="Please set the following parameters as specified: pseudo_dir = '$PSEUDO_DIR/', outdir='$TMP_DIR/'")

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
                Div(Field('param_executable', css_class='parameter'), css_class='col-xs-5'),
                Div(Field('param_input_files'), css_class='col-xs-5 col-xs-offset-1'),

                css_class='row-fluid col-sm-12 form-container'
            ),
        )

