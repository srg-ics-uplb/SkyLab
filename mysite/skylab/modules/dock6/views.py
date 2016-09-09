from __future__ import print_function
from __future__ import print_function

import json
import os.path

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView

from skylab.models import ToolActivity
from skylab.modules.base_tool import create_input_skylab_file
from skylab.modules.base_tool import send_mpi_message
from skylab.modules.dock6.forms import DockForm, GridForm


class DockFormView(LoginRequiredMixin, FormView):
    template_name = "modules/dock6/use_dock6.html"
    form_class = DockForm

    def get_form_kwargs(self):
        # pass "user" keyword argument with the current user to your form
        kwargs = super(DockFormView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return "../task/%d" % self.kwargs['id']

    def form_valid(self, form):
        cluster = form.cleaned_data['mpi_cluster']

        exec_string = "mpirun -np 4 dock6.mpi "
        tool_activity = ToolActivity.objects.create(
            mpi_cluster=cluster, tool_name="dock6", executable_name="dock6", user=self.request.user,
            exec_string=exec_string
        )
        self.kwargs['id'] = tool_activity.id

        cluster = form.cleaned_data['mpi_cluster']

        input_file = form.cleaned_data['param_input_file']
        create_input_skylab_file(tool_activity, 'input', input_file)
        exec_string += "-i %s " % input_file.name

        for file in form.cleaned_data['param_other_files']:
            create_input_skylab_file(tool_activity, 'input', file)

        if form.cleaned_data.get('param_output_prefix'):
            exec_string += "-o ../output/%s.out " % form.cleaned_data['param_output_prefix']
        else:
            exec_string += "-o ../output/%s.out " % os.path.splitext(input_file.name)[0]

        tool_activity.exec_string = exec_string
        tool_activity.save()

        # todo: access toolname and param_executable name from database
        data = {
            "actions": "use_tool",
            "activity": tool_activity.id,
            "tool": tool_activity.tool_name,
            "param_executable": "dock6",
        }
        message = json.dumps(data)
        print(message)
        # find a way to know if thread is already running
        send_mpi_message("skylab.consumer.%d" % tool_activity.mpi_cluster.id, message)
        # mpi_cluster.status = "Task Queued"

        return super(DockFormView, self).form_valid(form)


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
        tool_activity = ToolActivity.objects.create(
            mpi_cluster=cluster, tool_name="dock6", executable_name="grid", user=self.request.user,
            exec_string=exec_string
        )
        self.kwargs['id'] = tool_activity.id

        input_file = form.cleaned_data['param_input_file']
        create_input_skylab_file(tool_activity, 'input', input_file)
        exec_string += "-i %s " % input_file.name

        for file in form.cleaned_data['param_other_files']:
            create_input_skylab_file(tool_activity, 'input', file)

        if form.cleaned_data.get('param_output_prefix'):
            exec_string += "-o ../output/%s.out " % form.cleaned_data['param_output_prefix']
        else:
            exec_string += "-o ../output/%s.out " % os.path.splitext(input_file.name)[0]

        if form.cleaned_data['param_terse']:
            exec_string += "-t "

        if form.cleaned_data['param_verbose']:
            exec_string += "-v "

        tool_activity.exec_string = exec_string
        tool_activity.save()

        # todo: access toolname and param_executable name from database
        data = {
            "actions": "use_tool",
            "activity": tool_activity.id,
            "tool": tool_activity.tool_name,
            "param_executable": "grid",
        }
        message = json.dumps(data)
        print(message)
        # find a way to know if thread is already running
        send_mpi_message("skylab.consumer.%d" % tool_activity.mpi_cluster.id, message)
        tool_activity.status = "Task Queued"

        return super(GridFormView, self).form_valid(form)
