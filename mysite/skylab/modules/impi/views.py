from __future__ import print_function

import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import formset_factory
from django.shortcuts import render, redirect
from django.views.generic import FormView

from skylab.models import Tool, Task, SkyLabFile
from skylab.modules.impi.forms import InputParameterForm, SelectMPIFilesForm
from skylab.signals import send_to_queue


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
        context['tool'] = Tool.objects.get(simple_name='impi')  # pass tool to view context
        context['input_formset'] = self.input_forms  # pass input formset to view context
        return context


    def post(self, request, *args, **kwargs):
        # build command, strings, create SkylabFile instances for each input file

        form_class = self.get_form_class()
        select_mpi_form = self.get_form(form_class)
        input_formset = self.input_formset(request.POST, request.FILES)


        if select_mpi_form.is_valid() and input_formset.is_valid():
            cluster = select_mpi_form.cleaned_data['mpi_cluster']
            tool = Tool.objects.get(simple_name='impi')

            command_list = []
            for input_form in input_formset:
                operation = input_form.cleaned_data.get('param_operation')
                # command = {}
                if operation:
                    # command['operation'] = operation
                    command_list.append(operation)
                    if operation == '3' or operation == '4':
                        value = input_form.cleaned_data.get('param_value')
                        command_list.append(value)
                        # command['value'] = value
                        # command_list.append(command)

            task = Task.objects.create(
                mpi_cluster=cluster, tool=tool, user=self.request.user
            )
            input_filenames = []
            for f in select_mpi_form.cleaned_data['input_files']:
                SkyLabFile.objects.create(type=1, file=f, task=task)
                input_filenames.append(f.name)

            task_data = {
                    'command_list': command_list,
                    'input_filenames': input_filenames
            }


            task.refresh_from_db()
            task.task_data = json.dumps(task_data)
            task.save()  # send signal to queue this task to task queue
            send_to_queue(task=task)

            return redirect('task_detail_view', pk=task.id)
        else:
            return render(request, 'modules/impi/use_impi.html', {
                'form': select_mpi_form,
                'input_formset': input_formset,
                'tool':Tool.objects.get(simple_name='impi'),
            })
