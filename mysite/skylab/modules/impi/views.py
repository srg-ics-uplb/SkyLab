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
        select_mpi_form = SelectMPIFilesForm(request.POST)
        input_formset = self.input_formset(request.POST, request.FILES)

        if select_mpi_form.is_valid() and input_formset.is_valid():
            pass

            return redirect('task_detail_view', pk=0)
        else:
            return render(request, 'modules/quantum espresso/use_quantum_espresso.html', {
                'select_mpi_form': select_mpi_form,
                'input_formset': input_formset,
            })
            # todo fetch: ontologyterms.txt from http://geneontology.org/ontology/obo_format_1_2/gene_ontology_ext.obo for -gene-ontology
