from __future__ import print_function

import json
import os.path

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import formset_factory
from django.shortcuts import render, redirect
from django.views.generic import FormView

from skylab.models import Task, SkyLabFile, Tool
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
            cluster = select_mpi_form.cleaned_data['mpi_cluster']

            # based on intial environment variables config on quantum espresso
            para_prefix = "mpiexec -n {0:d} -f {1:s} ".format(cluster.total_node_count, settings.MPIEXEC_NODES_FILE)
            para_postfix = "-nk 1 -nd 1 -nb 1 -nt 1 "

            # copied from espresso's default env var value
            para_image_prefix = "mpiexec -n 4"
            param_image_postfix = '-ni 2 {0}'.format(para_postfix)

            tool = Tool.objects.get(simple_name='quantumespresso')

            task = Task.objects.create(
                mpi_cluster=cluster, tool=tool, user=self.request.user
            )
            # build command list
            command_list = []

            # in form clean pseudopotentials field returns json dict
            task_data = json.loads(select_mpi_form.cleaned_data['param_pseudopotentials'])
            # scf_output_files = []
            for form in input_formset:
                executable = form.cleaned_data.get('param_executable')
                if executable:  # ignore blank parameter value

                    input_files = form.cleaned_data.get("param_input_files", [])
                    if input_files:
                        for input_file in input_files:
                            instance = SkyLabFile.objects.create(type=1, file=input_file, task=task)

                            # if executable == "pw.x":
                            #     # TODO: parse input file and check if calculation is not found or calculation = 'scf'
                            #     pass
                            # neb.x -inp filename.in
                            # ph.x can be run using images #not supported

                            if executable == "neb.x":
                                command_list.append(
                                    '{0} {1} {2} -inp input/{3} > output/{4}.out'.format(para_prefix, executable,
                                                                                         para_postfix,
                                                                                         input_file.name,
                                                                                         os.path.splitext(
                                                                                             input_file.name)[0]))

                            else:
                                command_list.append('{0} {1} {2} < input/{3} > output/{4}.out'.format(
                                    para_prefix, executable, para_postfix, input_file.name,
                                    os.path.splitext(input_file.name)[0]))

            # task_data['scf_output_files'] = scf_output_files
            task_data['command_list'] = command_list
            task.task_data = json.dumps(task_data)
            task.save()

            print(task.task_data)

            return redirect('task_detail_view', pk=task.id)
        else:
            return render(request, 'modules/quantum espresso/use_quantum_espresso.html', {
                'form': select_mpi_form,
                'input_formset': input_formset,
            })
