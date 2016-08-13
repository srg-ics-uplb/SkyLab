from __future__ import unicode_literals

import os

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.validators import RegexValidator
from django.db import models
from django.utils.encoding import python_2_unicode_compatible


def get_available_tools():  # TODO: get file __path__
    module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules')
    dirs = [(lst, lst) for lst in os.listdir(module_path) if
            not os.path.isfile(os.path.join(module_path, lst)) and not lst.startswith("_")]
    return dirs

@python_2_unicode_compatible
class MPI_Cluster(models.Model):
    MAX_MPI_CLUSTER_SIZE = 10

    cluster_ip = models.GenericIPAddressField(null=True, default=None)

    cluster_name_validator = RegexValidator(r'^[a-zA-Z]+[0-9a-zA-Z\-]*$', 'Must start with a letter. Only alphanumeric characters, - are allowed.')
    cluster_name = models.CharField(max_length=50, unique=True, validators=[cluster_name_validator], help_text='This is required to be unique. e.g. chem-205-gamess-12-12345')

    CLUSTER_SIZE_CHOICES = zip(range(1, MAX_MPI_CLUSTER_SIZE+1), range(1, MAX_MPI_CLUSTER_SIZE+1))
    cluster_size = models.SmallIntegerField(default=1, choices=CLUSTER_SIZE_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(MAX_MPI_CLUSTER_SIZE)], help_text="This specifies the number of nodes in your cluster. Max = %d" % MAX_MPI_CLUSTER_SIZE)

    tool_list = get_available_tools()
    # print tool_list
    supported_tools = models.CharField(choices=tool_list, max_length=200, help_text='A cluster only supports one tool in this version')
    creator= models.ForeignKey(User, on_delete=models.CASCADE)
    shared_to_public = models.BooleanField(default=True)
    status = models.SmallIntegerField(default=0)

    updated = models.DateTimeField(auto_now=True, auto_now_add=False)
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=True)

    def get_absolute_url(self):
        return reverse('mpi-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.cluster_name

def get_upload_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return '{0}/{1}'.format(instance.upload_path, filename)

@python_2_unicode_compatible
class SkyLabFile(models.Model):
    upload_path = models.CharField(max_length=200)
    file = models.FileField(upload_to=get_upload_path, blank=True)
    filename = models.CharField(max_length=200)
    render_with_jsmol = models.BooleanField(default=False)

    def __str__(self):
        return self.filename

@python_2_unicode_compatible
class ToolActivity(models.Model):
    exec_string = models.CharField(max_length=200)
    tool_name = models.CharField(max_length=50)
    executable_name = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mpi_cluster = models.ForeignKey(MPI_Cluster, on_delete=models.SET_NULL, null=True)
    # status_msg = models.CharField(default="Task Created", max_length=200)
    # status_code = models.SmallIntegerField(default=0)
    input_files = models.ManyToManyField(SkyLabFile, related_name="input_files", blank=True)
    output_files = models.ManyToManyField(SkyLabFile, related_name="output_files", blank=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=False)
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=True)

    def __str__(self):
        return self.tool_name

    def get_default_status_msg(self, status_code):
        status_msgs = {
            100: "Initializing",
            101: "Queued",
            150: "Task started",
            151: "Uploading input files",
            152: "Executing tool script",
            153: "Tool execution successful",
            154: "Retrieving output files",
            200: "Task completed",
            400: "Task execution error",
            500: "MPI cluster connection error",
        }

        return status_msgs.get(status_code, "Status code %d not recognized" % status_code)

    def change_status(self, **kwargs):
        status_code = kwargs.get('status_code', self.logs.latest('id').status_code)
        status_msg = kwargs.get('status_msg', self.get_default_status_msg(status_code))
        Logs.objects.create(status_code=status_code, status_msg=status_msg, tool_activity=self)

    # workaround for accessing all logs in template
    @property
    def logs(self):
        return self.logs_set.all()

    # workaround for accessing latest log from template
    @property
    def latest_log(self):
        return self.logs_set.latest('timestamp')

# @python_2_unicode_compatible
# class Toolset(models.Model):
#     toolset_name = models.CharField(max_length=50)
#     description = models.CharField(max_length=300)
#
#     def __str__(self):
#         return self.toolset_name
#
# @python_2_unicode_compatible
# class Tool(models.Model):
#     tool_name = models.CharField(max_length=50)
#     view_name = models.CharField(max_length=50)
#     executable_name = models.CharField(max_length=50)
#     toolset = models.ForeignKey(Toolset, on_delete=models.CASCADE)
#     description = models.CharField(max_length=300)
#     source_url = models.URLField(max_length=100)
#     local_url = models.URLField(max_length=100)
#
#     def __str__(self):
#         return self.tool_name



@python_2_unicode_compatible
class Logs(models.Model):
    status_code = models.PositiveSmallIntegerField()
    status_msg = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=True)
    tool_activity = models.ForeignKey(ToolActivity, on_delete=models.CASCADE, blank=True)

    @property
    def __str__(self):
        return "task-{1}_log_{2}".format(self.tool_activity.id, self.timestamp.ctime())
