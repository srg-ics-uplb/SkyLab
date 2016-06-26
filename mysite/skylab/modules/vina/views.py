from django.views.generic import TemplateView, FormView
from skylab.modules.vina.forms import VinaForm
from django import forms
from django.shortcuts import render, redirect


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

            pass
            # return redirect("../toolactivity/%d" % tool_activity.id)
        else:
            return render(request, 'modules/vina/use_vina.html', {
                'vina_form': vina_form,

            })


class VinaSplitView(FormView):
    pass
