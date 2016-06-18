from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Fieldset, HTML
from django import forms
from django.db.models import Q
from multiupload.fields import MultiFileField
import os
from skylab.models import MPI_Cluster


class SelectMPIFilesForm(forms.Form):
    param_bynode = forms.BooleanField(required=False, label="-bynode",
                                      help_text="Launch processes one per node, cycling by node in a round-robin fashion. This spreads processes evenly among nodes and assigns MPI_COMM_WORLD ranks in a round-robin, 'by node' manner. ")
    param_mini_ranks = forms.BooleanField(required=False, label="-mini-ranks-per-rank",
                                          help_text="Mini ranks can be thought as ranks within ranks.")
    subparam_ranks_per_rank = forms.IntegerField(required=False, initial=1, min_value=1, label="")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('user')
        super(SelectMPIFilesForm, self).__init__(*args, **kwargs)
        # self.fields['mpi_cluster'].queryset = MPI_Cluster.objects.filter(creator=self.user)
        current_user_as_creator = Q(creator=self.user)
        cluster_is_public = Q(shared_to_public=True)
        supports_gamess = Q(supported_tools="gamess")
        # is_ready = Q(status=1)
        q = MPI_Cluster.objects.filter(current_user_as_creator | cluster_is_public)
        q = q.filter(supports_gamess).exclude(status=4) #exclude unusable clusters

        self.fields['mpi_cluster'] = forms.ModelChoiceField(queryset=q)

        self.helper = FormHelper()
        self.helper.form_tag = False
        # self.helper.form_id = 'id-rayForm'
        # self.helper.form_class = 'use-tool-forms'
        # self.helper.form_method = 'post'
        # self.helper.form_action = ''
        self.helper.layout = Layout(    #crispy_forms layout


            Div(
                Field('mpi_cluster', wrapper_class='col-xs-4'),
                css_class="col-sm-12"
            ),

            Fieldset(
                'MiniRanks',
                Div(
                    Div('param_bynode', css_class='col-xs-12'),
                    Div('param_mini_ranks', css_class='col-xs-4'),
                    Div('subparam_ranks_per_rank', css_class='col-xs-1'),
                    Div(HTML(
                        """<a href="https://github.com/sebhtml/RayPlatform/blob/master/Documentation/MiniRanks.txt">See documentation</a>"""),
                        css_class="col-xs-3"),

                    css_class='row-fluid col-sm-12'
                )
            ),


        )


def validate_ray_file_extension(value):
    # export.txt, qseq.txt are not supported because of lack of documentation on their use case
    valid_file_extensions = ['.fasta', '.fa', '.fasta.gz', '.fa.gz', '.fasta.bz2', '.fa.bz2', '.fastq', '.fq',
                             '.fastq.gz', '.fq.gz', '.fastq.bz2',
                             '.fq.bz2', '.sff', '.csfasta', '.csfa', '.conf'
                             ]
    valid = False
    for ext in valid_file_extensions:
        if value.name.lower().endswith(ext):
            valid = True
            break
    if not valid:
        raise forms.ValidationError(u'Filetype not supported', code='invalid_filetype')


class InputParameterForm(forms.Form):
    PARAMETER_CHOICES = (   #input parameter args
        ('', '---------'),
        ('-p','-p'),
        ('-i','-i'),
        ('-s','-s'),
    )
    parameter = forms.ChoiceField(choices=PARAMETER_CHOICES, required=False)
    avg_outer_distance = forms.DecimalField(label="Average outer distance", required=False, help_text="Optional",
                                            min_value=0)
    std_deviation = forms.DecimalField(label="Standard deviation", required=False, help_text="Optional", min_value=0)

    input_file1 = forms.FileField(label="Input file 1", validators=[validate_ray_file_extension], required=False)
    input_file2 = forms.FileField(label="Input file 2", validators=[validate_ray_file_extension], required=False)


    def __init__(self, *args, **kwargs):
        super(InputParameterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.disable_csrf = True
        self.helper.form_tag = False  # remove form headers
        # self.helper.form_error_title = "Form Errors"
        # self.helper.form_id = 'id-rayForm'
        # self.helper.form_class = 'use-tool-forms'
        # self.helper.form_method = 'post'

        # self.helper.form_action = ''

        self.helper.layout = Layout(  # layout using crispy_forms
            Div(
                Div(Field('parameter', css_class='parameter'), css_class='col-xs-1'),
                Div('avg_outer_distance', css_class='col-xs-2'),
                Div('std_deviation', css_class='col-xs-2'),

                Div('input_file1', css_class='col-xs-3'),
                Div('input_file2', css_class='col-xs-3'),

                css_class='row-fluid col-sm-12 form-container'
            ),
        )

    def clean(self):
        if self.cleaned_data:
            parameter = self.cleaned_data['parameter']
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


def odd_number_validator(value):
    if (value % 2 == 0):
        raise forms.ValidationError(u'Value must be odd', code='ray_kmer_even_input')


def strict_genome_to_taxon_validator(file):
    if file.name != "Genome-to-Taxon.tsv":
        raise forms.ValidationError(u'Filename must be Genome-to-Taxon.tsv',
                                    code="ray_taxo_genome_to_taxon_invalid_name")


def strict_tree_of_life_edges_validator(file):
    if file.name != "TreeOfLife-Edges.tsv":
        raise forms.ValidationError(u'Filename must be TreeOfLife-Edges.tsv',
                                    code="ray_taxo_tree_of_life_edges_invalid_name")


def strict_taxon_names_validator(file):
    if file.name != "Taxon-Names.tsv":
        raise forms.ValidationError(u'Filename must be Taxon-Names.tsv', code='ray_taxo_taxon_names_invalid_name')


def tsv_file_validator(file):  # to replace strict validators in the case it must be not strict
    ext = os.path.splitext(file.name)[1]
    if ext.lower() != '.tsv':
        raise forms.ValidationError(u'Only .tsv file accepted', code="ray_taxo_not_tsv")


def txt_file_validator(file):
    ext = os.path.splitext(file.name)[1]
    if ext.lower() != '.txt':
        raise forms.ValidationError(u'Only .txt file accepted', code="ray_gene_ontology_not_txt")


class OtherParameterForm(forms.Form):
    param_kmer = forms.BooleanField(initial=False, required=False, label="-k")
    # todo: verify min_value for kmer_length, 32 is default max if not specified in compilation
    # source: http://blog.gmane.org/gmane.science.biology.ray-genome-assembler/month=20121101
    subparam_kmer_length = forms.IntegerField(initial=21, validators=[odd_number_validator], max_value=32, min_value=1,
                                              required=False, label="",
                                              help_text="default value: 21. Value must be odd.")

    # Ray surveyor options See Documentation/Ray-Surveyor.md
    param_run_surveyor = forms.BooleanField(initial=False, required=False, label="-run-surveyor",
                                            help_text="Runs Ray Surveyor to compare samples.")
    param_read_sample_graph = forms.BooleanField(initial=False, required=False, label='-read-sample-graph',
                                                 help_text="Reads sample graphs (generated with -write-kmers)")  # dependent on -write-kmers parameter
    subparam_graph_files = MultiFileField(required=False, min_num=1, label="Upload graph(s)")
    # todo: sampleName = tool_activity_%d % id, sampleGraphFile = output_directory/kmers.txt

    # Assembly options are skipped because documentation says (defaults work well)
    # Distributed storage engine options are skipped due to lack of knowledge with mpi ranks

    # Biological abundances See Documentation/BiologicalAbundances.txt
    param_search = forms.BooleanField(initial=False, required=False, label='-search',
                                      help_text="Provide fasta files to be searched in the de Bruijn graph.")
    subparam_search_files = MultiFileField(min_num=1, required=False, label='Upload search files'
                                           )  # save to tool_activity_x/input/search
    param_one_color_per_file = forms.BooleanField(initial=False, required=False, label="-one-color-per-file",
                                                  help_text="Sets one color per file instead of one per sequence. For files with large numbers of sequences, using one single color per file may be more efficient.")

    # Taxonomic profiling with colored de Bruijn graphs
    # Computes and writes detailed taxonomic profiles. See Documentation/Taxonomy.txt for details.
    param_with_taxonomy = forms.BooleanField(required=False, initial=False, label='-with-taxonomy',
                                             help_text="Computes and writes detailed taxonomic profiles.")
    subparam_genome_to_taxon_file = forms.FileField(required=False, validators=[tsv_file_validator],
                                                    label="Genome-to-Taxon")
    subparam_tree_of_life_edges_file = forms.FileField(required=False, validators=[tsv_file_validator],
                                                       label="TreeOfLife-Edges")
    subparam_taxon_names_file = forms.FileField(required=False, validators=[tsv_file_validator], label="Taxon-Names")

    # Provides an ontology and annotations. See Documentation/GeneOntology.txt
    param_gene_ontology = forms.BooleanField(required=False, initial=False, label="-gene-ontology",
                                             help_text="Provides an ontology and annotations. OntologyTerms.txt is automatically fetched from geneontology.org .")
    # todo: The OntologyTerms.txt file is http://geneontology.org/ontology/obo_format_1_2/gene_ontology_ext.obo

    subparam_annotations_file = forms.FileField(required=False, validators=[txt_file_validator], label="Annotations",
                                                help_text="The annotation file must be derived from Uniprot-GOA (http://www.ebi.ac.uk/GOA/).")

    # Other outputs
    param_enable_neighbourhoods = forms.BooleanField(required=False, initial=False, label="-enable-neighbourhoods",
                                                     help_text="Computes contig neighborhoods in the de Bruijn graph")
    param_amos = forms.BooleanField(required=False, initial=False, label="-amos",
                                    help_text="Writes the AMOS file that contains read positions on contigs.")
    param_write_kmers = forms.BooleanField(required=False, initial=False, label="-write-kmers",
                                           help_text="Writes k-mer graph")
    param_graph_only = forms.BooleanField(required=False, initial=False, label="-graph-only",
                                          help_text="Exits after building graph.")
    param_write_read_markers = forms.BooleanField(required=False, initial=False, label="-write-read-markers",
                                                  help_text="Writes read markers to disk.")
    param_write_seeds = forms.BooleanField(required=False, initial=False, label="-write-seeds",
                                           help_text="Writes seed DNA sequences")
    param_write_extensions = forms.BooleanField(required=False, initial=False, label="-write-extensions",
                                                help_text="Writes extension DNA sequences")
    param_write_contig_paths = forms.BooleanField(required=False, initial=False, label="-write-contig-paths",
                                                  help_text="Writes contig paths with coverage values")
    param_write_marker_summary = forms.BooleanField(required=False, initial=False, label="-write-marker-summary",
                                                    help_text="Writes marker statistics.")

    # Memory usage options is skipped
    # Algorithm verbosity
    param_show_extension_choice = forms.BooleanField(required=False, initial=False, label="-show-extension-choice",
                                                     help_text="Shows the choice made (with other choices) during the extension.")
    param_show_ending_context = forms.BooleanField(required=False, initial=False, label="-show-ending-context",
                                                   help_text="Shows the ending context of each extension. Shows the children of the vertex where extension was too difficult.")
    param_distance_summary = forms.BooleanField(required=False, initial=False, label="-show-distance-summary",
                                                help_text="Shows summary of outer distances used for an extension path.")
    param_show_consensus = forms.BooleanField(required=False, initial=False, label="-show-consensus",
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
                    Div('param_kmer', css_class='col-xs-1'),
                    Div('subparam_kmer_length', css_class='col-xs-3'),
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
                'Algorithm verbosity',
                Div(
                    Div('param_show_extension_choice', css_class='col-xs-6'),
                    Div('param_show_ending_context', css_class='col-xs-6'),
                    Div('param_distance_summary', css_class='col-xs-6'),
                    Div('param_show_consensus', css_class='col-xs-6'),
                    css_class='row-fluid col-sm-12'
                )
            )



        )
