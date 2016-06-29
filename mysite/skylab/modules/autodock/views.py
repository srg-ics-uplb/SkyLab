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
        pass


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
        pass
