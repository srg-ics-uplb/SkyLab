import json
import os.path

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.views.generic import FormView

from skylab.models import Task, SkyLabFile, Tool
from skylab.modules.autodock4.forms import Autodock4Form, Autogrid4Form


class Autodock4View(LoginRequiredMixin, FormView):
    template_name = "modules/autodock/use_autodock.html"
    form_class = Autodock4Form

    def get_form_kwargs(self):
        # pass "user" keyword argument with the current user to your form
        kwargs = super(Autodock4View, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(Autodock4View, self).get_context_data(**kwargs)
        context['tool'] = Tool.objects.get(simple_name='autodock4')
        return context

    def get_success_url(self):
        return reverse('task_detail_view', kwargs={'pk': self.kwargs.pop('id')})


    def form_valid(self, form):
        cluster = form.cleaned_data['mpi_cluster']


        exec_string = "autodock4 "
        task = Task.objects.create(
            mpi_cluster=cluster, tool=Tool.objects.get(simple_name='autodock4'), user=self.request.user
        )
        self.kwargs['id'] = task.id


        # SkyLabFile.objects.create(type=1, file=form.cleaned_data['param_receptor_file'], task=task)
        SkyLabFile.objects.create(type=1, file=form.cleaned_data['param_ligand_file'], task=task)
        SkyLabFile.objects.create(type=1, file=form.cleaned_data['param_dpf_file'], task=task)
        exec_string += "-p %s " % form.cleaned_data['param_dpf_file'].name

        for grid_file in form.cleaned_data['param_grid_files']:
            SkyLabFile.objects.create(type=1, file=grid_file, task=task)

        # if form.cleaned_data.get('param_dat_file'):
        #     SkyLabFile.objects.create(type=1, file=form.cleaned_data['param_dat_file'], task=task)

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
        return super(Autodock4View, self).form_valid(form)


class Autogrid4View(LoginRequiredMixin, FormView):
    template_name = "modules/autodock/use_autogrid.html"
    form_class = Autogrid4Form

    def get_form_kwargs(self):
        # pass "user" keyword argument with the current user to your form
        kwargs = super(Autogrid4View, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(Autogrid4View, self).get_context_data(**kwargs)
        context['tool'] = Tool.objects.get(simple_name='autogrid4')
        return context

    def get_success_url(self):
        return reverse('task_detail_view', kwargs={'pk': self.kwargs.pop('id')})

    def form_valid(self, form):
        cluster = form.cleaned_data['mpi_cluster']
        receptor_file = form.cleaned_data['param_receptor_file']

        exec_string = "autogrid4 "
        task = Task.objects.create(
            mpi_cluster=cluster, tool=Tool.objects.get(simple_name='autogrid4'), user=self.request.user
        )

        self.kwargs['id'] = task.id

        SkyLabFile.objects.create(type=1, file=form.cleaned_data['param_gpf_file'], task=task)
        SkyLabFile.objects.create(type=1, file=form.cleaned_data['param_receptor_file'], task=task)

        exec_string += "-p %s " % form.cleaned_data['param_gpf_file'].name

        if form.cleaned_data.get('param_glg_filename'):
            exec_string += "-l ../output/%s.glg " % (form.cleaned_data['param_glg_filename'])
        else:
            exec_string += "-l ../output/%s.glg " % os.path.splitext(form.cleaned_data['param_gpf_file'].name)[0]

        if form.cleaned_data['param_d']:
            exec_string += "-d "
        exec_string += "; "

        if form.cleaned_data['param_use_with_autodock']:
            SkyLabFile.objects.create(type=1, file=form.cleaned_data['param_ligand_file'], task=task)
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

        return super(Autogrid4View, self).form_valid(form)
