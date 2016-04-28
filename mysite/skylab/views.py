import json

import pika
from django.http import HttpResponse
from django.views.generic import FormView
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView

from forms import Create_MPI_Cluster_Form, Use_Gamess_Form
from skylab.models import ToolActivity, SkyLabFile, MPI_Cluster


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

class HomeView(TemplateView):
	template_name = "home.html"

class CreateMPIView(CreateView):
	template_name = 'create_mpi_cluster.html'
	form_class = Create_MPI_Cluster_Form
	success_url = 'create-mpi-cluster'

	def get_form_kwargs(self):
		# pass "user" keyword argument with the current user to your form
		kwargs = super(CreateMPIView, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs

class Use_Gamess_View(FormView):
	template_name = "use_gamess.html"
	form_class = Use_Gamess_Form
	success_url = "use-gamess"

	def get_form_kwargs(self):
		# pass "user" keyword argument with the current user to your form
		kwargs = super(Use_Gamess_View, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs

	def form_valid(self, form):
		cluster = MPI_Cluster.objects.get(pk=self.request.POST['mpi_cluster'])
		print cluster
		tool_activity = ToolActivity.objects.create(
			mpi_cluster=cluster, tool_name="gamess", user=self.request.user
		)
		new_file = SkyLabFile.objects.create(file=self.request.FILES['inp_file'])
		tool_activity.input_files.add(new_file)
		print self.request.FILES['inp_file'].name

		data = {
			"actions"	:	"use_tool",
			"activity"			:	tool_activity.id,
			"tool"			:	tool_activity.tool_name
		}
		message = json.dumps(data)
		print message
		# find a way to know if thread is already running
		send_mpi_message("skylab.consumer.%d" % tool_activity.mpi_cluster.id, message)
		return super(Use_Gamess_View, self).form_valid(form)

def index(request):
	return HttpResponse("Hello, world. You're at the skylab index.")
