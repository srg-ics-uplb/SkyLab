from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, MultiField, Div, Field
from crispy_forms.bootstrap import InlineField
from django.db.models import Q
from skylab.models import MPI_Cluster


class SelectMPIForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('user')
        super(SelectMPIForm, self).__init__(*args, **kwargs)
        # self.fields['mpi_cluster'].queryset = MPI_Cluster.objects.filter(creator=self.user)
        current_user_as_creator = Q(creator=self.user)
        cluster_is_public = Q(shared_to_public=True)
        supports_gamess = Q(supported_tools="gamess")
        # is_ready = Q(status=1)
        q = MPI_Cluster.objects.filter(current_user_as_creator | cluster_is_public)
        q = q.filter(supports_gamess).exclude(status=4)

        self.fields['mpi_cluster'] = forms.ModelChoiceField(queryset=q)

        self.helper = FormHelper()
        self.helper.form_tag = False
        # self.helper.form_id = 'id-rayForm'
        # self.helper.form_class = 'use-tool-forms'
        # self.helper.form_method = 'post'
        self.helper.form_action = ''
        self.helper.layout = Layout(    #crispy_forms layout
            Fieldset(
                'Use Ray',
                Div(
                    'mpi_cluster',
                    css_class ="col-sm-5"
                )

            )
        )

class InputParameterForm(forms.Form):
    PARAMETER_CHOICES = (   #input parameter args
                        ('-p','-p'),
                        ('-s','-s'),
    )
    parameter = forms.ChoiceField(choices=PARAMETER_CHOICES)
    avg_outer_distance = forms.DecimalField(label="Average outer distance", required=False, help_text="Optional.")
    std_deviation = forms.DecimalField(label="Standard deviation", required=False, help_text="Optional.")
    input_file1 = forms.FileField(label="Input file 1")
    input_file2 = forms.FileField(label="Input file 2")
    def __init__(self, *args, **kwargs):
        super(InputParameterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False    #remove form headers
        # self.helper.form_id = 'id-rayForm'
        # self.helper.form_class = 'use-tool-forms'
        # self.helper.form_method = 'post'

        self.helper.form_action = ''

        self.helper.layout = Layout(    #layout using crispy_forms
            Div(
                Div('parameter', css_class = 'col-sm-1'),
                Div('avg_outer_distance', css_class = 'col-sm-3 col-sm-offset-1'),
                Field('std_deviation', wrapper_class = 'col-sm-3 col-sm-offset-1'),

                Field('input_file1', wrapper_class = 'col-sm-4'),
                Field('input_file2', wrapper_class = 'col-sm-4 col-sm-offset-1'),
                css_class = 'col-sm-12'
            ),
        )