from django.forms import formset_factory
from django.shortcuts import render
from django.views.generic import TemplateView

from skylab.modules.ray.forms import InputParameterForm, SelectMPIForm


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

    # todo: implement post function
    def post(self, request, *args, **kwargs):
        select_mpi_form = SelectMPIForm(request.POST)
        item_forms = self.input_formset(request.POST, request.FILES)

        if select_mpi_form.is_valid() and item_forms.is_valid():
            # do something with the cleaned_data on the formsets.
            # print select_mpi_form.cleaned_data.get('mpi_cluster')
            pass

        return render(request, 'modules/ray/use_ray.html', {
            'select_mpi_form': select_mpi_form,
            'item_forms': item_forms,
        })

    # item_forms = input_formset()

    # def get_form_kwargs(self):
    #     # pass "user" keyword argument with the current user to your form
    #     kwargs = super(GamessView, self).get_form_kwargs()
    #     kwargs['user'] = self.request.user
    #     return kwargs
