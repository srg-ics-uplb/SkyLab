from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field
from django import forms
from django.db.models import Q
from multiupload.fields import MultiFileField

from skylab.models import MPI_Cluster


class SelectMPIForm(forms.Form):
    attachments = MultiFileField(min_num=1, label="Input Files",
                                 help_text="Upload all files to be used including .conf file (if any)")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('user')
        super(SelectMPIForm, self).__init__(*args, **kwargs)
        # self.fields['mpi_cluster'].queryset = MPI_Cluster.objects.filter(creator=self.user)
        current_user_as_creator = Q(creator=self.user)
        cluster_is_public = Q(shared_to_public=True)
        supports_gamess = Q(supported_tools="gamess")
        # is_ready = Q(status=1)
        q = MPI_Cluster.objects.filter(current_user_as_creator | cluster_is_public)
        q = q.filter(supports_gamess).exclude(status=4) #exclude unusable clusters

        self.fields['mpi_cluster'] = forms.ModelChoiceField(queryset=q)

        self.helper = FormHelper()
        self.helper.form_tag = False
        # self.helper.form_id = 'id-rayForm'
        # self.helper.form_class = 'use-tool-forms'
        # self.helper.form_method = 'post'
        self.helper.form_action = ''
        self.helper.layout = Layout(    #crispy_forms layout

            Div(
                Field('mpi_cluster', wrapper_class='col-xs-4'),
                css_class="col-sm-12"
            ),
            Div(
                Field('attachments', wrapper_class='col-xs-6'),
                css_class="col-sm-12"
            ),

        )




class InputParameterForm(forms.Form):
    PARAMETER_CHOICES = (   #input parameter args
                        ('-p','-p'),
                        ('-i','-i'),
                        ('-s','-s'),
    )
    parameter = forms.ChoiceField(choices=PARAMETER_CHOICES)
    avg_outer_distance = forms.DecimalField(label="Average outer distance", required=False, help_text="Optional.",
                                            min_value=0)
    std_deviation = forms.DecimalField(label="Standard deviation", required=False, help_text="Optional.", min_value=0)

    INITIAL_CHOICES = (('', '---------'),)
    input_file1 = forms.ChoiceField(label="Input file 1", required=False, choices=INITIAL_CHOICES)
    # widget=forms.Select(attrs={'class': 'file-select'}))
    input_file2 = forms.ChoiceField(label="Input file 2", required=False, choices=INITIAL_CHOICES)

    # widget=forms.Select(attrs={'class': 'file-select'}))

    def __init__(self, *args, **kwargs):
        super(InputParameterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.disable_csrf = True
        self.helper.form_tag = False  # remove form headers
        # self.helper.form_id = 'id-rayForm'
        # self.helper.form_class = 'use-tool-forms'
        # self.helper.form_method = 'post'

        self.helper.form_action = ''

        self.helper.layout = Layout(  # layout using crispy_forms
            Div(
                Div('parameter', css_class='col-xs-1'),
                Div('avg_outer_distance', css_class='col-xs-2'),
                Div('std_deviation', css_class='col-xs-2'),

                Div('input_file1', css_class='col-xs-3'),
                Div('input_file2', css_class='col-xs-3'),

                css_class='row-fluid col-sm-12 form-container'
            ),
        )

    def clean(self):
        if self.cleaned_data:
            parameter = self.cleaned_data['parameter']

            input_file1 = self.cleaned_data['input_file1']
            input_file2 = self.cleaned_data['input_file2']

            print parameter, input_file1

            if parameter == '-p':  # -p needs two input files
                print "Goes inside parameter -p"

                if not input_file1:
                    print "None1"
                    raise forms.ValidationError(
                        '-p parameter requires two input files',
                        code='-p_incomplete_input_files'
                    )
                else:
                    print "M1"

                if not input_file2:
                    print "None2"
                else:
                    print "M2"

                if not input_file1 or not input_file2:
                    raise forms.ValidationError(
                        '-p parameter requires two input files',
                        code='-p_incomplete_input_files'
                    )

            elif parameter == '-i' or parameter == '-s':  # -i and -s needs one input file
                if not input_file1:
                    raise forms.ValidationError(
                        '%s parameter requires one input file' % parameter,
                        code='%s_incomplete_input_files' % parameter
                    )
