import json
import os.path

from django.forms import formset_factory
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from skylab.models import MPI_Cluster, ToolActivity, SkyLabFile

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


            # based on intial environment variables config on quantum espresso
            para_prefix = "mpiexec -n %s " % cluster_size
            para_postfix = "-nk 1 -nd 1 -nb 1 -nt 1 "

            para_image_prefix = "mpiexec -n 4"
            param_image_postfix = "-ni 2 %s" % para_postfix


            tool_activity = ToolActivity.objects.create(
                mpi_cluster=cluster_name, tool_name="quantum espresso", executable_name="quantum espresso",
                user=self.request.user,
                # command_list=json.dumps(command_list)
            )

            # build command list
            command_list = []
            for form in input_formset:
                executable = form.cleaned_data.get('param_executable')
                if executable:  # ignore blank parameter value

                    input_file = form.cleaned_data["param_input_file"]
                    filepath1 = create_input_skylab_file(tool_activity, 'input', input_file)

                    # neb.x -inp filename.in
                    # ph.x can be run using images #not supported

                    if executable == "neb.x":
                        command_list.append(
                            "%s %s %s -inp %s > %s.out" % (para_prefix, executable, para_postfix, input_file.name,
                                                           os.path.splitext(input_file.name)[0]))
                    else:
                        command_list.append("%s %s %s < %s > %s.out" % (
                        para_prefix, executable, para_postfix, input_file.name, os.path.splitext(input_file.name)[0]))

            # check pseudopotentials

            tool_activity.command_list = json.dumps(command_list)
            tool_activity.save()

            print tool_activity.command_list

            # data = {
            #     "actions": "use_tool",
            #     "activity": tool_activity.id,
            #     "tool": tool_activity.tool_name,
            #     "param_executable": tool_activity.executable_name,
            # }
            # message = json.dumps(data)
            # print message
            # # find a way to know if thread is already running
            # send_mpi_message("skylab.consumer.%d" % tool_activity.mpi_cluster.id, message)
            # tool_activity.status = "Task Queued"

            return redirect("../task/%d" % tool_activity.id)
        else:
            return render(request, 'modules/quantum espresso/use_quantum_espresso.html', {
                'select_mpi_form': select_mpi_form,
                'input_formset': input_formset,
            })
            # todo fetch: ontologyterms.txt from http://geneontology.org/ontology/obo_format_1_2/gene_ontology_ext.obo for -gene-ontology
