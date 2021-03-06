import json
import os.path

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import reverse
from django.views.generic import FormView

from skylab.models import Task, SkyLabFile, Tool
from skylab.modules.dock6.forms import Dock6Form, GridForm
from skylab.signals import send_to_queue


class Dock6View(LoginRequiredMixin, FormView):
    template_name = "modules/dock6/use_dock6.html"
    form_class = Dock6Form

    def get_form_kwargs(self):
        # pass "user" keyword argument with the current user to your form
        kwargs = super(Dock6View, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(Dock6View, self).get_context_data(**kwargs)
        context['tool'] = Tool.objects.get(simple_name='dock6')  # pass tool to view context
        return context

    def get_success_url(self):
        return reverse('task_detail_view', kwargs={'pk': self.kwargs.pop('id')})

    def form_valid(self, form):
        # build command strings, create skylabfile for file inputs
        cluster = form.cleaned_data['mpi_cluster']
        tool = Tool.objects.get(simple_name='dock6')

        # -n cluster_size
        command = "mpirun -np {0:d} -f {1:s} dock6.mpi ".format(cluster.total_node_count, settings.MPIEXEC_NODES_FILE)

        # command = "mpiexec -np 4 dock6.mpi "
        task = Task.objects.create(
            mpi_cluster=cluster, tool=tool, user=self.request.user
        )
        self.kwargs['id'] = task.id

        cluster = form.cleaned_data['mpi_cluster']

        input_file = form.cleaned_data['param_input_file']
        SkyLabFile.objects.create(type=1, file=input_file, task=task)

        command += u"-i {0:s} ".format(input_file.name)

        for f in form.cleaned_data['param_other_files']:
            SkyLabFile.objects.create(type=1, file=f, task=task)

        if form.cleaned_data.get('param_output_prefix'):
            command += u"-o ../output/{0:s}.out ".format(form.cleaned_data['param_output_prefix'])
        else:
            command += u"-o ../output/{0:s}.out ".format(os.path.splitext(input_file.name)[0])

        task.task_data = json.dumps({'command_list': [command]})
        task.save()
        send_to_queue(task=task)  # send signal to queue this task to task queue

        return super(Dock6View, self).form_valid(form)


class GridView(LoginRequiredMixin, FormView):
    template_name = "modules/dock6/use_grid.html"
    form_class = GridForm

    def get_form_kwargs(self):
        # pass "user" keyword argument with the current user to your form
        kwargs = super(GridView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(GridView, self).get_context_data(**kwargs)
        context['tool'] = Tool.objects.get(simple_name='grid')  # pass tool to view context
        return context

    def get_success_url(self):
        return reverse('task_detail_view', kwargs={'pk': self.kwargs.pop('id')})

    def form_valid(self, form):
        # build command strings, create skylabfile for file inputs

        cluster = form.cleaned_data['mpi_cluster']
        tool = Tool.objects.get(simple_name='grid')
        command = "grid "
        task = Task.objects.create(
            mpi_cluster=cluster, tool=tool, user=self.request.user,

        )
        self.kwargs['id'] = task.id

        input_file = form.cleaned_data['param_input_file']
        SkyLabFile.objects.create(type=1, file=input_file, task=task)

        command += "-i %s " % input_file.name

        for f in form.cleaned_data['param_other_files']:
            SkyLabFile.objects.create(type=1, file=f, task=task)


        if form.cleaned_data.get('param_output_prefix'):
            command += "-o ../output/%s.out " % form.cleaned_data['param_output_prefix']
        else:
            command += "-o ../output/%s.out " % os.path.splitext(input_file.name)[0]

        if form.cleaned_data['param_terse']:
            command += "-t "

        if form.cleaned_data['param_verbose']:
            command += "-v "

        task.task_data = json.dumps({'command_list': [command]})
        task.save()
        send_to_queue(task=task)  # send signal to queue this task to task queue
        return super(GridView, self).form_valid(form)
