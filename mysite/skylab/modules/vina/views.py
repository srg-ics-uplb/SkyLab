from django.views.generic import TemplateView, FormView
from skylab.modules.vina.forms import VinaForm
from django import forms
from django.shortcuts import render, redirect
from skylab.models import MPI_Cluster, ToolActivity, SkyLabFile
from skylab.modules.base_tool import send_mpi_message, create_skylab_file


class VinaView(TemplateView):
    template_name = "modules/vina/use_vina.html"

    def get_context_data(self, **kwargs):
        context = super(VinaView, self).get_context_data(**kwargs)
        context['vina_form'] = VinaForm()
        context['user'] = self.request.user
        return context

    def post(self, request, *args, **kwargs):
        vina_form = VinaForm(request.POST, request.FILES)

        if vina_form.is_valid():
            cluster_name = vina_form.cleaned_data['mpi_cluster']

            exec_string = "vina "
            tool_activity = ToolActivity.objects.create(
                mpi_cluster=cluster_name, tool_name="vina", user=self.request.user, exec_string=exec_string
            )

            receptor_file = vina_form.cleaned_data['param_receptor']
            create_skylab_file(tool_activity, '', receptor_file)

            pass
            # return redirect("../toolactivity/%d" % tool_activity.id)
        else:
            return render(request, 'modules/vina/use_vina.html', {
                'vina_form': vina_form,

            })


class VinaSplitView(FormView):
    pass
