from __future__ import print_function
from __future__ import print_function
from __future__ import print_function
from __future__ import print_function

import json
import os.path

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.utils.text import get_valid_filename
from django.views.generic import TemplateView, FormView

from skylab.models import Task, SkyLabFile
from skylab.modules.basetool import send_mpi_message
from skylab.modules.vina.forms import VinaForm, VinaSplitForm


class VinaView(LoginRequiredMixin, TemplateView):
    template_name = "modules/vina/use_vina.html"

    def get_context_data(self, **kwargs):
        context = super(VinaView, self).get_context_data(**kwargs)
        context['vina_form'] = VinaForm()
        context['user'] = self.request.user
        return context

    def post(self, request, *args, **kwargs):
        vina_form = VinaForm(request.POST, request.FILES)

        if vina_form.is_valid():
            cluster_name = vina_form.cleaned_data['mpi_cluster']

            exec_string_template = "mkdir -p %s; vina "
            task = Task.objects.create(
                mpi_cluster=cluster_name, tool_name="vina", executable_name="vina", user=self.request.user,
                exec_string=exec_string_template
            )

            # receptor_filepath = create_input_skylab_file(tool_activity, 'input',
            #                                              vina_form.cleaned_data['param_receptor'])
            instance = SkyLabFile.objects.create(type=1, file=vina_form.cleaned_data['param_receptor'], task=task)
            receptor_filepath = instance.file.name
            exec_string_template += "--receptor %s " % receptor_filepath

            if vina_form.cleaned_data.get('param_flex'):
                # flex_filepath = create_input_skylab_file(task, 'input', vina_form.cleaned_data['param_flex'])
                instance = SkyLabFile.objects.create(type=1, file=vina_form.cleaned_data['param_flex'], task=task)
                flex_filepath = instance.file.name
                exec_string_template += "--flex %s " % flex_filepath

            exec_string_template += "--ligand %s --out %s/out.pdbqt --log %s/log.txt "

            if vina_form.cleaned_data['param_score_only']:  # search space not required
                exec_string_template += "--score_only "
            else:  # search space required
                center_x = vina_form.cleaned_data['param_center_x']
                center_y = vina_form.cleaned_data['param_center_y']
                center_z = vina_form.cleaned_data['param_center_z']
                size_x = vina_form.cleaned_data['param_size_x']
                size_y = vina_form.cleaned_data['param_size_y']
                size_z = vina_form.cleaned_data['param_size_z']

                exec_string_template += "--center_x %s --center_y %s --center_z %s --size_x %s --size_y %s --size_z %s " % (
                center_x, center_y, center_z, size_x, size_y, size_z)

            if vina_form.cleaned_data.get('param_seed'):
                exec_string_template += "--seed %s " % vina_form.cleaned_data['param_seed']

            if vina_form.cleaned_data.get('param_exhaustiveness'):
                exec_string_template += "--exhaustiveness %s " % vina_form.cleaned_data['param_exhaustiveness']

            if vina_form.cleaned_data.get('param_num_modes'):
                exec_string_template += "--num_modes %s " % vina_form.cleaned_data['param_num_modes']

            if vina_form.cleaned_data.get('param_energy_range'):
                exec_string_template += "--energy_range %s " % vina_form.cleaned_data['param_energy_range']

            if vina_form.cleaned_data['param_local_only']:
                exec_string_template += "--local_only "

            if vina_form.cleaned_data['param_randomize_only']:
                exec_string_template += "--randomize_only "

            if vina_form.cleaned_data.get('param_weight_gauss1'):
                exec_string_template += "--weight_gauss1 %s " % vina_form.cleaned_data['param_weight_gauss1']

            if vina_form.cleaned_data.get('param_weight_gauss2'):
                exec_string_template += "--weight_gauss2 %s " % vina_form.cleaned_data['param_weight_gauss2']

            if vina_form.cleaned_data.get('param_weight_repulsion'):
                exec_string_template += "--weight_repulsion %s " % vina_form.cleaned_data['param_weight_repulsion']

            if vina_form.cleaned_data.get('param_weight_hydrophobic'):
                exec_string_template += "--weight_hydrophobic %s " % vina_form.cleaned_data['param_weight_hydrophobic']

            if vina_form.cleaned_data.get('param_weight_hydrogen'):
                exec_string_template += "--weight_hydrogen %s " % vina_form.cleaned_data['param_weight_hydrogen']

            if vina_form.cleaned_data.get('param_weight_rot'):
                exec_string_template += "--weight_rot %s " % vina_form.cleaned_data['param_weight_rot']

            exec_string_template += "; "

            # LAST
            exec_string = ""
            for f in vina_form.cleaned_data['param_ligands']:
                instance = SkyLabFile.objects.create(type=1, upload_path='input/ligands', file=f, task=task)
                filepath = instance.file.name
                # filepath = create_input_skylab_file(task, 'input/ligands', f)
                basename = os.path.splitext(f.name)[0]
                outpath = "tool_activity_%d/output/%s" % (task.id, basename)

                exec_string += exec_string_template % (outpath, filepath, outpath, outpath)

            task.exec_string = exec_string
            task.save()

            print(exec_string)
            data = {
                "actions": "use_tool",
                "activity": task.id,
                "tool": task.tool_name,
                "param_executable": "vina",
            }
            message = json.dumps(data)
            print(message)
            # find a way to know if thread is already running
            send_mpi_message("skylab.consumer.%d" % task.mpi_cluster.id, message)
            task.status = "Task Queued"

            return redirect("../toolactivity/%d" % task.id)
        else:
            return render(request, 'modules/vina/use_vina.html', {
                'vina_form': vina_form,

            })


class VinaSplitView(LoginRequiredMixin, FormView):
    template_name = "modules/vina/use_vina_split.html"
    form_class = VinaSplitForm

    def get_form_kwargs(self):
        # pass "user" keyword argument with the current user to your form
        kwargs = super(VinaSplitView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return "../task/%d" % self.kwargs['id']

    def form_valid(self, form):
        cluster = form.cleaned_data['mpi_cluster']

        input_file = form.cleaned_data['param_input']
        exec_string = "vina_split --input %s " % input_file.name

        if form.cleaned_data.get('param_ligand_prefix'):
            exec_string += "--ligand %s " % get_valid_filename(form.cleaned_data['param_ligand_prefix'])

        if form.cleaned_data.get('param_flex_prefix'):
            exec_string += "--flex %s " % get_valid_filename(form.cleaned_data['param_flex_prefix'])

        print(exec_string)

        task = Task.objects.create(
            mpi_cluster=cluster, tool_name="vina", executable_name="vina_split", user=self.request.user,
            exec_string=exec_string
        )
        self.kwargs['id'] = task.id

        SkyLabFile.objects.create(type=1, file=input_file, task=task)

        data = {
            "actions": "use_tool",
            "activity": task.id,
            "tool": task.tool_name,
            "param_executable": "vina split",
        }
        message = json.dumps(data)
        print(message)
        # find a way to know if thread is already running
        send_mpi_message("skylab.consumer.%d" % task.mpi_cluster.id, message)
        task.status = "Task Queued"
        return super(VinaSplitView, self).form_valid(form)
