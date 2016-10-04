from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML
from django import forms
from django.conf import settings
from django.core.validators import RegexValidator

from skylab.models import ToolSet
from skylab.validators import cluster_name_unique_validator, cluster_size_validator, get_current_max_nodes


class CreateMPIForm(forms.Form):
	cluster_name_validator = RegexValidator(r'^\w+$',
											'Must start with a letter. Only alphanumeric characters and _ are allowed.')
	cluster_name = forms.CharField(label="Cluster name", max_length=50,
								   validators=[cluster_name_validator, cluster_name_unique_validator],
								   help_text='This is required to be unique. e.g. chem_205_gamess_12_12345')
	cluster_size = forms.IntegerField(label="Cluster size", min_value=1, max_value=settings.MAX_NODES_PER_CLUSTER,
									  validators=[cluster_size_validator], initial=1)
	toolsets = forms.ModelMultipleChoiceField(label="Toolsets", queryset=ToolSet.objects.all(),
											  help_text="Select toolsets to be activated",
											  widget=forms.CheckboxSelectMultiple())
	is_public = forms.BooleanField(required=False, label="Share to public")

	def __init__(self, *args, **kwargs):
		super(CreateMPIForm, self).__init__(*args, **kwargs)
		self.fields['cluster_size'].widget.attrs.update({'max': get_current_max_nodes()})


		self.helper = FormHelper()
		self.helper.form_id = 'id-mpiForm'
		self.helper.form_class = 'create-mpi-cluster-form'
		self.helper.form_method = 'post'
		self.helper.form_action = ''
		self.helper.layout = Layout(

			'cluster_name',
			'cluster_size',
			'toolsets',
			'is_public',
			HTML('<input name="submit" value="Execute" type="submit" class="btn btn-primary btn-block">')

		)

# class ImpiForm(forms.Form):
# 	mpi_cluster_size = forms.IntegerField(max_value=3, min_value=1)
# 	# param_input_file = forms.ImageField()
# 	auto_destroy = forms.BooleanField()
#
# 	def __init__(self, *args, **kwargs):
# 		super(ImpiForm, self).__init__(*args, **kwargs)
# 		self.helper = FormHelper()
# 		self.helper.form_id = 'id-impiForm'
# 		self.helper.form_class = 'use-tool-forms'
# 		self.helper.form_method = 'post'
# 		self.helper.form_action = ''
#
# 		self.helper.add_input(Submit('submit','Execute'))
