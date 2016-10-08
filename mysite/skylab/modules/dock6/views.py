from __future__ import print_function
from __future__ import print_function

import os.path

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView

from skylab.models import Task, SkyLabFile
from skylab.modules.dock6.forms import Dock6Form, GridForm


class Dock6FormView(LoginRequiredMixin, FormView):
    template_name = "modules/dock6/use_dock6.html"
    form_class = Dock6Form

    def get_form_kwargs(self):
        # pass "user" keyword argument with the current user to your form
        kwargs = super(Dock6FormView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return "../task/%d" % self.kwargs['id']

    def form_valid(self, form):
        cluster = form.cleaned_data['mpi_cluster']

        exec_string = "mpirun -np 4 dock6.mpi "
        task = Task.objects.create(
            mpi_cluster=cluster, tool_name="dock6", executable_name="dock6", user=self.request.user,
            exec_string=exec_string
        )
        self.kwargs['id'] = task.id

        cluster = form.cleaned_data['mpi_cluster']

        input_file = form.cleaned_data['param_input_file']
        SkyLabFile.objects.create(type=1, file=input_file, task=task)

        exec_string += "-i %s " % input_file.name

        for f in form.cleaned_data['param_other_files']:
            SkyLabFile.objects.create(type=1, file=f, task=task)

        if form.cleaned_data.get('param_output_prefix'):
            exec_string += "-o ../output/%s.out " % form.cleaned_data['param_output_prefix']
        else:
            exec_string += "-o ../output/%s.out " % os.path.splitext(input_file.name)[0]

        task.exec_string = exec_string
        task.save()

        return super(Dock6FormView, self).form_valid(form)


class GridFormView(LoginRequiredMixin, FormView):
    template_name = "modules/dock6/use_grid.html"
    form_class = GridForm

    def get_form_kwargs(self):
        # pass "user" keyword argument with the current user to your form
        kwargs = super(GridFormView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return "../toolactivity/%d" % self.kwargs['id']

    def form_valid(self, form):
        cluster = form.cleaned_data['mpi_cluster']

        exec_string = "grid "
        task = Task.objects.create(
            mpi_cluster=cluster, tool_name="dock6", executable_name="grid", user=self.request.user,
            exec_string=exec_string
        )
        self.kwargs['id'] = task.id

        input_file = form.cleaned_data['param_input_file']
        SkyLabFile.objects.create(type=1, file=input_file, task=task)

        exec_string += "-i %s " % input_file.name

        for f in form.cleaned_data['param_other_files']:
            SkyLabFile.objects.create(type=1, file=f, task=task)


        if form.cleaned_data.get('param_output_prefix'):
            exec_string += "-o ../output/%s.out " % form.cleaned_data['param_output_prefix']
        else:
            exec_string += "-o ../output/%s.out " % os.path.splitext(input_file.name)[0]

        if form.cleaned_data['param_terse']:
            exec_string += "-t "

        if form.cleaned_data['param_verbose']:
            exec_string += "-v "

        task.exec_string = exec_string
        task.save()

        return super(GridFormView, self).form_valid(form)
