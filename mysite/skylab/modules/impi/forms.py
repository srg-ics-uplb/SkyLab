from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field
from django import forms
from django.core.urlresolvers import reverse
from django.db.models import Q
from multiupload.fields import MultiFileField

from skylab.forms import MPIModelChoiceField, get_mpi_queryset_for_task_submission
from skylab.models import MPICluster, ToolSet
from skylab.modules.impi.validators import impi_files_validator


class SelectMPIFilesForm(forms.Form):
    input_files = MultiFileField(label="Image file(s) ", validators=[impi_files_validator],
                                 help_text="Only supports JPEG format (.jpeg, .jpg)")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')  # get user from form kwargs
        super(SelectMPIFilesForm, self).__init__(*args, **kwargs)

        toolset = ToolSet.objects.get(p2ctool_name="impi")

        self.fields['mpi_cluster'] = MPIModelChoiceField(queryset=get_mpi_queryset_for_task_submission(self.user), label="MPI Cluster",
                                                         toolset=toolset,
                                                         help_text="Getting an empty list? Try <a href='{0}'>creating an MPI Cluster</a> first.".format(
                                                             reverse('create_mpi')))
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(  # crispy_forms layout

            Field('mpi_cluster', wrapper_class="col-xs-12"),
            Field('input_files', wrapper_class="col-xs-12"),
        )


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
    param_operation = forms.ChoiceField(label="Image processing operation", choices=OPTIONS) #todo: required=False, validate in custom formset
    param_value = forms.IntegerField(label="Value", help_text="Select from 1-100", required=False, max_value=100,
                                     min_value=1)

    def __init__(self, *args, **kwargs):
        super(InputParameterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.disable_csrf = True
        self.helper.form_tag = False  # remove form headers

        self.helper.layout = Layout(  # layout using crispy_forms
            Div(
                Field('param_operation', css_class='parameter', wrapper_class='col-xs-10 col-sm-5'),
                Div(Field('param_value', wrapper_class='hidden'), css_class='col-xs-10 col-sm-5 col-sm-offset-1'),

                css_class='col-xs-12 form-container'
            ),
        )

    def clean(self):
        if self.cleaned_data:
            operation = self.cleaned_data.get("param_operation", None)
            value = self.cleaned_data.get('param_value', None)

            if operation:
                if operation == '3' or operation == '4':
                    if not value:
                        raise forms.ValidationError('Brightness/Contrast requires additional input value',
                                                    code='no_additional_value_provided')
