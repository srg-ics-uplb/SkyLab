from __future__ import print_function
from __future__ import print_function
from __future__ import print_function

import json
import os

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView

from skylab.models import Task, SkyLabFile, MPI_Cluster
from skylab.modules.base_tool import send_mpi_message
from skylab.modules.gamess.forms import GamessForm


class GamessView(LoginRequiredMixin, FormView):
    template_name = "modules/gamess/use_gamess.html"
    form_class = GamessForm

    def get_form_kwargs(self):
        # pass "user" keyword argument with the current user to your form
        kwargs = super(GamessView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return "task/{0}".format(self.kwargs['id'])

    def form_valid(self, form):
        cluster = MPI_Cluster.objects.get(pk=self.request.POST['mpi_cluster'])
        print(cluster)
        filename = os.path.splitext(self.request.FILES['inp_file'].name)[0]
        exec_string = "rungms {0} 01 1 2>&1 | tee {0}.log".format(filename)
        # command_list = "rungms %s 01" % (filename)
        tool_activity = Task.objects.create(
            mpi_cluster=cluster, tool_name="gamess", executable_name="gamess", user=self.request.user,
            command_list=json.dumps([exec_string])
        )

        tool_activity.change_status(status_code=100, status_msg="Task initialized")
        # Create log file stating task is initialized

        self.kwargs['id'] = tool_activity.id
        new_file = SkyLabFile.objects.create(upload_path="tool_activity_%d/input" % tool_activity.id,
                                             file=self.request.FILES['inp_file'],
                                             filename=self.request.FILES['inp_file'].name)
        tool_activity.input_files.add(new_file)

        print(self.request.FILES['inp_file'].name)

        data = {
            "actions": "use_tool",
            "activity": tool_activity.id,
            "tool": tool_activity.tool_name,
            "param_executable": "gamess",
        }
        message = json.dumps(data)
        print(message)
        # find a way to know if thread is already running
        send_mpi_message("skylab.consumer.{0}".format(tool_activity.mpi_cluster.id), message)

        # Create log file stating task is queued
        tool_activity.change_status(status_code=101, status_msg="Task queued")


        return super(GamessView, self).form_valid(form)
