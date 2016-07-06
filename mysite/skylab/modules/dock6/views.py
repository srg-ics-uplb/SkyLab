from django.views.generic import TemplateView, FormView
from skylab.modules.dock6.forms import DockForm, GridForm
from django import forms
from django.shortcuts import render, redirect
from skylab.models import MPI_Cluster, ToolActivity, SkyLabFile
from skylab.modules.base_tool import send_mpi_message, create_input_skylab_file
import os.path
import json
from django.utils.text import get_valid_filename
from skylab.modules.base_tool import create_input_skylab_file


class DockFormView(FormView):
    template_name = "modules/dock6/use_dock6.html"
    form_class = DockForm

    def get_form_kwargs(self):
        # pass "user" keyword argument with the current user to your form
        kwargs = super(DockFormView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return "../toolactivity/%d" % self.kwargs['id']

    def form_valid(self, form):
        pass


class GridFormView(FormView):
    template_name = "modules/dock6/use_dock6.html"
    form_class = GridForm

    def get_form_kwargs(self):
        # pass "user" keyword argument with the current user to your form
        kwargs = super(GridFormView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return "../toolactivity/%d" % self.kwargs['id']

    def form_valid(self, form):
        pass
