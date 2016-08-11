import os

import pika
from django.conf import settings
from django.http import HttpResponse
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from sendfile import sendfile
from django_ajax.decorators import ajax

from forms import Create_MPI_Cluster_Form
from skylab.models import ToolActivity


def has_read_permission(request, path):
	# TODO: query if user in toolactivity
	"Only show to authenticated users - extend this as desired"

	return request.user.is_authenticated()


def serve_private_file(request, path, filename):
	"Simple example of a view to serve private files with xsendfile"
	if has_read_permission(request, path):
		fullpath = os.path.join(settings.PRIVATE_MEDIA_ROOT, path)

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
	success_url = 'create_mpi_cluster'

	def test(self):
		self.render_to_response()

	def get_form_kwargs(self):
		# pass "user" keyword argument with the current user to your form
		kwargs = super(CreateMPIView, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs

class ToolActivityDetail(DetailView):
	model = ToolActivity
	template_name = 'tool_activity_detail.html'

	# def get_context_data(self, **kwargs):
	# 	context = super(ToolActivityDetail,self).get_context_data(**kwargs)
	# 	logs = Logs.objects.
	# 	return context

	def get_queryset(self):
		qs = super(ToolActivityDetail, self).get_queryset()
		return qs.filter(user=self.request.user)

def index(request):
	return HttpResponse("Hello, world. You're at the skylab index.")


@ajax
def task_fragments_view(request, pk=None):
	print pk
	if pk is not None:
		task = ToolActivity.objects.filter(pk=pk, user=request.user.id)[0]
		print task.id

		if task.status_code == 0 or task.status_code == 1:
			progress_bar = '<div class="progress progress-striped active"><div class="progress-bar" role="progressbar" aria-valuenow="100" aria-valuemin="0"aria-valuemax="100" style="width: 100%"></div></div>'
		elif task.status_code == 2:
			progress_bar = '<div class="progress-bar progress-bar-success" role="progressbar" aria-valuenow="100"aria-valuemin="0" aria-valuemax="100" style="width:100%"></div>'
		elif task.status_code == 3:
			progress_bar = '<div class="progress-bar progress-bar-danger" role="progressbar" aria-valuenow="100"aria-valuemin="0" aria-valuemax="100" style="width:100%"></div>'
		# progress_bar

		data = {
			'inner-fragments': {
				'#task-output-files-list': '<li>replace element with this content1</li>',
				'#progress-bar-container': progress_bar,
				'#task-status': task.status,
			},
			'status_code': task.status_code

		}
		return data
