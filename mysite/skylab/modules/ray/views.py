from django.forms import formset_factory
from django.shortcuts import render
from django.views.generic import TemplateView, FormView

from skylab.modules.ray.forms import InputParameterForm, SelectMPIForm, UploadForm


class RayView(TemplateView):
    template_name = "modules/ray/use_ray.html"
    input_formset = formset_factory(InputParameterForm, max_num=10, validate_max=True, can_delete=True)
    input_forms = input_formset()


    def get_context_data(self, **kwargs):
        context = super(RayView, self).get_context_data(**kwargs)
        context['select_mpi_form'] = SelectMPIForm()
        context['input_formset'] = self.input_forms
        context['user'] = self.request.user
        return context

    # todo: implement post function
    def post(self, request, *args, **kwargs):
        select_mpi_form = SelectMPIForm(request.POST)
        input_formset = self.input_formset(request.POST, request.FILES)

        if select_mpi_form.is_valid() and input_formset.is_valid():
            # do something with the cleaned_data on the formsets.
            # print select_mpi_form.cleaned_data.get('mpi_cluster')
            for form in input_formset:
                print form.cleaned_data.get('parameter')
            pass

        return render(request, 'modules/ray/use_ray.html', {
            'select_mpi_form': select_mpi_form,
            'input_formset': input_formset,
        })


class UploadView(FormView):
    template_name = 'modules/ray/upload_files.html'
    form_class = UploadForm
    success_url = 'use_ray'

    # def form_valid(self, form):
    #     pass
