from __future__ import print_function

from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import formset_factory
from django.shortcuts import render, redirect
from django.views.generic import FormView

from skylab.modules.impi.forms import InputParameterForm, SelectMPIFilesForm


class ImpiView(LoginRequiredMixin, FormView):
    template_name = "modules/impi/use_impi.html"
    input_formset = formset_factory(InputParameterForm, min_num=1, extra=0, max_num=10, validate_max=True,
                                    validate_min=False, can_delete=True)
    input_forms = input_formset()
    form_class = SelectMPIFilesForm

    def get_form_kwargs(self):
        # pass "user" keyword argument with the current user to your form
        kwargs = super(ImpiView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(ImpiView, self).get_context_data(**kwargs)
        # context['select_mpi_form'] = SelectMPIFilesForm()
        context['input_formset'] = self.input_forms
        return context

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        select_mpi_form = self.get_form(form_class)
        input_formset = self.input_formset(request.POST, request.FILES)

        if select_mpi_form.is_valid() and input_formset.is_valid():
            pass
            # todo: implement task creation
            for input_form in input_formset:
                operation = input_form.cleaned_data.get('param_operation')
                if operation:
                    if operation == '3' or operation == '4':
                        print('Check value')
                    else:
                        print("Don't check value")
            return redirect('task_detail_view', pk=0)
        else:
            return render(request, 'modules/impi/use_impi.html', {
                'form': select_mpi_form,
                'input_formset': input_formset,
            })
