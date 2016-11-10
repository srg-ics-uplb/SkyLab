from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML
from django import forms
from django.conf import settings
from django.core.validators import RegexValidator

from skylab.models import ToolSet, MPICluster, ToolActivation
from skylab.validators import cluster_name_unique_validator, cluster_size_validator, get_current_max_nodes


class CreateMPIForm(forms.Form):
	cluster_name_validator = RegexValidator(r'^[a-zA-Z]\w*$',
											'Must start with a letter. Only alphanumeric characters and _ are allowed.')
	cluster_name = forms.CharField(label="Cluster name", max_length=30, min_length=5,
								   validators=[cluster_name_validator, cluster_name_unique_validator],
								   help_text='This is required to be unique. e.g. chem_205_gamess_12_12345')
	# ./vcluster-start cluster_name cluster_size-1
	cluster_size = forms.IntegerField(label="Cluster size", min_value=2, max_value=settings.MAX_NODES_PER_CLUSTER,
									  validators=[cluster_size_validator], initial=2)
	toolsets = forms.ModelMultipleChoiceField(required=False, label="Toolsets", queryset=ToolSet.objects.all(),
											  help_text="Select toolsets to be activated. Optional",
											  widget=forms.CheckboxSelectMultiple())
	is_public = forms.BooleanField(required=False, label="Public",
								   help_text="This option makes the cluster visible to all users.")

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
			HTML('<input name="submit" value="Create cluster" type="submit" class="btn btn-primary btn-block">')

		)

	def clean_cluster_name(self):
		cluster_name = self.cleaned_data['cluster_name']
		if MPICluster.objects.exclude(status=5).filter(cluster_name=cluster_name).exists():
			raise forms.ValidationError('Cluster with the given name already exists.', code='cluster_name_exists')

		return cluster_name

# class ImpiForm(forms.Form):
# 	mpi_cluster_size = forms.IntegerField(max_value=3, min_value=1)
# 	# param_input_files = forms.ImageField()
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
class MPIModelChoiceField(forms.ModelChoiceField):
	def __init__(self, *args, **kwargs):
		self.toolset = kwargs.pop("toolset", None)
		super(MPIModelChoiceField, self).__init__(*args, **kwargs)

	def label_from_instance(self, obj):
		if self.toolset is not None:
			try:
				tool_activation = ToolActivation.objects.get(mpi_cluster=obj, toolset=self.toolset)

				if tool_activation.status == 2:
					status = "Installed"
				elif tool_activation.status == 1:
					status = "Queued for installation"
				elif tool_activation.status == 0:
					status = "Not installed"
				return "{0} (nodes : {1}, queue length: {2}) ({3} status: {4})".format(obj.cluster_name, obj.total_node_count, obj.task_queued_count,
																	self.toolset.display_name, status)
			except ToolActivation.DoesNotExist:
				return "{0} (nodes : {1}) ({2}, queue length: {3}) ".format(obj.cluster_name, obj.total_node_count,
														self.toolset.display_name, obj.task_queued_count)
		else:
			return "{0} (nodes : {1}, queue length: {2}))".format(obj.cluster_name, obj.total_node_count, obj.task_queued_count)

