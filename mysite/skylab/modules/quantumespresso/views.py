from django.forms import formset_factory
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from skylab.models import MPI_Cluster, ToolActivity, SkyLabFile
import json
from skylab.modules.base_tool import send_mpi_message, create_input_skylab_file

from skylab.modules.quantumespresso.forms import InputParameterForm, SelectMPIFilesForm
from django.contrib.auth.mixins import LoginRequiredMixin



class QuantumEspressoView(LoginRequiredMixin, TemplateView):
    template_name = "modules/quantum espresso/use_quantum_espresso.html"
    input_formset = formset_factory(InputParameterForm, min_num=1, extra=0, max_num=10, validate_max=True,
                                    validate_min=False, can_delete=True)
    input_forms = input_formset()

    def get_context_data(self, **kwargs):
        context = super(QuantumEspressoView, self).get_context_data(**kwargs)
        context['select_mpi_form'] = SelectMPIFilesForm()
        context['input_formset'] = self.input_forms

        context['user'] = self.request.user
        return context

    def post(self, request, *args, **kwargs):
        select_mpi_form = SelectMPIFilesForm(request.POST)
        input_formset = self.input_formset(request.POST, request.FILES)

        if select_mpi_form.is_valid() and input_formset.is_valid():
            # do something with the cleaned_data on the formsets.
            # print select_mpi_form.cleaned_data.get('mpi_cluster')
            cluster_name = select_mpi_form.cleaned_data['mpi_cluster']
            cluster_size = MPI_Cluster.objects.get(cluster_name=cluster_name).cluster_size

            # -n cluster_size
            exec_string = "mpiexec -n %s " % cluster_size

            # -bynode
            if select_mpi_form.cleaned_data['param_bynode']:
                exec_string += "-bynode "

            tool_activity = ToolActivity.objects.create(
                mpi_cluster=cluster_name, tool_name="ray", executable_name="ray", user=self.request.user,
                exec_string=exec_string
            )

            exec_string += "Ray -o tool_activity_%d/output " % tool_activity.id

            # k-mer length


            # -mini-ranks-per-rank
            if select_mpi_form.cleaned_data.get('param_mini_ranks'):
                exec_string += "-mini-ranks-per-rank %s " % select_mpi_form.cleaned_data["param_mini_ranks"]

            for form in input_formset:
                parameter = form.cleaned_data.get('parameter')
                if parameter:  # ignore blank parameter value

                    input_file1 = form.cleaned_data['input_file1']
                    filepath1 = create_input_skylab_file(tool_activity, 'input', input_file1)

                if parameter == "-p":
                    input_file2 = form.cleaned_data['input_file2']
                    filepath2 = create_input_skylab_file(tool_activity, 'input', input_file2)

                    exec_string += "%s %s %s " % (parameter, filepath1, filepath2)

                elif parameter == "-s" or parameter == "-i":
                    exec_string += "%s %s " % (parameter, filepath1)


            tool_activity.exec_string = exec_string
            tool_activity.save()

            print exec_string

            data = {
                "actions": "use_tool",
                "activity": tool_activity.id,
                "tool": tool_activity.tool_name,
                "executable": "ray",
            }
            message = json.dumps(data)
            print message
            # find a way to know if thread is already running
            send_mpi_message("skylab.consumer.%d" % tool_activity.mpi_cluster.id, message)
            tool_activity.status = "Task Queued"

            return redirect("../task/%d" % tool_activity.id)
        else:
            return render(request, 'modules/ray/use_ray.html', {
                'select_mpi_form': select_mpi_form,
                'input_formset': input_formset,
            })
            # todo fetch: ontologyterms.txt from http://geneontology.org/ontology/obo_format_1_2/gene_ontology_ext.obo for -gene-ontology
