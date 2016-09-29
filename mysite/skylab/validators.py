from django.forms import ValidationError

from skylab.models import MPICluster


def cluster_name_unique_validator(cluster_name):
    if MPICluster.objects.filter(cluster_name=cluster_name).exists():
        raise ValidationError(u'Cluster name already exists',
                              code="create_existing_mpi_error")
