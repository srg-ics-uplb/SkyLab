import os

import pika
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.http import HttpResponseForbidden, Http404
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django_ajax.decorators import ajax
from sendfile import sendfile

from forms import CreateMPIForm
from skylab.models import Task, MPICluster, ToolActivation


def has_read_permission(request, task_id):
	# TODO: query if user in toolactivity
	"Only show to authenticated users - extend this as desired"
	if Task.objects.get(pk=task_id).user_id == request.user.id:
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
		task = Task.objects.get(pk=task_id)

		if type == "input":
			file = task.input_files.get(filename__exact=filename)
		elif type == "output":
			file = task.output_files.get(filename__exact=filename)
	except ObjectDoesNotExist:
		return Http404

	if has_read_permission(request, task_id):
		fullpath = os.path.join(settings.PRIVATE_MEDIA_ROOT,
								"{0}/{1}".format(file.upload_path, filename))
		print (fullpath)
		return sendfile(request, fullpath, attachment=True)
	else:  # if user fails test return 403
		return HttpResponseForbidden()


def serve_file_for_jsmol(request, task_id, type, filename):
	try:
		task = Task.objects.get(pk=task_id)

		if type == "input":
			file = task.input_files.get(filename__exact=filename)
		elif type == "output":
			file = task.output_files.get(filename__exact=filename)

		fullpath = os.path.join(settings.PRIVATE_MEDIA_ROOT, "{0}/{1}".format(file.upload_path, filename))
		print (fullpath)
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


class CreateMPIView(LoginRequiredMixin, FormView):
	template_name = 'create_mpi_cluster.html'
	form_class = CreateMPIForm

	# TODO: change success url (-> my mpi cluster view)
	success_url = 'create-mpi-cluster'

	# def get_form_kwargs(self):
	# 	# pass "user" keyword argument with the current user to your form
	# 	kwargs = super(CreateMPIView, self).get_form_kwargs()
	# 	kwargs['user'] = self.request.user
	# 	return kwargs

	def form_valid(self, form):
		mpi_cluster = MPICluster.objects.create(creator=self.request.user,
												cluster_name=form.cleaned_data['cluster_name'],
												cluster_size=form.cleaned_data['cluster_size'],
												is_public=form.cleaned_data['is_public'])

		mpi_cluster.allowed_users.add(self.user)
		mpi_cluster.save()


		for t in form.cleaned_data['toolsets']:
			ToolActivation.objects.create(toolset=t, mpi_cluster=mpi_cluster, activated=False)

		return super(CreateMPIView, self).form_valid(form)


# class CreateMPIView(LoginRequiredMixin, CreateView):
# 	template_name = 'create_mpi_cluster.html'
# 	form_class = Create_MPI_Cluster_Form
#
# 	# TODO: change success url (-> my mpi cluster view)
# 	success_url = 'create-mpi-cluster'
#
# 	def get_form_kwargs(self):
# 		# pass "user" keyword argument with the current user to your form
# 		kwargs = super(CreateMPIView, self).get_form_kwargs()
# 		kwargs['user'] = self.request.user
# 		return kwargs


class ToolActivityDetail(LoginRequiredMixin, DetailView):
	model = Task
	template_name = 'task_detail_view.html'

	def get_context_data(self, **kwargs):
		context = super(ToolActivityDetail, self).get_context_data(**kwargs)
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
	if pk is not None:
		task = Task.objects.filter(pk=pk, user=request.user.id)[0]
		# print task.id
		# print "Status code", task.latest_log.status_code

		task_output_file_list = ''
		for item in task.get_output_files_urls():
			task_output_file_list += '<a class="list-group-item" href="%s">%s</a>' % (
			item.get("url"), item.get("filename"))

		if task.latest_log.status_code < 200:
			progress_bar = '<div class="progress progress-striped active"><div class="progress-bar" role="progressbar" aria-valuenow="100" aria-valuemin="0"aria-valuemax="100" style="width: 100%"></div></div>'
			status_msg = '<span id="task-status" class="text-info pull-right">' + task.latest_log.status_msg + '</span>'
		elif task.latest_log.status_code == 200:
			progress_bar = '<div class="progress progress-striped"><div class="progress-bar progress-bar-success" role="progressbar" aria-valuenow="100"aria-valuemin="0" aria-valuemax="100" style="width:100%"></div></div>'
			status_msg = '<span id="task-status" class="text-success pull-right">' + task.latest_log.status_msg + '</span>'
		elif task.latest_log.status_code >= 400:
			progress_bar = '<div class="progress progress-striped"><div class="progress-bar progress-bar-danger" role="progressbar" aria-valuenow="100"aria-valuemin="0" aria-valuemax="100" style="width:100%"></div></div>'
			status_msg = '<span id="task-status" class="text-danger pull-right">' + task.latest_log.status_msg + '</span>'
		# progress_bar

		data = {
			'inner-fragments': {
				'#task-output-files-list': task_output_file_list,
			},
			'fragments': {
				'#progress': progress_bar,
				'#task-status': status_msg,
			},
			'status_code': task.latest_log.status_code,

			# 'has_jsmol_file': task.has_jsmol_file,
			'uri_dict': task.get_dict_jsmol_files_uris(request),

		}
		return data
