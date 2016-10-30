from __future__ import print_function

import json
import os

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import reverse
from django.views.generic import FormView

from skylab.models import Task, SkyLabFile, Tool
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
        return reverse('task_detail_view', kwargs={'pk': self.kwargs.pop('id')})

    def form_valid(self, form):
        cluster = form.cleaned_data['mpi_cluster']
        tool = Tool.objects.get(display_name="GAMESS")
        task = Task.objects.create(
            mpi_cluster=cluster, tool=tool, user=self.request.user
        )
        command_list = []
        for f in form.cleaned_data['input_files']:
            SkyLabFile.objects.create(type=1, file=f, task=task)

            filename_without_ext = os.path.splitext(f.name)[0]
            command = "rungms {0} 01 1 2>&1 | tee ../output/{0}.log".format(filename_without_ext)
            command_list.append(command)

        task.refresh_from_db()
        task.task_data = json.dumps({'command_list': command_list})
        task.save()

        self.kwargs['id'] = task.id
        return super(GamessView, self).form_valid(form)
