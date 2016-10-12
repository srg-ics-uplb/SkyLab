import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import Http404
from django.http import HttpResponse
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django_ajax.decorators import ajax
from sendfile import sendfile

from forms import CreateMPIForm
from skylab.models import Task, MPICluster, ToolActivation, SkyLabFile


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
def serve_skylabfile(request, task_id, type, filename):
	try:
		if type == "input":
			requested_file = SkyLabFile.objects.get(type=1, task_id=task_id, filename=filename)
		elif type == "output":
			requested_file = SkyLabFile.objects.get(type=2, task_id=task_id, filename=filename)
	except ObjectDoesNotExist:

		return Http404

	fullpath = os.path.join(settings.MEDIA_ROOT, requested_file.file.name)

	return sendfile(request, fullpath, attachment=True)


# if has_read_permission(request, task_id):
# 	return sendfile(request, file.file.url, attachment=True)
# else:  # if user fails test return 403
# 	return HttpResponseForbidden()

# def send_mpi_message(routing_key, body):
# 	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
#
# 	channel = connection.channel()
#
# 	channel.exchange_declare(exchange='topic_logs',
# 							 type='topic')
#
# 	channel.confirm_delivery()
#
# 	channel.basic_publish(exchange='topic_logs',
# 						  routing_key=routing_key,
# 						  body=body,
# 						  properties=pika.BasicProperties(
# 							  delivery_mode=2,  # make message persistent
# 						  ))
#
# 	print(" [x] Sent %r:%r" % (routing_key, "body:%r" % body))
# 	connection.close()


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

		mpi_cluster.allowed_users.add(self.request.user)
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
def refresh_nav_task_list(request):
	tasks = Task.objects.filter(user=request.user.id).order_by('-updated')[:3]
	list_items = []
	if tasks:
		task_item_template = '<li><a href="{task_url}"><div><p><strong>Task {task_id} <small>({tool_name})</small></strong><span class="pull-right text-{progress_bar_type}">{task_status_msg}</span></p><div class="progress progress-striped {active}"><div class="progress-bar progress-bar-{progress_bar_type}" role="progressbar" aria-valuenow="{task_completion_rate}aria-valuemin="0" aria-valuemax="100" style="width: {task_completion_rate}%"><span class="sr-only">{task_status_msg}</span></div></div></div></a></li>'
		for task in tasks:  # build <li class="divider"></li>.join(list_items)
			task_id = task.id
			task_url = reverse('task_detail_view', kwargs={'pk': task_id})
			tool_name = 'Quantum Espresso'  # task.tool.display_name
			task_completion_rate = task.completion_rate
			active = 'active' if task_completion_rate < 100 else ''
			latest_log = task.latest_log
			task_status_msg = task.get_simple_status_msg(latest_log.status_code)

			if latest_log.status_code < 200:
				progress_bar_type = 'info'
			elif task.latest_log.status_code / 100 == 2:
				progress_bar_type = 'success'
			elif task.latest_log.status_code >= 400:
				progress_bar_type = 'danger'
			else:
				progress_bar_type = 'warning'

			list_items.append(task_item_template.format(tool_name=tool_name, task_id=task_id, task_url=task_url,
														task_completion_rate=task_completion_rate,
														task_status_msg=task_status_msg, active=active,
														progress_bar_type=progress_bar_type))

		list_items.append(  # link to task list view
			'<li><a class="text-center" href="#"><strong>See All Tasks</strong><i class="fa fa-angle-right"></i></a></li>')
	else:
		list_items.append('<li><div><p class="text-center text-muted">No tasks created</p></div></li>')

	data = {
		'inner-fragments': {
			'#nav-task-list': '<li class="divider"></li>'.join(list_items)
		}
	}

	return data


@login_required
@ajax
def refresh_task_detail_view(request, pk=None):
	if pk is not None:
		task = Task.objects.get(pk=pk, user=request.user.id)
		# print task.id
		# print "Status code", task.latest_log.status_code

		task_output_file_list = ''
		for item in task.get_output_files_urls():
			task_output_file_list += '<a class="list-group-item" href="%s">%s</a>' % (
				item.get("url"), item.get("filename"))

		if task.latest_log.status_code < 200:
			progress_bar = '<div id="task-view-progress-bar" class="progress progress-striped active"><div class="progress-bar" role="progressbar" aria-valuenow="100" aria-valuemin="0"aria-valuemax="100" style="width: 100%"></div></div>'
			status_msg = '<span id="task-status" class="text-info pull-right">' + task.get_simple_status_msg(
				task.latest_log.status_code) + '</span>'
		elif task.latest_log.status_code == 200:
			progress_bar = '<div id="task-view-progress-bar" class="progress progress-striped"><div class="progress-bar progress-bar-success" role="progressbar" aria-valuenow="100"aria-valuemin="0" aria-valuemax="100" style="width:100%"></div></div>'
			status_msg = '<span id="task-status" class="text-success pull-right">' + task.get_simple_status_msg(
				task.latest_log.status_code) + '</span>'
		elif task.latest_log.status_code >= 400:
			progress_bar = '<div id="task-view-progress-bar" class="progress progress-striped"><div class="progress-bar progress-bar-danger" role="progressbar" aria-valuenow="100"aria-valuemin="0" aria-valuemax="100" style="width:100%"></div></div>'
			status_msg = '<span id="task-status" class="text-danger pull-right">' + task.get_simple_status_msg(
				task.latest_log.status_code) + '</span>'
		# progress_bar

		data = {
			'inner-fragments': {
				'#task-output-files-list': task_output_file_list,
			},
			'fragments': {
				'#task-view-progress-bar': progress_bar,
				'#task-status': status_msg,
			},
			'status_code': task.latest_log.status_code,
			'progress': progress_bar,
			# 'has_jsmol_file': task.has_jsmol_file,
			'uri_dict': task.get_dict_jsmol_files_uris(request),

		}
		return data
