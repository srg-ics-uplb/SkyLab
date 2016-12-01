from django.conf import settings
from django.forms import ValidationError

from skylab.models import MPICluster

# use to validate form inputs

def cluster_name_unique_validator(cluster_name):
    if MPICluster.objects.filter(cluster_name=cluster_name).exists():  # exclude(status=5)
        raise ValidationError(u'Cluster with name "' + cluster_name + '" already exists',
                              code="create_existing_mpi_error")


def cluster_size_validator(value):
    current_max = get_current_max_nodes()
    if value > current_max:
        if current_max > 1:
            raise ValidationError(u'Can only create max of {0} nodes'.format(current_max),
                                  code="cluster_size_above_limit")
        else:
            raise ValidationError(u'Sorry. The system has reached the limit for max active clusters.'.format(current_max),
                                  code="cluster_size_above_limit")


def get_current_max_nodes():
    online_clusters = MPICluster.objects.exclude(status=5)
    current_instance_count = 0
    for c in online_clusters:
        current_instance_count += c.total_node_count

    return min(settings.MAX_NODES_PER_CLUSTER, settings.MAX_TOTAL_INSTANCES - current_instance_count)
