from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit
from django import forms

from skylab.models import MPI_Cluster


# class MyRegistrationForm(RegistrationForm):
# 	first_name = forms.CharField(widget=forms.TextInput())
# 	last_name = forms.CharField(widget=forms.TextInput())
#
# 	def user_created(sender, user, request, **kwargs):
# 		"""
# 		Called when user registers
# 		"""
# 		form = MyRegistrationForm(request.Post)
# 		user.first_name=form.data['first_name']
# 		user.last_name=form.data['last_name']
# 		user.save()
#
# 	user_registered.connect(user_created)

class Create_MPI_Cluster_Form(forms.ModelForm):
	class Meta:
		model = MPI_Cluster
		fields = ['cluster_name','cluster_size', 'supported_tool', 'shared_to_public']

		# widgets = {'cluster_size' : forms.NumberInput()}
	def __init__(self, *args, **kwargs):
		super(Create_MPI_Cluster_Form, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_id = 'id-mpiForm'
		self.helper.form_class = 'create-mpi-cluster-form'
		self.helper.form_method = 'post'
		self.helper.form_action = ''
		self.helper.layout = Layout(
			Fieldset(
				'Create a MPI Cluster',
				'cluster_name',
				'cluster_size',
				'supported_tool',
				'shared_to_public',
			),
			Submit('submit', 'Create MPI Cluster')

		)



# class ImpiForm(forms.Form):
# 	mpi_cluster_size = forms.IntegerField(max_value=3, min_value=1)
# 	# input_file = forms.ImageField()
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



