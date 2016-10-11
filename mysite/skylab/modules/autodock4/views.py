import json
import os.path

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView

from skylab.models import Task, SkyLabFile, Tool
from skylab.modules.autodock4.forms import AutodockForm, AutogridForm


class AutodockView(LoginRequiredMixin, FormView):
    template_name = "modules/autodock/use_autodock.html"
    form_class = AutodockForm

    def get_form_kwargs(self):
        # pass "user" keyword argument with the current user to your form
        kwargs = super(AutodockView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return "../task/%d" % self.kwargs['id']

    def form_valid(self, form):
        cluster = form.cleaned_data['mpi_cluster']


        exec_string = "autodock4 "
        task = Task.objects.create(
            mpi_cluster=cluster, tool=Tool.objects.get(display_name='AutoDock 4'), user=self.request.user
        )
        self.kwargs['id'] = task.id

        SkyLabFile.objects.bulk_create([
            SkyLabFile(type=1, file=form.cleaned_data['param_receptor_file'], task=task),
            SkyLabFile(type=1, file=form.cleaned_data['param_ligand_file'], task=task),
            SkyLabFile(type=1, file=form.cleaned_data['param_dpf_file'], task=task),
        ])

        for grid_file in form.cleaned_data['param_grid_files']:
            SkyLabFile.objects.create(type=1, file=grid_file, task=task)

        exec_string += "-p %s " % form.cleaned_data['param_dpf_file'].name

        if form.cleaned_data.get('param_dlg_filename'):
            exec_string += "-l ../output/%s.dlg " % (form.cleaned_data['param_dlg_filename'])
        else:
            exec_string += "-l ../output/%s.dlg " % os.path.splitext(form.cleaned_data['param_dpf_file'].name)[0]

        if form.cleaned_data['param_k']:
            exec_string += "-k "

        if form.cleaned_data['param_i']:
            exec_string += "-i "

        if form.cleaned_data['param_t']:
            exec_string += "-t "

        if form.cleaned_data['param_d']:
            exec_string += "-d "

        exec_string += ";"

        task.task_data = json.dumps({'command_list': [exec_string]})
        task.save()

        # find a way to know if thread is already running
        return super(AutodockView, self).form_valid(form)


class AutogridView(LoginRequiredMixin, FormView):
    template_name = "modules/autodock/use_autogrid.html"
    form_class = AutogridForm

    def get_form_kwargs(self):
        # pass "user" keyword argument with the current user to your form
        kwargs = super(AutogridView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return "../toolactivity/%d" % self.kwargs['id']

    def form_valid(self, form):
        cluster = form.cleaned_data['mpi_cluster']
        receptor_file = form.cleaned_data['param_receptor_file']

        exec_string = "autogrid4 "
        task = Task.objects.create(
            mpi_cluster=cluster, tool=Tool.objects.get(display_name='AutoGrid 4'), user=self.request.user
        )

        self.kwargs['id'] = task.id

        SkyLabFile.objects.bulk_create([
            SkyLabFile(type=1, file=form.cleaned_data['param_gpf_file'], task=task),
            SkyLabFile(type=1, file=form.cleaned_data['param_receptor_file'], task=task),
            SkyLabFile(type=1, file=form.cleaned_data['param_ligand_file'], task=task)
        ])


        exec_string += "-p %s " % form.cleaned_data['param_gpf_file'].name

        if form.cleaned_data.get('param_glg_filename'):
            exec_string += "-l ../output/%s.glg " % (form.cleaned_data['param_glg_filename'])
        else:
            exec_string += "-l ../output/%s.glg " % os.path.splitext(form.cleaned_data['param_gpf_file'].name)[0]

        if form.cleaned_data['param_d']:
            exec_string += "-d "
        exec_string += "; "

        if form.cleaned_data['param_use_with_autodock']:
            SkyLabFile.objects.create(type=1, file=form.cleaned_data['param_dpf_file'], task=task)
            exec_string += "autodock4 -p %s " % form.cleaned_data['param_dpf_file'].name

            if form.cleaned_data.get('param_dlg_filename'):
                exec_string += "-l ../output/%s.dlg " % (form.cleaned_data['param_dlg_filename'])
            else:
                exec_string += "-l ../output/%s.dlg " % os.path.splitext(form.cleaned_data['param_dpf_file'].name)[0]

            if form.cleaned_data['param_k']:
                exec_string += "-k "

            if form.cleaned_data['param_i']:
                exec_string += "-i "

            if form.cleaned_data['param_t']:
                exec_string += "-t "

            if form.cleaned_data['param_d_dock']:
                exec_string += "-d "

            exec_string += ";"

            task.task_data = json.dumps({'command_list': [exec_string]})
            task.save()

        return super(AutogridView, self).form_valid(form)
