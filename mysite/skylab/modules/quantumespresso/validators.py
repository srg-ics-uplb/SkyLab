from django import forms
import os.path


def in_file_extension_validator(file):
    # using .conf is also not supported because it does not fit with the use-case abstraction
    # export.txt, qseq.txt are not supported because of lack of documentation on their use case
    # .gz and bz2 files are not supported since compilation in p2c-tools script does not have HAVE_LIBZ=y, HAVE_LIBBZ2=y
    # valid_file_extensions = ['.fasta', '.fa', '.fasta.gz', '.fa.gz', '.fasta.bz2', '.fa.bz2', '.fastq', '.fq',
    #                          '.fastq.gz', '.fq.gz', '.fastq.bz2',
    #                          '.fq.bz2', '.sff', '.csfasta', '.csfa'
    #                          ]
    valid_file_extensions = ['.in']

    valid = False
    for ext in valid_file_extensions:
        if file.name.lower().endswith(ext):
            valid = True
            break
    if not valid:
        invalid_ext = os.path.splitext(file.name)[1]
        raise forms.ValidationError(u'%s not supported' % invalid_ext, code='invalid_filetype')

