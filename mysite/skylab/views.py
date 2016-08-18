import os

import pika
import json
from django.conf import settings
from django.http import HttpResponse, response
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from sendfile import sendfile
from django_ajax.decorators import ajax

from forms import Create_MPI_Cluster_Form
from skylab.models import ToolActivity
from django.http import HttpResponseForbidden, Http404


def has_read_permission(request, task_id):
	# TODO: query if user in toolactivity
	"Only show to authenticated users - extend this as desired"
	if ToolActivity.objects.get(pk=task_id).user_id == request.user.id:
		return True
	else:
		return False


# def display_private_file_content(request, path, filename):
# 	if has_read_permission(request, path):
# 		fullpath = os.path.join(settings.PRIVATE_MEDIA_ROOT, path)
# 		print fullpath
# 		file = open(fullpath, 'r')
# 		response = file.read()
# 		print response
# 		file.close()
# 		return HttpResponse(response.replace('\n', '<br>'))

@login_required
def serve_private_file(request, task_id, type, filename):
	try:
		task = ToolActivity.objects.get(pk=task_id)

		if type == "input":
			file = task.input_files.get(filename__exact=filename)
		elif type == "output":
			file = task.output_files.get(filename__exact=filename)
	except ObjectDoesNotExist:
		return Http404

	if has_read_permission(request, task_id):
		fullpath = os.path.join(settings.PRIVATE_MEDIA_ROOT,
								"%s/%s" % (file.upload_path, filename))
		print fullpath
		return sendfile(request, fullpath, attachment=True)
	else:  # if user fails test return 403
		return HttpResponseForbidden()


def serve_file_for_jsmol(request, task_id, type, filename):
	try:
		task = ToolActivity.objects.get(pk=task_id)

		if type == "input":
			file = task.input_files.get(filename__exact=filename)
		elif type == "output":
			file = task.output_files.get(filename__exact=filename)

		fullpath = os.path.join(settings.PRIVATE_MEDIA_ROOT, "%s/%s" % (file.upload_path, filename))
		print fullpath
		return sendfile(request, fullpath, attachment=True)

	except ObjectDoesNotExist:
		return Http404

def send_mpi_message(routing_key, body):
	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))

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


class CreateMPIView(LoginRequiredMixin, CreateView):
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


class ToolActivityDetail(LoginRequiredMixin, DetailView):
	model = ToolActivity
	template_name = 'jsmol_test_detail.html'

	def get_context_data(self, **kwargs):
		context = super(ToolActivityDetail, self).get_context_data(**kwargs)
		# print context.keys()

		# jsmol_files_absolute_uris = []
		# print context["object"].id
		#
		# output_files = context["object"].output_files.filter(render_with_jsmol=True)
		# for file in output_files:
		# 	jsmol_files_absolute_uris.append(
		# 		{"uri": self.request.build_absolute_uri(reverse('jsmol_file_url',
		# 														kwargs={"task_id": context["object"].id,
		# 																"type": "output", "filename": file.filename})),
		# 		 "filename": file.filename}
		# 	)
		#
		# input_files = context["object"].input_files.filter(render_with_jsmol=True)
		# for file in input_files:
		# 	jsmol_files_absolute_uris.append(
		# 		{"uri" : self.request.build_absolute_uri(reverse('jsmol_file_url', kwargs={"task_id": context["object"].id, "type": "input", "filename": file.filename})),
		# 		 "filename" : file.filename}
		# 	)

		context["jsmol_files_absolute_uris"] = context["object"].get_dict_jsmol_files_uris(self.request)
		context["jsmol_server_url"] = settings.JSMOL_SERVER_URL
		return context

	def get_queryset(self):
		qs = super(ToolActivityDetail, self).get_queryset()
		return qs.filter(user=self.request.user)

def index(request):
	return HttpResponse("Hello, world. You're at the skylab index.")


@login_required
@ajax
def task_fragments_view(request, pk=None):
	print pk
	if pk is not None:
		task = ToolActivity.objects.filter(pk=pk, user=request.user.id)[0]
		print task.id
		print "Status code", task.latest_log.status_code
		if task.latest_log.status_code < 200:
			progress_bar = '<div class="progress progress-striped active"><div class="progress-bar" role="progressbar" aria-valuenow="100" aria-valuemin="0"aria-valuemax="100" style="width: 100%"></div></div>'
		elif task.latest_log.status_code == 200:
			progress_bar = '<div class="progress progress-striped"><div class="progress-bar progress-bar-success" role="progressbar" aria-valuenow="100"aria-valuemin="0" aria-valuemax="100" style="width:100%"></div></div>'
		elif task.latest_log.status_code >= 400:
			progress_bar = '<div class="progress progress-striped"><div class="progress-bar progress-bar-danger" role="progressbar" aria-valuenow="100"aria-valuemin="0" aria-valuemax="100" style="width:100%"></div></div>'
		# progress_bar

		data = {
			'inner-fragments': {
				'#task-output-files-list': '<li>replace element with this content1</li>',
				'#task-status': task.latest_log.status_msg,
			},
			'fragments': {
				'#progress': progress_bar,
			},
			'status_code': task.latest_log.status_code,
			# 'has_jsmol_file': task.has_jsmol_file,
			'uri_dict': task.get_dict_jsmol_files_uris(request),

		}
		return data
