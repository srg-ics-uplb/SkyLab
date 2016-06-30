from django.views.generic import TemplateView, FormView
from skylab.modules.autodock.forms import AutodockForm, AutogridForm
from django import forms
from django.shortcuts import render, redirect
from skylab.models import MPI_Cluster, ToolActivity, SkyLabFile
from skylab.modules.base_tool import send_mpi_message, create_skylab_file
import os.path
import json
from django.utils.text import get_valid_filename
from skylab.modules.base_tool import create_skylab_file


class AutodockView(FormView):
    template_name = "modules/autodock/use_autodock.html"
    form_class = AutodockForm

    def get_form_kwargs(self):
        # pass "user" keyword argument with the current user to your form
        kwargs = super(AutodockView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return "../toolactivity/%d" % self.kwargs['id']

    def form_valid(self, form):
        cluster = form.cleaned_data['mpi_cluster']
        receptor_file = form.cleaned_data['param_receptor_file']

        exec_string = "autodock4 "
        tool_activity = ToolActivity.objects.create(
            mpi_cluster=cluster, tool_name="autodock", executable_name="autodock", user=self.request.user,
            exec_string=exec_string
        )
        self.kwargs['id'] = tool_activity.id

        create_skylab_file(tool_activity, 'input', form.cleaned_data['param_receptor_file'])
        create_skylab_file(tool_activity, 'input', form.cleaned_data['param_ligand_file'])
        create_skylab_file(tool_activity, 'input', form.cleaned_data['param_dpf_file'])

        exec_string += "-p workdir/%s" % form.cleaned_data['param_dpf_file'].name

        if form.cleaned_data.get('param_dlg_filename'):
            exec_string += "-l output/%s.dlg " % get_valid_filename(form.cleaned_data['param_dlg_filename'])
        else:
            exec_string += "-l output/%s.dlg " % os.path.splitext(form.cleaned_data['param_dpf_file'].name)[0]

        if form.cleaned_data['param_k']:
            exec_string += "-k "

        if form.cleaned_data['param_i']:
            exec_string += "-i "

        if form.cleaned_data['param_t']:
            exec_string += "-t "

        if form.cleaned_data['param_d']:
            exec_string += "-d "

        exec_string += ";"


        return super(AutodockView, self).form_valid(form)



class AutogridView(FormView):
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
        tool_activity = ToolActivity.objects.create(
            mpi_cluster=cluster, tool_name="autodock", executable_name="autodock", user=self.request.user,
            exec_string=exec_string
        )
        self.kwargs['id'] = tool_activity.id

        create_skylab_file(tool_activity, 'input', form.cleaned_data['param_gpf_file'])
        create_skylab_file(tool_activity, 'input', form.cleaned_data['param_receptor_file'])
        create_skylab_file(tool_activity, 'input', form.cleaned_data['param_ligand_file'])

        exec_string += "-p workdir/%s " % form.cleaned_data['param_gpf_file'].name

        if form.cleaned_data.get('param_glg_filename'):
            exec_string += "-l output/%s.glg " % get_valid_filename(form.cleaned_data['param_glg_filename'])
        else:
            exec_string += "-l output/%s.glg " % os.path.splitext(form.cleaned_data['param_gpf_file'].name)[0]

        if form.cleaned_data['param_d']:
            exec_string += "-d "
        exec_string += "; "

        if form.cleaned['param_use_with_autodock']:
            create_skylab_file(tool_activity, 'input', form.cleaned_data['param_dpf_file'])

            exec_string += "-p workdir/%s" % form.cleaned_data['param_dpf_file'].name

            if form.cleaned_data.get('param_dlg_filename'):
                exec_string += "-l output/%s.dlg " % get_valid_filename(form.cleaned_data['param_dlg_filename'])
            else:
                exec_string += "-l output/%s.dlg " % os.path.splitext(form.cleaned_data['param_dpf_file'].name)[0]

            if form.cleaned_data['param_k']:
                exec_string += "-k "

            if form.cleaned_data['param_i']:
                exec_string += "-i "

            if form.cleaned_data['param_t']:
                exec_string += "-t "

            if form.cleaned_data['param_d_dock']:
                exec_string += "-d "

            exec_string += ";"

        return super(AutogridView, self).form_valid(form)
