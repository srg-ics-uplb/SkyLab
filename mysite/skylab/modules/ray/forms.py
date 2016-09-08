from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Fieldset, HTML
from django import forms
from django.db.models import Q
from django.core.validators import MinValueValidator, MaxValueValidator
from multiupload.fields import MultiFileField
from validators import odd_number_validator, txt_file_validator, tsv_file_validator, ray_file_extension_validator, \
    multi_graph_files_validator, multi_ray_files_validator
from skylab.models import MPI_Cluster
from skylab.modules.base_tool import MPIModelChoiceField


class SelectMPIFilesForm(forms.Form):
    param_bynode = forms.BooleanField(required=False, label="-bynode",
                                      help_text="Launch processes one per node, cycling by node in a round-robin fashion. This spreads processes evenly among nodes and assigns MPI_COMM_WORLD ranks in a round-robin, 'by node' manner. ")
    # param_mini_ranks = forms.BooleanField(required=False, label="-mini-ranks-per-rank",
    #                                       help_text="Mini ranks can be thought as ranks within ranks. <a href='https://github.com/sebhtml/RayPlatform/blob/master/Documentation/MiniRanks.txt'>See documentation</a>")
    # mini-ranks max set to 4
    param_mini_ranks = forms.IntegerField(required=False, min_value=1, max_value=4, label="Mini-ranks per rank",
                                          help_text="Mini ranks can be thought as ranks within ranks. <a href='https://github.com/sebhtml/RayPlatform/blob/master/Documentation/MiniRanks.txt'>See documentation</a>",
                                          validators=[MinValueValidator(1), MaxValueValidator(4)],
                                          widget=forms.NumberInput(attrs={'placeholder': 'default: 1'}))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('user')
        super(SelectMPIFilesForm, self).__init__(*args, **kwargs)
        # self.fields['mpi_cluster'].queryset = MPI_Cluster.objects.filter(creator=self.user)
        current_user_as_creator = Q(creator=self.user)
        cluster_is_public = Q(shared_to_public=True)
        supports_ray = Q(supported_tools="ray")
        # is_ready = Q(status=1)
        q = MPI_Cluster.objects.filter(current_user_as_creator | cluster_is_public)
        q = q.filter(supports_ray).exclude(status=4)  # exclude unusable clusters

        self.fields['mpi_cluster'] = MPIModelChoiceField(queryset=q, label="MPI Cluster",
                                                         help_text="Getting an empty list? Try <a href='../create_mpi_cluster'>creating an MPI Cluster</a> first.")


        self.helper = FormHelper()
        self.helper.form_tag = False
        # self.helper.form_id = 'id-rayForm'
        # self.helper.form_class = 'use-tool-forms'
        # self.helper.form_method = 'post'
        # self.helper.form_action = ''
        self.helper.layout = Layout(    #crispy_forms layout


            Div(
                Field('mpi_cluster', wrapper_class='col-xs-5'),
                css_class="col-sm-12"
            ),

            Fieldset(
                'MiniRanks',
                Div(
                    Div('param_bynode', css_class='col-xs-12'),
                    Div('param_mini_ranks', css_class='col-xs-4'),

                    css_class='row-fluid col-sm-12'
                )
            ),


        )

        # def clean(self):
        #     if self.cleaned_data:
        #         if self.cleaned_data['param_mini_ranks']:
        #             if not self.cleaned_data["param_mini_ranks"]:
        #                 raise forms.ValidationError(u'-mini-ranks-per-rank: No value provided',
        #                                             code="mini_ranks_no_value_set")



class InputParameterForm(forms.Form):
    PARAMETER_CHOICES = (   #input parameter args
        ('', '---------'),
        ('-p','-p'),
        ('-i','-i'),
        ('-s','-s'),
    )
    parameter = forms.ChoiceField(choices=PARAMETER_CHOICES, required=False)
    input_file1 = forms.FileField(label="Sequence file 1", validators=[ray_file_extension_validator], required=False)
    input_file2 = forms.FileField(label="Sequence file 2", validators=[ray_file_extension_validator], required=False)


    def __init__(self, *args, **kwargs):
        super(InputParameterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.disable_csrf = True
        self.helper.form_tag = False  # remove form headers

        # self.helper.form_id = 'id-rayForm'
        # self.helper.form_class = 'use-tool-forms'
        # self.helper.form_method = 'post'

        self.helper.layout = Layout(  # layout using crispy_forms
            Div(
                Div(Field('parameter', css_class='parameter'), css_class='col-xs-2'),
                Div(Field('input_file1', wrapper_class="hidden"), css_class='col-xs-3 col-xs-offset-1'),
                Div(Field('input_file2', wrapper_class="hidden"), css_class='col-xs-3'),

                css_class='row-fluid col-sm-12 form-container'
            ),
        )

    def clean(self):
        if self.cleaned_data:
            parameter = self.cleaned_data["param_executable"]
            input_file1 = self.cleaned_data.get('input_file1')
            input_file2 = self.cleaned_data.get('input_file2')

            # print parameter, input_file1

            if parameter == '-p':  # -p needs two input files

                if not input_file1 or not input_file2:
                    raise forms.ValidationError(
                        '-p parameter requires two input files',
                        code='-p_incomplete_input_files'
                    )

            elif parameter == '-i' or parameter == '-s':  # -i and -s needs one input file
                if not input_file1:
                    raise forms.ValidationError(
                        '%s parameter requires one input file' % parameter,
                        code='%s_incomplete_input_files' % parameter
                    )




class OtherParameterForm(forms.Form):
    # param_kmer = forms.BooleanField(required=False, label="-k")
    # todo: verify min_value for kmer_length, 32 is default max if not specified in compilation
    # source: http://blog.gmane.org/gmane.science.biology.ray-genome-assembler/month=20121101
    param_kmer_length = forms.IntegerField(validators=[odd_number_validator], max_value=32, min_value=1,
                                           required=False, label="",
                                           help_text="Value must be odd.",
                                           widget=forms.NumberInput(attrs={'placeholder': 'default: 21'}))

    # Ray surveyor options See Documentation/Ray-Surveyor.md
    param_run_surveyor = forms.BooleanField(required=False, label="-run-surveyor",
                                            help_text="Runs Ray Surveyor to compare samples.")
    param_read_sample_graph = forms.BooleanField(required=False, label='-read-sample-graph',
                                                 help_text="Reads sample graphs (generated with -write-kmers).")  # dependent on -write-kmers parameter
    subparam_graph_files = MultiFileField(required=False, min_num=1, label="Upload graph(s)",
                                          validators=[multi_graph_files_validator])
    # todo: sampleName = tool_activity_%d % id, sampleGraphFile = output_directory/kmers.txt

    # Assembly options are skipped because documentation says (defaults work well)
    # Distributed storage engine options are skipped due to lack of knowledge with mpi ranks

    # Biological abundances See Documentation/BiologicalAbundances.txt
    param_search = forms.BooleanField(required=False, label='-search',
                                      help_text="Provide fasta files to be searched in the de Bruijn graph.")
    subparam_search_files = MultiFileField(min_num=1, required=False, label='Upload search files', validators=[
        multi_ray_files_validator])  # save to tool_activity_x/input/search
    param_one_color_per_file = forms.BooleanField(required=False, label="-one-color-per-file",
                                                  help_text="Sets one color per file instead of one per sequence. For files with large numbers of sequences, using one single color per file may be more efficient.")

    # Taxonomic profiling with colored de Bruijn graphs
    # Computes and writes detailed taxonomic profiles. See Documentation/Taxonomy.txt for details.
    param_with_taxonomy = forms.BooleanField(required=False, label='-with-taxonomy',
                                             help_text="Computes and writes detailed taxonomic profiles.")
    subparam_genome_to_taxon_file = forms.FileField(required=False, validators=[tsv_file_validator],
                                                    label="Genome-to-Taxon")
    subparam_tree_of_life_edges_file = forms.FileField(required=False, validators=[tsv_file_validator],
                                                       label="TreeOfLife-Edges")
    subparam_taxon_names_file = forms.FileField(required=False, validators=[tsv_file_validator], label="Taxon-Names")

    # Provides an ontology and annotations. See Documentation/GeneOntology.txt
    param_gene_ontology = forms.BooleanField(required=False, label="-gene-ontology",
                                             help_text="Provides an ontology and annotations. OntologyTerms.txt is automatically fetched from geneontology.org .")
    # todo: The OntologyTerms.txt file is http://geneontology.org/ontology/obo_format_1_2/gene_ontology_ext.obo

    subparam_annotations_file = forms.FileField(required=False, validators=[txt_file_validator], label="Annotations",
                                                help_text="The annotation file must be derived from Uniprot-GOA (http://www.ebi.ac.uk/GOA/).")

    # Other outputs
    param_enable_neighbourhoods = forms.BooleanField(required=False, label="-enable-neighbourhoods",
                                                     help_text="Computes contig neighborhoods in the de Bruijn graph")
    param_amos = forms.BooleanField(required=False, label="-amos",
                                    help_text="Writes the AMOS file that contains read positions on contigs.")
    param_write_kmers = forms.BooleanField(required=False, label="-write-kmers",
                                           help_text="Writes k-mer graph")
    param_graph_only = forms.BooleanField(required=False, label="-graph-only",
                                          help_text="Exits after building graph.")
    param_write_read_markers = forms.BooleanField(required=False, label="-write-read-markers",
                                                  help_text="Writes read markers to disk.")
    param_write_seeds = forms.BooleanField(required=False, label="-write-seeds",
                                           help_text="Writes seed DNA sequences")
    param_write_extensions = forms.BooleanField(required=False, label="-write-extensions",
                                                help_text="Writes extension DNA sequences")
    param_write_contig_paths = forms.BooleanField(required=False, label="-write-contig-paths",
                                                  help_text="Writes contig paths with coverage values")
    param_write_marker_summary = forms.BooleanField(required=False, label="-write-marker-summary",
                                                    help_text="Writes marker statistics.")

    # Memory usage
    param_show_memory_usage = forms.BooleanField(required=False, label="-show-memory-usage",
                                                 help_text="Shows memory usage")
    param_show_memory_allocations = forms.BooleanField(required=False, label="-show-memory-allocations",
                                                       help_text="Shows memory allocation events")

    # Algorithm verbosity
    param_show_extension_choice = forms.BooleanField(required=False, label="-show-extension-choice",
                                                     help_text="Shows the choice made (with other choices) during the extension.")
    param_show_ending_context = forms.BooleanField(required=False, label="-show-ending-context",
                                                   help_text="Shows the ending context of each extension. Shows the children of the vertex where extension was too difficult.")
    param_show_distance_summary = forms.BooleanField(required=False, label="-show-distance-summary",
                                                     help_text="Shows summary of outer distances used for an extension path.")
    param_show_consensus = forms.BooleanField(required=False, label="-show-consensus",
                                              help_text="Shows the consensus when a choice is done.")

# Checkpointing is skipped
# Message routing is skipped
# Hardware testing is skipped
# Debugging is skipped

    def __init__(self, *args, **kwargs):  # for crispy forms layout
        super(OtherParameterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.disable_csrf = True
        self.helper.form_tag = False  # remove form headers
        # self.helper.form_error_title = "Form Errors"
        # self.helper.form_id = 'id-rayForm'
        # self.helper.form_class = 'use-tool-forms'
        # self.helper.form_method = 'post'

        self.helper.layout = Layout(

            Fieldset(
                'K-mer length',
                Div(
                    Div('param_kmer_length', css_class='col-xs-3'),
                    css_class='row-fluid col-sm-12'
                )
            ),
            Fieldset(
                'Ray Surveyor options',
                Div(
                    Div('param_run_surveyor', css_class='col-xs-6'),
                    css_class='col-sm-12'
                ),
                Div(
                    Div('param_read_sample_graph', css_class='col-xs-6'),
                    Div('subparam_graph_files', css_class='col-xs-3'),
                    css_class='row-fluid col-sm-12'
                ),
            ),
            Fieldset(

                'Biological abundances',
                Div(
                    Div('param_search', css_class='col-xs-6'),
                    Div('subparam_search_files', css_class='col-xs-3'),
                    css_class='row-fluid col-sm-12'
                ),
                Div(
                    Div('param_one_color_per_file', css_class='col-xs-12'),
                    css_class='col-sm-12'
                ),
            ),
            Fieldset(
                'Taxonomic profiling with colored de Bruijn graphs',
                Div(
                    Div(
                        'param_with_taxonomy',
                        HTML(
                            """<a href="https://github.com/sebhtml/ray/blob/master/Documentation/Taxonomy.txt">See documentation</a>"""),
                        css_class='col-xs-3'
                    ),
                    Div('subparam_genome_to_taxon_file', css_class='col-xs-3'),
                    Div('subparam_tree_of_life_edges_file', css_class='col-xs-3'),
                    Div('subparam_taxon_names_file', css_class='col-xs-3'),

                    css_class='row-fluid col-sm-12'
                ),
                Div(
                    Div(
                        'param_gene_ontology',
                        HTML(
                            """<a href="https://github.com/sebhtml/ray/blob/master/Documentation/GeneOntology.txt">See documentation</a>"""),
                        css_class='col-xs-5',

                    ),
                    Div('subparam_annotations_file', css_class='col-xs-3'),
                    css_class='row-fluid col-sm-12'
                )
            ),
            Fieldset(
                'Other outputs',
                Div(
                    Div('param_enable_neighbourhoods', css_class='col-xs-3'),
                    Div('param_amos', css_class='col-xs-3'),
                    Div('param_write_kmers', css_class='col-xs-3'),
                    Div('param_graph_only', css_class='col-xs-3'),
                    css_class='row-fluid col-sm-12'
                ),
                Div(
                    Div('param_write_read_markers', css_class='col-xs-3'),
                    Div('param_write_seeds', css_class='col-xs-3'),
                    Div('param_write_extensions', css_class='col-xs-3'),
                    Div('param_write_contig_paths', css_class='col-xs-3'),
                    css_class='row-fluid col-sm-12'
                ),
                Div(
                    Div('param_write_marker_summary', css_class='col-xs-3'),
                    css_class='col-sm-12'
                )
            ),
            Fieldset(
                'Memory usage',
                Div(
                    Div(
                        Div('param_show_memory_usage', css_class='col-xs-6'),
                        Div('param_show_memory_allocations', css_class='col-xs-6'),
                    ),
                    css_class="row-fluid col-sm-12"
                )
            ),
            Fieldset(
                'Algorithm verbosity',
                Div(
                    Div('param_show_extension_choice', css_class='col-xs-6'),
                    Div('param_show_ending_context', css_class='col-xs-6'),
                    Div('param_show_distance_summary', css_class='col-xs-6'),
                    Div('param_show_consensus', css_class='col-xs-6'),
                    css_class='row-fluid col-sm-12'
                )
            )
        )

    def clean(self):
        if self.cleaned_data:
            # if self.cleaned_data['param_kmer']:
            #     if not self.cleaned_data.get('subparam_kmer_length'):
            #         raise forms.ValidationError(u'-k: No value provided', code='kmer_no_value_set')

            if self.cleaned_data['param_read_sample_graph']:
                if not self.cleaned_data.get('subparam_graph_files'):
                    raise forms.ValidationError(u'-read-sample-graph: No graph files are provided',
                                                code='no_graphs_to_read_provided')

            if self.cleaned_data['param_search']:
                print "search is triggered"
                if not self.cleaned_data.get('subparam_search_files'):
                    raise forms.ValidationError(u'-search: No search files are provided',
                                                code="no_search_files_provided")

            if self.cleaned_data['param_with_taxonomy']:
                if not self.cleaned_data.get('subparam_genome_to_taxon_file'):
                    raise forms.ValidationError(u'-with-taxonomy: Missing Genome-to-Taxon file',
                                                code="with_taxo_no_genome_to_taxon")
                if not self.cleaned_data.get('subparam_tree_of_life_edges_file'):
                    raise forms.ValidationError(u'-with-taxonomy: Missing TreeOfLife-Edges file',
                                                code="with_taxo_no_tree_of_life")
                if not self.cleaned_data.get('subparam_taxon_names_file'):
                    raise forms.ValidationError(u'-with-taxonomy: Missing Taxon-Names file',
                                                code="with_taxo_no_taxon_names")

            if self.cleaned_data['param_gene_ontology']:
                if not self.cleaned_data.get('subparam_annotations_file'):
                    raise forms.ValidationError(u'-gene-ontology: Missing Annotations file',
                                                code="gene_ontology_no_anno_file")
