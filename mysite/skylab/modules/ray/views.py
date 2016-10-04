import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import formset_factory
from django.shortcuts import render, redirect
from django.views.generic import TemplateView

from skylab.models import MPICluster, Task, SkyLabFile
from skylab.modules.basetool import send_mpi_message
from skylab.modules.ray.forms import InputParameterForm, SelectMPIFilesForm, OtherParameterForm


class RayView(LoginRequiredMixin, TemplateView):
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
            cluster_name = select_mpi_form.cleaned_data['mpi_cluster']
            cluster_size = MPICluster.objects.get(cluster_name=cluster_name).cluster_size

            # -n cluster_size
            exec_string = "mpiexec -n %s " % cluster_size

            # -bynode
            if select_mpi_form.cleaned_data['param_bynode']:
                exec_string += "-bynode "

            task = Task.objects.create(
                mpi_cluster=cluster_name, tool_name="ray", executable_name="ray", user=self.request.user,
                exec_string=exec_string
            )

            exec_string += "Ray -o tool_activity_%d/output " % task.id

            # k-mer length
            if other_parameter_form.cleaned_data.get('param_kmer_length'):
                exec_string += "-k %s " % other_parameter_form.cleaned_data["param_kmer_length"]

            # -mini-ranks-per-rank
            if select_mpi_form.cleaned_data.get('param_mini_ranks'):
                exec_string += "-mini-ranks-per-rank %s " % select_mpi_form.cleaned_data["param_mini_ranks"]

            for form in input_formset:
                parameter = form.cleaned_data.get('parameter')
                if parameter:  # ignore blank parameter value

                    input_file1 = form.cleaned_data['input_file1']
                    instance = SkyLabFile.objects.create(type=1, file=input_file1, task=task)
                    # filepath1 = create_input_skylab_file(tool_activity, 'input', input_file1)
                    filepath1 = instance.file.name

                if parameter == "-p":
                    input_file2 = form.cleaned_data['input_file2']
                    instance = SkyLabFile.objects.create(type=1, file=input_file2, task=task)
                    # filepath2 = create_input_skylab_file(tool_activity, 'input', input_file2)
                    filepath2 = instance.file.name

                    exec_string += "%s %s %s " % (parameter, filepath1, filepath2)

                elif parameter == "-s" or parameter == "-i":
                    exec_string += "%s %s " % (parameter, filepath1)

            if other_parameter_form.cleaned_data['param_run_surveyor']:
                exec_string += "-run-surveyor "

            if other_parameter_form.cleaned_data['param_read_sample_graph']:
                for index, f in other_parameter_form.cleaned_data['subparam_graph_files']:
                    instance = SkyLabFile.objects.create(type=1, upload_path='input/graph', file=f, task=task)
                    filepath = instance.file.name
                    #filepath = create_input_skylab_file(tool_activity, 'input/graph', f)
                    exec_string += "-read-sample-graph graph%s %s " % (index, filepath)

            if other_parameter_form.cleaned_data['param_search']:
                exec_string += "-search tool_activity_%d/input/search " % task.id
                for f in other_parameter_form.cleaned_data['subparam_search_files']:
                    SkyLabFile.objects.create(type=1, upload_path='input/search', file=f, task=task)

            if other_parameter_form.cleaned_data['param_one_color_per_file']:
                exec_string += "-one-color-per-file "

            if other_parameter_form.cleaned_data['param_with_taxonomy']:
                genome_to_taxon_file = other_parameter_form.cleaned_data['subparam_genome_to_taxon_file']
                tree_of_life_edges_file = other_parameter_form.cleaned_data['subparam_tree_of_life_edges_file']
                taxon_names_file = other_parameter_form.cleaned_data['subparam_taxon_names_file']

                instance = SkyLabFile.objects.create(type=1, upload_path='input/taxonomy', file=genome_to_taxon_file,
                                                     task=task)
                genome_filepath = instance.file.name
                instance = SkyLabFile.objects.create(type=1, upload_path='input/taxonomy', file=tree_of_life_edges_file,
                                                     task=task)
                tree_filepath = instance.file.name
                instance = SkyLabFile.objects.create(type=1, upload_path='input/taxonomy', file=taxon_names_file,
                                                     task=task)
                taxon_filepath = instance.file.name

                exec_string += "-with-taxonomy %s %s %s " % (genome_filepath, tree_filepath, taxon_filepath)

            if other_parameter_form.cleaned_data['param_gene_ontology']:
                annotations_file = other_parameter_form.cleaned_data['subparam_annotations_file']

                SkyLabFile.objects.create(type=1, upload_path='input/gene_ontology', file=annotations_file, task=task)
                exec_string += "-gene-ontology tool_activity_%d/input/OntologyTerms.txt %s " % (
                    task.id, annotations_file.name)

            # Other Output options
            if other_parameter_form.cleaned_data['param_enable_neighbourhoods']:
                exec_string += "-enable-neighbourhoods "

            if other_parameter_form.cleaned_data['param_amos']:
                exec_string += "-amos "

            if other_parameter_form.cleaned_data['param_write_kmers']:
                exec_string += "-write-kmers "

            if other_parameter_form.cleaned_data['param_graph_only']:
                exec_string += "-graph-only "

            if other_parameter_form.cleaned_data['param_write_read_markers']:
                exec_string += "-write-read-markers "

            if other_parameter_form.cleaned_data['param_write_seeds']:
                exec_string += "-write-seeds "

            if other_parameter_form.cleaned_data['param_write_extensions']:
                exec_string += "-write-extensions "

            if other_parameter_form.cleaned_data['param_write_contig_paths']:
                exec_string += "-write-contig-paths "

            if other_parameter_form.cleaned_data['param_write_marker_summary']:
                exec_string += "-write-marker-summary "

            # Memory usage
            if other_parameter_form.cleaned_data['param_show_memory_usage']:
                exec_string += "-show-memory-usage "
            if other_parameter_form.cleaned_data['param_show_memory_allocations']:
                exec_string += "-show-memory-allocations "

            # Algorithm verbosity
            if other_parameter_form.cleaned_data['param_show_extension_choice']:
                exec_string += "-show-extension-choice "

            if other_parameter_form.cleaned_data['param_show_ending_context']:
                exec_string += "-show-ending-context "
            if other_parameter_form.cleaned_data["param_show_distance_summary"]:
                exec_string += "-show-distance-summary "
            if other_parameter_form.cleaned_data['param_show_consensus']:
                exec_string += "-show-consensus "

            task.exec_string = exec_string
            task.save()

            print (exec_string)

            data = {
                "actions": "use_tool",
                "activity": task.id,
                "tool": task.tool_name,
                "param_executable": "ray",
            }
            message = json.dumps(data)
            print (message)
            # find a way to know if thread is already running
            send_mpi_message("skylab.consumer.%d" % task.mpi_cluster.id, message)
            task.status = "Task Queued"

            return redirect("../task/%d" % task.id)
        else:
            return render(request, 'modules/ray/use_ray.html', {
                'select_mpi_form': select_mpi_form,
                'other_parameter_form': other_parameter_form,
                'input_formset': input_formset,
            })
                # todo fetch: ontologyterms.txt from http://geneontology.org/ontology/obo_format_1_2/gene_ontology_ext.obo for -gene-ontology
