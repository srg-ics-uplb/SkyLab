from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML
from django import forms
from django.conf import settings
from django.core.validators import RegexValidator

from skylab.models import MPICluster, ToolSet
from skylab.validators import cluster_name_unique_validator


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

# def send_mpi_message(routing_key, body):
# 	connection = pika.BlockingConnection(pika.ConnectionParameters(
# 		host='localhost'))
#
# 	channel = connection.channel()
#
# 	channel.exchange_declare(exchange='topic_logs',
# 							 type='topic')
#
# 	# routing_key = 'skylab.msg'
#
# 	channel.basic_publish(exchange='topic_logs',
# 						  routing_key=routing_key,
# 						  body=body,
# 						  properties=pika.BasicProperties(
# 							  delivery_mode=2,  # make message persistent
# 						  ))
#
# 	print(" [x] Sent %r:%r" % (routing_key, "body:%r" %body))
# 	connection.close()

def get_current_max_nodes():
	online_clusters = MPICluster.objects.exclude(status=5)
	current_instance_count = 0
	for c in online_clusters:
		current_instance_count += c.cluster_size + 1

	return min(settings.MAX_NODES_PER_CLUSTER, settings.MAX_TOTAL_INSTANCES - current_instance_count)


class CreateMPIForm(forms.Form):
	cluster_name_validator = RegexValidator(r'^\w+$',
											'Must start with a letter. Only alphanumeric characters and _ are allowed.')
	cluster_name = forms.CharField(label="Cluster name", max_length=50,
								   validators=[cluster_name_validator, cluster_name_unique_validator],
								   help_text='This is required to be unique. e.g. chem_205_gamess_12_12345')
	cluster_size = forms.IntegerField(label="Cluster size", min_value=1, max_value=get_current_max_nodes())
	toolsets = forms.ModelMultipleChoiceField(label="Toolsets", queryset=ToolSet.objects.all(),
											  help_text="Select toolsets to be activated")
	is_public = forms.BooleanField(label="Share to public")

	def __init__(self, *args, **kwargs):
		super(CreateMPIForm, self).__init__(*args, **kwargs)

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

# class Create_MPI_Cluster_Form(forms.ModelForm):
# 	class Meta:
# 		model = MPICluster
# 		fields = ['cluster_name', 'cluster_size', "supported_toolsets", "is_public"]  # 'supported_tools'
#
# 	# widgets = {'cluster_size' : forms.NumberInput()}
#
# 	def __init__(self, *args, **kwargs):
# 		self.user = kwargs.pop('user')
# 		super(Create_MPI_Cluster_Form, self).__init__(*args, **kwargs)
#
# 		self.helper = FormHelper()
# 		self.helper.form_id = 'id-mpiForm'
# 		self.helper.form_class = 'create-mpi-cluster-form'
# 		self.helper.form_method = 'post'
# 		self.helper.form_action = ''
# 		self.helper.layout = Layout(
#
# 			'cluster_name',
# 			'cluster_size',
# 			'supported_toolsets',
# 			'is_public',
# 			HTML('<input name="submit" value="Execute" type="submit" class="btn btn-primary btn-block">')
#
# 		)
#
# 	def save(self):
# 		result = super(Create_MPI_Cluster_Form, self).save(commit=False)
# 		result.creator = self.user
# 		result.save()
# 		for t in result.activated_toolset.all():
# 			print t.display_name
# 		data = {
# 			"actions"	:	"create_cluster",
# 			"pk"			:	result.id,
# 			"cluster_name"	:	result.cluster_name,
# 			"cluster_size"	:	result.cluster_size,
# 			# "tools"			:	result.supported_tools
# 		}
# 		message = json.dumps(data)
# 		print message
# 		# find a way to know if thread is already running
# 		# send_mpi_message("skylab.mpi.create", message)
# 		# time.sleep(10)
# 		return result

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
