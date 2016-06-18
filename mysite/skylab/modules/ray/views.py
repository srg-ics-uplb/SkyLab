from django.forms import formset_factory
from django.shortcuts import render
from django.views.generic import TemplateView

from skylab.modules.ray.forms import InputParameterForm, SelectMPIFilesForm, OtherParameterForm


class RayView(TemplateView):
    template_name = "modules/ray/use_ray.html"
    input_formset = formset_factory(InputParameterForm, min_num=1, extra=0, max_num=10, validate_max=True,
                                    validate_min=False, can_delete=True)
    input_forms = input_formset()


    def get_context_data(self, **kwargs):
        context = super(RayView, self).get_context_data(**kwargs)
        context['select_mpi_form'] = SelectMPIFilesForm()
        context['input_formset'] = self.input_forms
        context['other_parameter_form'] = OtherParameterForm()
        context['user'] = self.request.user
        return context

    def post(self, request, *args, **kwargs):
        select_mpi_form = SelectMPIFilesForm(request.POST)
        input_formset = self.input_formset(request.POST, request.FILES)
        other_parameter_form = OtherParameterForm(request.POST, request.FILES)

        if select_mpi_form.is_valid() and other_parameter_form.is_valid() and input_formset.is_valid():
            # do something with the cleaned_data on the formsets.
            # print select_mpi_form.cleaned_data.get('mpi_cluster')
            for form in input_formset:
                # print form.cleaned_data.get('parameter')
                # todo: -n = size of chosen cluster
                # todo: ignore paramter == ''
                # todo fetch: ontologyterms.txt from http://geneontology.org/ontology/obo_format_1_2/gene_ontology_ext.obo for -gene-ontology
                # TODO: generate exec_string here
                pass

        return render(request, 'modules/ray/use_ray.html', {
            'select_mpi_form': select_mpi_form,
            'other_parameter_form': other_parameter_form,
            'input_formset': input_formset,
        })


