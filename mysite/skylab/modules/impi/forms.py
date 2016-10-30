from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field
from django import forms
from django.core.urlresolvers import reverse
from django.db.models import Q

from skylab.forms import MPIModelChoiceField
from skylab.models import MPICluster, ToolSet
from skylab.modules.impi.validators import jpeg_file_extension_validator


class SelectMPIFilesForm(forms.Form):
    param_input_file = forms.FileField(label="Image file ", validators=[jpeg_file_extension_validator], required=False,
                                       help_text="Only supports JPEG format (.jpeg, .jpg)")

    # , validators=[in_file_extension_validator],


    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        print self.user
        super(SelectMPIFilesForm, self).__init__(*args, **kwargs)
        # print self.user
        # self.fields['mpi_cluster'].queryset = MPICluster.objects.filter(creator=self.user)
        user_allowed = Q(allowed_users=self.user)
        cluster_is_public = Q(is_public=True)

        q = MPICluster.objects.filter(user_allowed | cluster_is_public)
        q = q.exclude(status=5).exclude(queued_for_deletion=True)

        toolset = ToolSet.objects.get(p2ctool_name="impi")

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
                Div('param_input_file'),
                css_class='row-fluid col-sm-12'
            )

        )

    def clean(self):
        cluster = self.cleaned_data['mpi_cluster']
        print cluster.cluster_name


class InputParameterForm(forms.Form):
    OPTIONS = (  # input parameter args
        ('', '---------'),
        ('1', 'Mean'),
        ('2', 'Median'),
        ('3', 'Brightness'),
        ('4', 'Contrast'),
        ('5', 'Invert'),
        ('7', 'Noise reduction'),
        ('8', 'Laplace (4-neighbor)'),
        ('9', 'Laplace (8-neighbor)'),
        ('10', 'Sobel')
    )
    param_operation = forms.ChoiceField(label="Operation", choices=OPTIONS, required=False)
    param_value = forms.IntegerField(label="Value", help_text="Select from 1-100", required=False, max_value=100,
                                     min_value=1)

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
                Div(Field('param_operation', css_class='parameter'), css_class='col-xs-5'),
                Div(Field('param_value', wrapper_class='hidden'), css_class='col-xs-5 col-xs-offset-1'),

                css_class='row-fluid col-sm-12 form-container'
            ),
        )

    def clean(self):
        if self.cleaned_data:
            operation = self.cleaned_data.get("param_operation", None)
            value = self.cleaned_data.get('value', None)

            if operation:
                if operation == 3 or operation == 4:
                    if not value:
                        raise forms.ValidationError('Brightness/Contrast requires additional input value',
                                                    code='no_additional_value_provided')
