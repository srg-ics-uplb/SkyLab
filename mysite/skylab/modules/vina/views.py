import json
import os.path

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.utils.text import get_valid_filename
from django.views.generic import FormView

from skylab.models import Task, SkyLabFile, Tool
from skylab.modules.vina.forms import VinaForm, VinaSplitForm


class VinaView(LoginRequiredMixin, FormView):
    template_name = "modules/vina/use_vina.html"
    form_class = VinaForm
    
    def get_form_kwargs(self):
        # pass "user" keyword argument with the current user to your form
        kwargs = super(VinaView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_invalid(self, form):
        return render(self.request, 'modules/vina/use_vina.html', {
            'form': form,
        })

    def get_success_url(self):
        return reverse('task_detail_view', kwargs={'pk': self.kwargs['task_id']})

    def form_valid(self, form):
        cluster = form.cleaned_data['mpi_cluster']

        exec_string_template = "mkdir -p {outpath}; vina "
        tool = Tool.objects.get(display_name="Vina")
        task = Task.objects.create(
            mpi_cluster=cluster, tool=tool, user=self.request.user
        )

        # receptor_filepath = create_input_skylab_file(task, 'input',
        #                                              form.cleaned_data['param_receptor'])
        instance = SkyLabFile.objects.create(type=1, file=form.cleaned_data['param_receptor'], task=task)
        receptor_filepath = instance.file.name
        exec_string_template += "--receptor %s " % receptor_filepath

        if form.cleaned_data.get('param_flex'):
            # flex_filepath = create_input_skylab_file(task, 'input', form.cleaned_data['param_flex'])
            instance = SkyLabFile.objects.create(type=1, file=form.cleaned_data['param_flex'], task=task)
            flex_filepath = instance.file.name
            exec_string_template += "--flex %s " % flex_filepath

        exec_string_template += "--ligand {filepath} --out {outpath}/out.pdbqt --log {outpath}/log.txt "

        if form.cleaned_data['param_score_only']:  # search space not required
            exec_string_template += "--score_only "
        else:  # search space required
            center_x = form.cleaned_data['param_center_x']
            center_y = form.cleaned_data['param_center_y']
            center_z = form.cleaned_data['param_center_z']
            size_x = form.cleaned_data['param_size_x']
            size_y = form.cleaned_data['param_size_y']
            size_z = form.cleaned_data['param_size_z']

            exec_string_template += "--center_x {0:s} --center_y {1:s} --center_z {2:s} --size_x {3:s} --size_y {4:s} --size_z {5:s} ".format(
                center_x, center_y, center_z, size_x, size_y, size_z)

        if form.cleaned_data.get('param_seed'):
            exec_string_template += "--seed {0:s} ".format(form.cleaned_data['param_seed'])

        if form.cleaned_data.get('param_exhaustiveness'):
            exec_string_template += "--exhaustiveness {0:s} ".format(form.cleaned_data['param_exhaustiveness'])

        if form.cleaned_data.get('param_num_modes'):
            exec_string_template += "--num_modes {0:s} ".format(form.cleaned_data['param_num_modes'])

        if form.cleaned_data.get('param_energy_range'):
            exec_string_template += "--energy_range {0:s} ".format(form.cleaned_data['param_energy_range'])

        if form.cleaned_data['param_local_only']:
            exec_string_template += "--local_only "

        if form.cleaned_data['param_randomize_only']:
            exec_string_template += "--randomize_only "

        if form.cleaned_data.get('param_weight_gauss1'):
            exec_string_template += "--weight_gauss1 {0:s} ".format(form.cleaned_data['param_weight_gauss1'])

        if form.cleaned_data.get('param_weight_gauss2'):
            exec_string_template += "--weight_gauss2 {0:s} ".format(form.cleaned_data['param_weight_gauss2'])

        if form.cleaned_data.get('param_weight_repulsion'):
            exec_string_template += "--weight_repulsion {0:s} ".format(
                form.cleaned_data['param_weight_repulsion'])

        if form.cleaned_data.get('param_weight_hydrophobic'):
            exec_string_template += "--weight_hydrophobic {0:s} ".format(
                form.cleaned_data['param_weight_hydrophobic'])

        if form.cleaned_data.get('param_weight_hydrogen'):
            exec_string_template += "--weight_hydrogen {0:s} ".format(
                form.cleaned_data['param_weight_hydrogen'])

        if form.cleaned_data.get('param_weight_rot'):
            exec_string_template += "--weight_rot {0:s} ".format(form.cleaned_data['param_weight_rot'])

        exec_string_template += "; "

        # build commands

        command_list = []
        task_remote_subdirs = ['input', 'output']
        for f in form.cleaned_data['param_ligands']:
            instance = SkyLabFile.objects.create(type=1, upload_path='input/ligands', file=f, task=task)
            filepath = instance.file.name
            # filepath = create_input_skylab_file(task, 'input/ligands', f)
            filename_without_ext = os.path.splitext(f.name)[0]
            task_remote_subdir = 'output/' + filename_without_ext

            outpath = os.path.join(task.task_dirname, task_remote_subdir)

            task_remote_subdirs.append(task_remote_subdir)
            command_list.append(exec_string_template.format(outpath=outpath, filepath=filepath))

        task.task_data = json.dumps({'command_list': command_list, 'task_remote_subdirs': task_remote_subdirs})
        task.save()
        self.kwargs['task_id'] = task.id
        return super(VinaView, self).form_valid(form)

class VinaSplitView(LoginRequiredMixin, FormView):
    #TODO: support dynamic formsetl multiple input files; remove input, output prefix; set to created default
    template_name = "modules/vina/use_vina_split.html"
    form_class = VinaSplitForm

    def get_form_kwargs(self):
        # pass "user" keyword argument with the current user to your form
        kwargs = super(VinaSplitView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('task_detail_view', kwargs={'pk': self.kwargs.pop('id')})

    def form_valid(self, form):
        cluster = form.cleaned_data['mpi_cluster']

        input_file = form.cleaned_data['param_input']
        exec_string = u"vina_split --input {0:s} ".format(input_file.name)

        input_filename_without_ext = os.path.splitext(os.path.basename(input_file.name))[0]

        if form.cleaned_data.get('param_ligand_prefix'):
            exec_string += u"--ligand {0:s} ".format(get_valid_filename(form.cleaned_data['param_ligand_prefix']))
        else:
            exec_string += u"--ligand {0:s}-ligand ".format(input_filename_without_ext)

        if form.cleaned_data.get('param_flex_prefix'):
            exec_string += u"--flex {0:s} ".format(get_valid_filename(form.cleaned_data['param_flex_prefix']))
        else:
            exec_string += u"--flex {0:s}-flex ".format(input_filename_without_ext)

        #print(exec_string)

        tool = Tool.objects.get(display_name="Vina split")
        task = Task.objects.create(
            mpi_cluster=cluster, tool=tool, user=self.request.user,
            task_data=json.dumps({'command_list': [exec_string]})
        )
        self.kwargs['id'] = task.id  # pass to get_success_url

        SkyLabFile.objects.create(type=1, file=input_file, task=task)

        return super(VinaSplitView, self).form_valid(form)
