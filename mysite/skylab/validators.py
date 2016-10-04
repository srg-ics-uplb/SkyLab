from django.conf import settings
from django.forms import ValidationError

from skylab.models import MPICluster


def cluster_name_unique_validator(cluster_name):
    if MPICluster.objects.filter(cluster_name=cluster_name).exists():
        raise ValidationError(u'Cluster name already exists',
                              code="create_existing_mpi_error")


def cluster_size_validator(value):
    current_max = get_current_max_nodes()
    if value > current_max:
        raise ValidationError(u'Can only create max of {0} nodes'.format(current_max),
                              code="create_existing_mpi_error")


def get_current_max_nodes():
    online_clusters = MPICluster.objects.exclude(status=5)
    current_instance_count = 0
    for c in online_clusters:
        current_instance_count += c.cluster_size + 1

    return min(settings.MAX_NODES_PER_CLUSTER, settings.MAX_TOTAL_INSTANCES - current_instance_count)
