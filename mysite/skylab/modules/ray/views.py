import json

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.forms import formset_factory
from django.shortcuts import render, redirect
from django.views.generic import TemplateView

from skylab.models import MPICluster, Task, SkyLabFile, Tool
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

            command_list = []
            # -n cluster_size
            command = "mpiexec -n {0:d} -f {1:s} ".format(cluster_size, settings.MPIEXEC_NODES_FILE)

            # -bynode
            if select_mpi_form.cleaned_data['param_bynode']:
                command += "-bynode "

            tool = Tool.objects.get(display_name="Ray")
            task = Task.objects.create(
                mpi_cluster=cluster_name, tool=tool, user=self.request.user
            )

            command += "Ray -o task_{0:d}/output ".format(task.id)

            # k-mer length
            if other_parameter_form.cleaned_data.get('param_kmer_length'):
                command += "-k {0:s} ".format(other_parameter_form.cleaned_data["param_kmer_length"])

            # -mini-ranks-per-rank
            if select_mpi_form.cleaned_data.get('param_mini_ranks'):
                command += "-mini-ranks-per-rank {0:s} ".format(select_mpi_form.cleaned_data["param_mini_ranks"])

            for form in input_formset:
                parameter = form.cleaned_data.get('parameter')
                if parameter:  # ignore blank parameter value

                    input_file1 = form.cleaned_data['input_file1']
                    instance = SkyLabFile.objects.create(type=1, file=input_file1, task=task)
                    # filepath1 = create_input_skylab_file(task, 'input', input_file1)
                    filepath1 = instance.file.name

                if parameter == "-p":
                    input_file2 = form.cleaned_data['input_file2']
                    instance = SkyLabFile.objects.create(type=1, file=input_file2, task=task)
                    # filepath2 = create_input_skylab_file(task, 'input', input_file2)
                    filepath2 = instance.file.name

                    command += "{0:s} {1:s} {2:s} ".format(parameter, filepath1, filepath2)

                elif parameter == "-s" or parameter == "-i":
                    command += "{0:s} {1:s} ".format(parameter, filepath1)

            if other_parameter_form.cleaned_data['param_run_surveyor']:
                command += "-run-surveyor "

            if other_parameter_form.cleaned_data['param_read_sample_graph']:
                for index, f in other_parameter_form.cleaned_data['subparam_graph_files']:
                    instance = SkyLabFile.objects.create(type=1, upload_path='input/graph', file=f, task=task)
                    filepath = instance.file.name
                    # filepath = create_input_skylab_file(task, 'input/graph', f)
                    command += "-read-sample-graph graph{0:s} {1:s} ".format(index, filepath)

            if other_parameter_form.cleaned_data['param_search']:
                command += "-search task_{0:d}/input/search ".format(task.id)
                for f in other_parameter_form.cleaned_data['subparam_search_files']:
                    SkyLabFile.objects.create(type=1, upload_path='input/search', file=f, task=task)

            if other_parameter_form.cleaned_data['param_one_color_per_file']:
                command += "-one-color-per-file "

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

                command += "-with-taxonomy {0:s} {1:s} {2:s} ".format(genome_filepath, tree_filepath, taxon_filepath)

            if other_parameter_form.cleaned_data['param_gene_ontology']:
                annotations_file = other_parameter_form.cleaned_data['subparam_annotations_file']

                SkyLabFile.objects.create(type=1, upload_path='input/gene_ontology', file=annotations_file, task=task)
                command += "-gene-ontology task_{0:d}/input/OntologyTerms.txt {1:s} ".format(task.id,
                                                                                             annotations_file.name)

                command_list.append(
                    "wget -O task_{0:d}/input/OntologyTerms.txt http://geneontology.org/ontology/obo_format_1_2/gene_ontology_ext.obo".format(
                        task.id))

            # Other Output options
            if other_parameter_form.cleaned_data['param_enable_neighbourhoods']:
                command += "-enable-neighbourhoods "

            if other_parameter_form.cleaned_data['param_amos']:
                command += "-amos "

            if other_parameter_form.cleaned_data['param_write_kmers']:
                command += "-write-kmers "

            if other_parameter_form.cleaned_data['param_graph_only']:
                command += "-graph-only "

            if other_parameter_form.cleaned_data['param_write_read_markers']:
                command += "-write-read-markers "

            if other_parameter_form.cleaned_data['param_write_seeds']:
                command += "-write-seeds "

            if other_parameter_form.cleaned_data['param_write_extensions']:
                command += "-write-extensions "

            if other_parameter_form.cleaned_data['param_write_contig_paths']:
                command += "-write-contig-paths "

            if other_parameter_form.cleaned_data['param_write_marker_summary']:
                command += "-write-marker-summary "

            # Memory usage
            if other_parameter_form.cleaned_data['param_show_memory_usage']:
                command += "-show-memory-usage "
            if other_parameter_form.cleaned_data['param_show_memory_allocations']:
                command += "-show-memory-allocations "

            # Algorithm verbosity
            if other_parameter_form.cleaned_data['param_show_extension_choice']:
                command += "-show-extension-choice "

            if other_parameter_form.cleaned_data['param_show_ending_context']:
                command += "-show-ending-context "
            if other_parameter_form.cleaned_data["param_show_distance_summary"]:
                command += "-show-distance-summary "
            if other_parameter_form.cleaned_data['param_show_consensus']:
                command += "-show-consensus "

            command_list.append(command)

            task.command_list = json.dumps(command_list)
            task.save()

            return redirect(reverse('task_detailview', kwargs={'pk': task.id}))
        else:
            return render(request, 'modules/ray/use_ray.html', {
                'select_mpi_form': select_mpi_form,
                'other_parameter_form': other_parameter_form,
                'input_formset': input_formset,
            })
