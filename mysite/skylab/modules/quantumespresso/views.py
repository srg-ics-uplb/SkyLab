from __future__ import print_function

import json
import os.path

from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import formset_factory
from django.shortcuts import render, redirect
from django.views.generic import FormView

from skylab.models import MPICluster, Task, SkyLabFile
from skylab.modules.quantumespresso.forms import InputParameterForm, SelectMPIFilesForm


class QuantumEspressoView(LoginRequiredMixin, FormView):
    template_name = "modules/quantum espresso/use_quantum_espresso.html"
    input_formset = formset_factory(InputParameterForm, min_num=1, extra=0, max_num=10, validate_max=True,
                                    validate_min=False, can_delete=True)
    input_forms = input_formset()
    form_class = SelectMPIFilesForm

    def get_form_kwargs(self):
        # pass "user" keyword argument with the current user to your form
        kwargs = super(QuantumEspressoView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(QuantumEspressoView, self).get_context_data(**kwargs)
        context['input_formset'] = self.input_forms

        context['user'] = self.request.user
        return context

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        select_mpi_form = self.get_form(form_class)
        input_formset = self.input_formset(request.POST, request.FILES)

        if select_mpi_form.is_valid() and input_formset.is_valid():
            # do something with the cleaned_data on the formsets.
            # print select_mpi_form.cleaned_data.get('mpi_cluster')
            cluster_name = select_mpi_form.cleaned_data['mpi_cluster']

            cluster_size = MPICluster.objects.get(cluster_name=cluster_name).cluster_size

            # -n cluster_size


            # based on intial environment variables config on quantum espresso
            para_prefix = 'mpiexec -n {0} '.format(cluster_size)
            para_postfix = "-nk 1 -nd 1 -nb 1 -nt 1 "

            # copied from espresso's default env var value
            para_image_prefix = "mpiexec -n 4"
            param_image_postfix = '-ni 2 {0}'.format(para_postfix)

            task = Task.objects.create(
                mpi_cluster=cluster_name, tool_name="quantum espresso", executable_name="quantum espresso",
                user=self.request.user,
                # additional_info=
                # task_data=json.dumps(task_data)
            )

            # build command list
            command_list = []
            task_data = json.loads(select_mpi_form.cleaned_data['param_pseudopotentials'])
            scf_output_files = []
            for form in input_formset:
                executable = form.cleaned_data.get('param_executable')
                if executable:  # ignore blank parameter value

                    input_file = form.cleaned_data["param_input_file"]
                    # filepath = create_input_skylab_file(task, 'input', input_file)
                    instance = SkyLabFile.objects.create(type=1, file=input_file, task=task)
                    # filepath = instance.file.name
                    if executable == "pw.x":
                        pass

                    # TODO: parse input file and check if calculation is not found or calculation = 'scf'
                    # if True:  scf_output_files.append(os.path.splitext(input_file.name)[0])


                    # neb.x -inp filename.in
                    # ph.x can be run using images #not supported

                    if executable == "neb.x":
                        command_list.append(
                            '{0} {1} {2} -inp input/{3} > output/{4}.out'.format(para_prefix, executable, para_postfix,
                                                                                 input_file.name,
                                                                                 os.path.splitext(input_file.name)[0]))

                    else:
                        command_list.append('{0} {1} {2} < input/{3} > output/{4}.out'.format(
                        para_prefix, executable, para_postfix, input_file.name, os.path.splitext(input_file.name)[0]))

            task_data['scf_output_files'] = scf_output_files
            task_data['command_list'] = command_list
            task.task_data = json.dumps(task_data)
            task.save()

            print(task.task_data)

            # data = {
            #     "actions": "use_tool",
            #     "activity": mpi_cluster.id,
            #     "tool": mpi_cluster.tool_name,
            #     "param_executable": mpi_cluster.executable_name,
            # }
            # message = json.dumps(data)
            # print message
            # # find a way to know if thread is already running
            # send_mpi_message("skylab.consumer.%d" % mpi_cluster.mpi_cluster.id, message)
            # mpi_cluster.status = "Task Queued"


            return redirect('task_detail_view', pk=task.id)
        else:
            return render(request, 'modules/quantum espresso/use_quantum_espresso.html', {
                'select_mpi_form': select_mpi_form,
                'input_formset': input_formset,
            })
            # todo fetch: ontologyterms.txt from http://geneontology.org/ontology/obo_format_1_2/gene_ontology_ext.obo for -gene-ontology
