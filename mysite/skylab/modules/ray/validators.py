from django import forms
import os.path

def ray_file_extension_validator(file):
    # using .conf is also not supported because it does not fit with the use-case abstraction
    # export.txt, qseq.txt are not supported because of lack of documentation on their use case
    # .gz and bz2 files are not supported since compilation in p2c-tools script does not have HAVE_LIBZ=y, HAVE_LIBBZ2=y
    # valid_file_extensions = ['.fasta', '.fa', '.fasta.gz', '.fa.gz', '.fasta.bz2', '.fa.bz2', '.fastq', '.fq',
    #                          '.fastq.gz', '.fq.gz', '.fastq.bz2',
    #                          '.fq.bz2', '.sff', '.csfasta', '.csfa'
    #                          ]
    valid_file_extensions = ['.fasta', '.fa', '.fastq', '.fq',
                             '.sff', '.csfasta', '.csfa'
                             ]

    valid = False
    for ext in valid_file_extensions:
        if file.name.lower().endswith(ext):
            valid = True
            break
    if not valid:
        invalid_ext = os.path.splitext(file.name)[1]
        raise forms.ValidationError(u'%s not supported' % invalid_ext, code='invalid_filetype')


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


def multi_graph_files_validator(files):
    for file in files:
        txt_file_validator(file)


def multi_ray_files_validator(files):
    for file in files:
        ray_file_extension_validator(file)
