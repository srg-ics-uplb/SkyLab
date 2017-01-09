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
from skylab.signals import send_to_queue


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
        context['tool'] = Tool.objects.get(simple_name='quantumespresso')  # pass tool to view context
        # context['user'] = self.request.user
        return context

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        select_mpi_form = self.get_form(form_class)
        input_formset = self.input_formset(request.POST, request.FILES)

        if select_mpi_form.is_valid() and input_formset.is_valid():
            # build command strings, create skylabfile for each file input

            cluster = select_mpi_form.cleaned_data['mpi_cluster']

            # based on intial environment variables config on quantum espresso
            para_prefix = "mpirun -np {0:d} -f {1:s} ".format(cluster.total_node_count, settings.MPIEXEC_NODES_FILE)
            para_postfix = "-nk 1 -nd 1 -nb 1 -nt 1 "

            # copied from espresso's default env var value
            para_image_prefix = "mpirun -np 4"
            param_image_postfix = '-ni 2 {0}'.format(para_postfix)

            tool = Tool.objects.get(simple_name='quantumespresso')

            task = Task.objects.create(
                mpi_cluster=cluster, tool=tool, user=self.request.user
            )
            # build command list
            command_list = []
            jsmol_output_files = []

            # in form clean pseudopotentials field returns json dict
            task_data = json.loads(select_mpi_form.cleaned_data['param_pseudopotentials'])

            #location of quantum espresso executables
            remote_bin_dir = "/mirror/espresso-5.4.0/bin"

            for form in input_formset:
                executable = form.cleaned_data.get('param_executable', None)
                input_file = form.cleaned_data.get("param_input_file", None)
                if executable and input_file:  # ignore blank parameter value
                    instance = SkyLabFile.objects.create(type=1, file=input_file, task=task)
                    # neb.x -inp filename.in
                    # ph.x can be run using images #not supported
                    output_filename = '{0}.out'.format(os.path.splitext(input_file.name)[0])

                    if executable == "neb.x":
                        command_list.append(
                            '{0} {1} {2} -inp input/{3} > output/{4}'.format(para_prefix, os.path.join(remote_bin_dir,executable),
                                                                                 para_postfix,
                                                                                 input_file.name,
                                                                                 output_filename)
                        )

                    else:  # at least for pw.x, cp.x
                        command_list.append('{0} {1} {2} < input/{3} > output/{4}'.format(
                            para_prefix, os.path.join(remote_bin_dir,executable), para_postfix, input_file.name,
                            output_filename)
                        )

                        if executable == "pw.x": #identify expected output as compatible for jsmol
                            jsmol_output_files.append(output_filename)

            task_data['command_list'] = command_list
            task_data['jsmol_output_files'] = jsmol_output_files
            task.task_data = json.dumps(task_data)
            task.save()
            send_to_queue(task=task)  # send signal to queue task to task queue

            return redirect('task_detail_view', pk=task.id)
        else:
            return render(request, 'modules/quantum espresso/use_quantum_espresso.html', {
                'form': select_mpi_form,
                'input_formset': input_formset,
                'tool':  Tool.objects.get(simple_name='quantumespresso'),
            })
