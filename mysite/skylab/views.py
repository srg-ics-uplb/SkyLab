import os

import pika
from django.conf import settings
from django.http import HttpResponse
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from sendfile import sendfile

from forms import Create_MPI_Cluster_Form
from skylab.models import ToolActivity


def has_read_permission(request, path):
	# TODO: query if user in toolactivity
	"Only show to authenticated users - extend this as desired"

	return request.user.is_authenticated()


def serve_private_file(request, path, filename):
	"Simple example of a view to serve private files with xsendfile"
	# if has_read_permission(request, path):
	fullpath = os.path.join(settings.PRIVATE_MEDIA_ROOT, path)
	print fullpath

	print sendfile(request, fullpath, attachment=True)
	return sendfile(request, fullpath, attachment=True)

def send_mpi_message(routing_key, body):
	connection = pika.BlockingConnection(pika.ConnectionParameters(
		host='localhost'))

	channel = connection.channel()

	channel.exchange_declare(exchange='topic_logs',
							 type='topic')

	channel.confirm_delivery()

	channel.basic_publish(exchange='topic_logs',
						  routing_key=routing_key,
						  body=body,
						  properties=pika.BasicProperties(
							  delivery_mode=2,  # make message persistent
						  ))

	print(" [x] Sent %r:%r" % (routing_key, "body:%r" % body))
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

class ToolActivityDetail(DetailView):
	model = ToolActivity
	template_name = 'tool_activity_detail.html'

	def get_queryset(self):
		qs = super(ToolActivityDetail, self).get_queryset()
		return qs.filter(user=self.request.user)

def index(request):
	return HttpResponse("Hello, world. You're at the skylab index.")
