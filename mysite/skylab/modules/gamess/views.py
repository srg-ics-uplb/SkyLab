from __future__ import print_function
from __future__ import print_function
from __future__ import print_function

import json
import os

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView

from skylab.models import Task, SkyLabFile, Tool
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
        cluster = form.cleaned_data['mpi_cluster']
        task = Task.objects.create(
            mpi_cluster=cluster, tool=Tool.objects.get(display_name="GAMESS"), user=self.request.user,
            command_list=""
        )
        command_list = []
        for f in form.cleaned_data['input_files']:
            SkyLabFile.objects.create(type=1, upload_path="task_{0}/input".format(task.id),
                                      file=f,
                                      filename=f.name, task=task)

            filename_without_ext = os.path.splitext(f.name)[0]
            command_list.append("rungms {0} 01 1 2>&1 | tee {0}.log".format(filename_without_ext))

        task.refresh_from_db()
        task.command_list = json.dumps(command_list)
        task.save()
        task.change_status(status_code=100, status_msg="Task initialized")
        # Create log file stating task is initialized

        self.kwargs['id'] = task.id
        return super(GAMESSView, self).form_valid(form)
