from __future__ import print_function
from __future__ import print_function
from __future__ import print_function

import json
import os

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView

from skylab.models import Task, SkyLabFile, MPICluster, Tool
from skylab.modules.gamess.forms import GamessForm


class GAMESSView(LoginRequiredMixin, FormView):
    template_name = "modules/gamess/use_gamess.html"
    form_class = GamessForm

    def get_form_kwargs(self):
        # pass "user" keyword argument with the current user to your form
        kwargs = super(GAMESSView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return "task/{0}".format(self.kwargs['id'])

    def form_valid(self, form):
        cluster = MPICluster.objects.get(pk=self.request.POST['mpi_cluster'])
        print(cluster)
        filename = os.path.splitext(self.request.FILES['inp_file'].name)[0]
        exec_string = "rungms {0} 01 1 2>&1 | tee {0}.log".format(filename)
        # command_list = "rungms %s 01" % (filename)
        task = Task.objects.create(
            mpi_cluster=cluster, tool=Tool.objects.get(display_name="GAMESS"), user=self.request.user,
            command_list=json.dumps([exec_string])
        )

        task.change_status(status_code=100, status_msg="Task initialized")
        # Create log file stating task is initialized

        self.kwargs['id'] = task.id
        new_file = SkyLabFile.objects.create(type=1, upload_path="tool_activity_%d/input" % task.id,
                                             file=self.request.FILES['inp_file'],
                                             filename=self.request.FILES['inp_file'].name, task=task)


        print(self.request.FILES['inp_file'].name)

        data = {
            "actions": "use_tool",
            "activity": task.id,
            "tool": task.tool.display_name,
        }
        message = json.dumps(data)
        print(message)
        # find a way to know if thread is already running
        # send_mpi_message("skylab.consumer.{0}".format(tool_activity.mpi_cluster.id), message)

        # Create log file stating task is queued
        # task.change_status(status_code=101, status_msg="Task queued")


        return super(GAMESSView, self).form_valid(form)
