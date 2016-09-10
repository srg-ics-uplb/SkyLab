from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit
from django import forms
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.models import Q

from skylab.models import MPI_Cluster
from skylab.modules.base_tool import MPIModelChoiceField


def validate_gamess_input_extension(value):
    if not value.name.endswith('.inp'):
        raise ValidationError(u'Only (.inp) files are accepted')


class GamessForm(forms.Form):
    inp_file = forms.FileField(validators=[validate_gamess_input_extension], label="Input file")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(GamessForm, self).__init__(*args, **kwargs)
        # self.fields['mpi_cluster'].queryset = MPI_Cluster.objects.filter(creator=self.user)
        current_user_as_creator = Q(creator=self.user)
        cluster_is_public = Q(shared_to_public=True)
        supports_gamess = Q(supported_tools="gamess")
        # is_ready = Q(status=1)
        q = MPI_Cluster.objects.filter(current_user_as_creator | cluster_is_public)
        q = q.filter(supports_gamess).exclude(status=4)

        self.fields['mpi_cluster'] = MPIModelChoiceField(queryset=q, label="MPI Cluster",
                                                         help_text="Getting an empty list? Try <a href='{0}'>creating an MPI Cluster</a> first.".format(
                                                             reverse('create_mpi')))

        self.helper = FormHelper()
        self.helper.form_id = 'id-impiForm'
        self.helper.form_class = 'use-tool-forms'
        self.helper.form_method = 'post'
        self.helper.form_action = ''
        self.helper.layout = Layout(
            Fieldset(
                'Use Gamess',
                'mpi_cluster',
                'inp_file',
            ),
            Submit('submit', 'Execute')
        )
