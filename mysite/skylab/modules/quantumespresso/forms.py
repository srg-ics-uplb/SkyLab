import json
import re

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field
from django import forms
from django.core.urlresolvers import reverse
from django.db.models import Q
from multiupload.fields import MultiFileField

from skylab.forms import MPIModelChoiceField, get_mpi_queryset_all
from skylab.models import MPICluster, ToolSet
from validators import in_files_validator


class SelectMPIFilesForm(forms.Form):
    param_pseudopotentials = forms.CharField(label="Pseudopotentials", validators=[],
                                             help_text="Required UPF files separated by commas. (xx.UPF,yy.UPF)")

    def clean_param_pseudopotentials(self):
        pseudopotentials = self.cleaned_data.get('param_pseudopotentials', None)
        if pseudopotentials:
            # atomic_symbol.description.UPF
            # "^[a-zA-Z]{1,3}\.([a-zA-Z0-9]+\-){1,4}([a-zA-Z0-9]+(_[a-zA-Z0-9]+)?$"

            # description = [field1-][field2-]field3-[field4-]field5[_field6]

            for upf_file in pseudopotentials.replace(' ', '').split(','):
                p = re.match("^[a-zA-Z]{1,3}\.([a-zA-Z0-9]+\-){1,4}[a-zA-Z0-9]+(_[a-zA-Z0-9]+)?\.UPF$", upf_file)
                if not p:
                    raise forms.ValidationError("Invalid UPF file : {0}".format(upf_file))

            return json.dumps({"pseudopotentials": pseudopotentials.split(' ')})
        else: raise forms.ValidationError("No pseudopotentials specified")


    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(SelectMPIFilesForm, self).__init__(*args, **kwargs)
        # self.fields['mpi_cluster'].queryset = MPICluster.objects.filter(creator=self.user)

        toolset = ToolSet.objects.get(p2ctool_name="espresso")

        self.fields['mpi_cluster'] = MPIModelChoiceField(queryset=get_mpi_queryset_all(self.user), label="MPI Cluster",
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
            'mpi_cluster',
            'param_pseudopotentials'
        )


class InputParameterForm(forms.Form):
    EXECUTABLE_CHOICES = (  # input parameter args
        ('', '---------'), #supported tools
        ('pw.x', 'PWscf / pw.x'),
        ('cp.x', 'CPV / cp.x'),
        # ('pwcond.x','pwcond.x'),
        # ('bands.x','bands.x'),

        # ('neb.x', 'neb.x'),
        #('ph.x','ph.x'), #PHonon

    )
    param_executable = forms.ChoiceField(label="Executable", choices=EXECUTABLE_CHOICES) #todo: required=False, validate formset
    param_input_files = MultiFileField(label="Input files (.in)", validators=[in_files_validator],
                                       required=False)#,
                                      # help_text="Please set the following parameters as specified: <br>pseudo_dir = '/mirror/espresso-5.4.0/pseudo/',<br> outdir='/mirror/espresso-5.4.0/tempdir/'",)
                                     #  help_text="Please set the following parameters as specified: pseudo_dir = '$PSEUDO_DIR/', outdir='$TMP_DIR/'")

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
                Field('param_executable', css_class='parameter', wrapper_class='col-xs-10 col-sm-5'),
                Div(Field('param_input_files'), css_class='col-xs-12 col-sm-5 col-sm-offset-1'),

                css_class='col-xs-12 form-container'
            ),
        )

