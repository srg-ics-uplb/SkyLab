import json

import pika
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q

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

def send_mpi_message(routing_key, body):
	connection = pika.BlockingConnection(pika.ConnectionParameters(
		host='localhost'))

	channel = connection.channel()

	channel.exchange_declare(exchange='topic_logs',
							 type='topic')

	# routing_key = 'skylab.msg'

	channel.basic_publish(exchange='topic_logs',
						  routing_key=routing_key,
						  body=body,
						  properties=pika.BasicProperties(
							  delivery_mode=2,  # make message persistent
						  ))

	print(" [x] Sent %r:%r" % (routing_key, "body:%r" %body))
	connection.close()

class Create_MPI_Cluster_Form(forms.ModelForm):
	class Meta:
		model = MPI_Cluster
		fields = ['cluster_name', 'cluster_size', 'supported_tools', 'shared_to_public']

		# widgets = {'cluster_size' : forms.NumberInput()}

	def __init__(self, *args, **kwargs):
		self.user = kwargs.pop('user')
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
				'supported_tools',
				'shared_to_public',
			),
			Submit('submit', 'Create MPI Cluster')

		)

	def save(self):
		result = super(Create_MPI_Cluster_Form, self).save(commit=False)
		result.creator = self.user
		result.save()
		data = {
			"actions"		:	"create_cluster",
			"pk"			:	result.id,
			"cluster_name"	:	result.cluster_name,
			"cluster_size"	:	result.cluster_size,
			"tools"			:	result.supported_tools
		}
		message = json.dumps(data)
		print message
		# find a way to know if thread is already running
		send_mpi_message("skylab.mpi.create", message)
		# time.sleep(10)
		return result

def validate_gamess_input_extension(value):
    if not value.name.endswith('.inp'):
        raise ValidationError(u'Only (.inp) files are accepted')

class Use_Gamess_Form(forms.Form):

	inp_file = forms.FileField(validators=[validate_gamess_input_extension], label="Input file")

	def __init__(self, *args, **kwargs):
		self.user = kwargs.pop('user')
		super(Use_Gamess_Form, self).__init__(*args, **kwargs)
		# self.fields['mpi_cluster'].queryset = MPI_Cluster.objects.filter(creator=self.user)
		current_user_as_creator = Q(creator=self.user)
		cluster_is_public = Q(shared_to_public=True)
		q = MPI_Cluster.objects.filter(current_user_as_creator | cluster_is_public)
		self.fields['mpi_cluster'] = forms.ModelChoiceField(queryset=MPI_Cluster.objects.filter(current_user_as_creator | cluster_is_public))

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



