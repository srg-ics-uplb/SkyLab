import os

from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from skylab.models import SkyLabFile, Task, TaskLog


# @receiver(post_save, sender=MPICluster)
# def auto_delete_related_models_on_task_delete(sender, instance, **kwargs):
#     """"Delete related models on task delete"""
#     if instance.status == 5:
#         ToolActivation.objects.filter(mpi_cluster=instance).delete()

@receiver(post_delete, sender=Task)
def auto_delete_related_models_on_task_delete(sender, instance, **kwargs):
    """"Delete related models on task delete"""
    SkyLabFile.objects.filter(task=instance).delete()
    TaskLog.objects.filter(task=instance).delete()


# Retrieved from http: // stackoverflow.com / questions / 16041232 / django - delete - filefield
# These two auto-delete files from filesystem when they are unneeded:
@receiver(post_delete, sender=SkyLabFile)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """Deletes file from filesystem
    when corresponding `SkyLabFile` object is deleted.    """

    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)


@receiver(pre_save, sender=SkyLabFile)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """Deletes file from filesystem
    when corresponding `SkyLabFile` object is changed.
    """
    if not instance.pk:
        return False

    try:
        old_file = SkyLabFile.objects.get(pk=instance.pk).file
    except SkyLabFile.DoesNotExist:
        return False

    if old_file:
        new_file = instance.file
        if not old_file == new_file:
            if os.path.isfile(old_file.path):
                os.remove(old_file.path)
