import json
import os

import pika
from django.views.generic import TemplateView

from django.forms import formset_factory

from skylab.models import ToolActivity, SkyLabFile, MPI_Cluster
from skylab.modules.ray.forms import InputParameterForm, SelectMPIForm
from skylab.modules.base_tool import send_mpi_message

class RayView(TemplateView):
    template_name = "modules/ray/use_ray.html"
    input_formset = formset_factory(InputParameterForm, max_num=10, validate_max=True, can_delete=True)
    item_forms = input_formset()


    def get_context_data(self, **kwargs):
        context = super(RayView, self).get_context_data(**kwargs)
        context['select_mpi_form'] = SelectMPIForm()
        context['item_forms'] = self.item_forms
        context['user'] = self.request.user
        return context
    # item_forms = input_formset()

    # def get_form_kwargs(self):
    #     # pass "user" keyword argument with the current user to your form
    #     kwargs = super(GamessView, self).get_form_kwargs()
    #     kwargs['user'] = self.request.user
    #     return kwargs
