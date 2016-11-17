from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, HTML, Field
from django import forms
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.models import Q
from multiupload.fields import MultiFileField

from skylab.forms import MPIModelChoiceField, get_mpi_queryset_for_task_submission
from skylab.models import MPICluster, ToolSet


def validate_gamess_input_extension(files):
    for f in files:
        if not f.name.endswith('.inp'):
            raise ValidationError(u'Only (.inp) files are accepted')


class GamessForm(forms.Form):
    input_files = MultiFileField(validators=[validate_gamess_input_extension], label="Input file(s)", help_text="File type: (.inp)")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(GamessForm, self).__init__(*args, **kwargs)

        toolset = ToolSet.objects.get(p2ctool_name="gamess")

        self.fields['mpi_cluster'] = MPIModelChoiceField(queryset=get_mpi_queryset_for_task_submission(self.user), label="MPI Cluster",
                                                         toolset=toolset,
                                                         help_text="Getting an empty list? Try <a href='{0}'>creating an MPI Cluster</a> first.".format(
                                                             reverse('create_mpi')))

        self.helper = FormHelper()
        self.helper.form_id = 'id-impiForm'
        self.helper.form_class = 'use-tool-forms'
        self.helper.form_method = 'post'
        self.helper.form_action = ''
        self.helper.layout = Layout(
                Field('mpi_cluster', wrapper_class="col-xs-12"),
                Field('input_files', wrapper_class="col-xs-12"),
                HTML('<input name="submit" value="Submit task" type="submit" class="btn btn-primary btn-block">')
        )
