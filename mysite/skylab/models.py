from __future__ import unicode_literals

import os
import re

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible


def get_available_tools():  # TODO: get file __path__
    module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules')
    dirs = [(lst, lst) for lst in os.listdir(module_path) if
            not os.path.isfile(os.path.join(module_path, lst)) and not lst.startswith("_")]
    return dirs


def get_sentinel_user():
    return User.objects.get_or_create(username='deleted_user')[0]

@python_2_unicode_compatible
class MPICluster(models.Model):
    MAX_MPI_CLUSTER_SIZE = settings.MAX_NODES_PER_CLUSTER
    # TODO: current can be lower than set MAX

    cluster_ip = models.GenericIPAddressField(null=True, default=None)
    cluster_name = models.CharField(max_length=50, unique=True)
    cluster_size = models.SmallIntegerField(default=1)

    # tool_list = get_available_tools()CharField
    # print tool_list
    queued_for_deletion = models.BooleanField(default=False)
    toolsets = models.ManyToManyField("ToolSet", help_text="You can select multiple tools to activate",
                                      through='ToolActivation')
    creator = models.ForeignKey(User, on_delete=models.SET(get_sentinel_user), related_name="created_mpi")
    allowed_users = models.ForeignKey(User, on_delete=models.SET(get_sentinel_user), null=True,
                                      related_name="accessible_mpi")
    is_public = models.BooleanField(default=True)
    status = models.SmallIntegerField(default=0)

    updated = models.DateTimeField(auto_now=True, auto_now_add=False)
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=True)

    def get_absolute_url(self):
        return reverse('mpi-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.cluster_name

    def change_status(self, status):
        self.status = status
        self.save()


class ToolActivation(models.Model):
    mpi_cluster = models.ForeignKey(MPICluster, on_delete=models.CASCADE)
    toolset = models.ForeignKey("ToolSet", on_delete=models.CASCADE)
    activated = models.BooleanField(default=False)


def get_upload_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return '{0}/{1}'.format(instance.upload_path, filename)


def get_default_package_name(display_name):
    pattern = re.compile('[\W]+')
    pattern.sub('', display_name).lower()


@python_2_unicode_compatible
class ToolSet(models.Model):
    display_name = models.CharField(max_length=50, unique=True)
    p2ctool_name = models.CharField(max_length=50, unique=True)
    package_name = models.CharField(max_length=50, default=None, unique=True, blank=True)
    description = models.CharField(max_length=300, null=True, blank=True)
    source_url = models.URLField(blank=True)

    def __str__(self):
        return self.display_name

    def save(self, *args, **kwargs):
        if self.package_name is None:
            pattern = re.compile('[\W]+')
            self.package_name = pattern.sub('', self.package_name).lower()

        super(ToolSet, self).save(*args, **kwargs)


def get_default_tool_view_name(display_name):
    return display_name + "View"


def get_default_tool_executable_name(display_name):
    return display_name + "Executable"

@python_2_unicode_compatible
class Tool(models.Model):
    display_name = models.CharField(max_length=50,
                                    unique=True)  # e.g. format is display_name = ToolName, executable_name=ToolNameExecutable. view_name = ToolNameExecutable
    executable_name = models.CharField(max_length=50, blank=True)  # Executable
    view_name = models.CharField(max_length=50, blank=True)
    description = models.CharField(max_length=300, null=True, blank=True)
    toolset = models.ForeignKey(ToolSet, on_delete=models.CASCADE)

    def __str__(self):
        return self.display_name

        # def save(self, *args, **kwargs):
        #     if self.executable_name is None:
        #         self.executable_name = self.display_name.replace(" ", "") + "Executable"
        #     if self.view_name is None:
        #         self.view_name = self.display_name.replace(" ", "") + "View"
        #     super(Tool, self).save(*args, **kwargs)


def get_sentinel_mpi():
    return MPICluster.objects.get_or_create(cluster_name="deleted cluster")[0]


@python_2_unicode_compatible
class Task(models.Model):
    type = models.PositiveSmallIntegerField(default=2)  # 1=p2c tool activate, 2=tool, 3=mpi_delete
    command_list = models.CharField(max_length=500, blank=True)
    additional_info = models.CharField(max_length=500, blank=True)
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    mpi_cluster = models.ForeignKey(MPICluster, on_delete=models.SET(get_sentinel_mpi), null=True)
    # status_msg = models.CharField(default="Task Created", max_length=200)
    # status_code = models.SmallIntegerField(default=0)


    # updated = models.DateTimeField(auto_now=True, auto_now_add=False)
    # timestamp = models.DateTimeField(auto_now=False, auto_now_add=True)

    def __str__(self):
        return str(self.id)

    @staticmethod
    def get_default_status_msg(status_code):
        status_msgs = {
            000: "Unknown",
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

        status_code = kwargs.get('status_code', 000)
        status_msg = kwargs.get('status_msg', self.get_default_status_msg(status_code))
        TaskLog.objects.create(status_code=status_code, status_msg=status_msg, task=self)

    @property
    def output_files(self):
        return self.files.filter(type=2)

    @property
    def input_files(self):
        return self.files.filter(type=1)

    # workaround for accessing all logs in template
    @property
    def logs(self):
        return self.tasklog_set.all()

    # workaround for accessing latest log from template
    @property
    def latest_log(self):
        return self.tasklog_set.latest('timestamp')

    @property
    def jsmol_output_files(self):
        return self.output_files.filter(render_with_jsmol=True)

    @property
    def jsmol_input_files(self):
        return self.input_files.filter(render_with_jsmol=True)

    def get_output_files_urls(self):
        output_files_urls_dict = []
        for f in self.output_files.all():
            output_files_urls_dict.append({'url': reverse('skylab_file_url',
                                                          kwargs={'task_id': self.id, 'type': 'output',
                                                                  'filename': f.filename}),
                                           'filename': f.filename})

        return output_files_urls_dict

    def get_dict_jsmol_files_uris(self, request):
        jsmol_files_absolute_uris = []
        output_files = self.output_files.filter(render_with_jsmol=True)
        for f in output_files:
            jsmol_files_absolute_uris.append(
                {"uri": request.build_absolute_uri(reverse('jsmol_file_url',
                                                           kwargs={"task_id": self.id,
                                                                   "type": "output", "filename": f.filename})),
                 "filename": f.filename}
            )

        input_files = self.input_files.filter(render_with_jsmol=True)
        for f in input_files:
            jsmol_files_absolute_uris.append(
                {"uri": request.build_absolute_uri(reverse('jsmol_file_url',
                                                           kwargs={"task_id": self.id,
                                                                   "type": "input", "filename": f.filename})),
                 "filename": f.filename}
            )

        return jsmol_files_absolute_uris

@python_2_unicode_compatible
class SkyLabFile(models.Model):
    type = models.PositiveSmallIntegerField()  # 1=input, 2=output
    upload_path = models.CharField(max_length=200)
    file = models.FileField(upload_to=get_upload_path, blank=True)
    filename = models.CharField(max_length=200)
    render_with_jsmol = models.BooleanField(default=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="files")

    def __str__(self):
        return self.filename


@python_2_unicode_compatible
class TaskLog(models.Model):
    status_code = models.PositiveSmallIntegerField()
    status_msg = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, blank=True)

    @property
    def __str__(self):
        return "task-{0}_log_{1}".format(self.task_id, self.timestamp.ctime())



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




