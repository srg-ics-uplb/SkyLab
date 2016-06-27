from django.views.generic import TemplateView, FormView
from skylab.modules.vina.forms import VinaForm
from django import forms
from django.shortcuts import render, redirect
from skylab.models import MPI_Cluster, ToolActivity, SkyLabFile
from skylab.modules.base_tool import send_mpi_message, create_skylab_file
import os.path
import json


class VinaView(TemplateView):
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

            exec_string_template = "vina "
            tool_activity = ToolActivity.objects.create(
                mpi_cluster=cluster_name, tool_name="vina", user=self.request.user, exec_string=exec_string_template
            )

            receptor_filepath = create_skylab_file(tool_activity, '', vina_form.cleaned_data['param_receptor'])
            exec_string_template += "--receptor %s " % receptor_filepath

            if vina_form.cleaned_data.get('param_flex'):
                flex_filepath = create_skylab_file(tool_activity, '', vina_form.cleaned_data['param_flex'])
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
            for file in vina_form.cleaned_data['param_ligands']:
                filepath = create_skylab_file(tool_activity, 'ligands', file)
                basename = os.path.splitext(file.name)[0]
                outpath = "tool_activity_%d/output/%s" % (tool_activity.id, basename)

                exec_string += exec_string_template % (filepath, outpath, outpath)

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

            return redirect("../toolactivity/%d" % tool_activity.id)
        else:
            return render(request, 'modules/vina/use_vina.html', {
                'vina_form': vina_form,

            })


class VinaSplitView(FormView):
    pass
