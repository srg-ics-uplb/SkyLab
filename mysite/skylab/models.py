from __future__ import unicode_literals

import os
import random
import re
import string

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible



def get_available_tools():
    module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules')
    dirs = [(lst, lst) for lst in os.listdir(module_path) if
            not os.path.isfile(os.path.join(module_path, lst)) and not lst.startswith("_")]
    return dirs


def get_sentinel_user():
    return User.objects.get_or_create(username='deleted_user')


def generate_share_key(N=5):
    """
    Generate string [A-Z0-9]{N}
    :param N:
    :return: string of capital letters and numbers with length n
    """
    while True:
        key = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(N))
        if MPICluster.objects.filter(share_key=key).exists():
            continue
        return key


@python_2_unicode_compatible
class MPICluster(models.Model):
    MAX_MPI_CLUSTER_SIZE = settings.MAX_NODES_PER_CLUSTER

    cluster_ip = models.GenericIPAddressField(null=True, default=None)
    cluster_name = models.CharField(max_length=30, unique=True)
    cluster_size = models.SmallIntegerField(default=1, validators=[MaxValueValidator(MAX_MPI_CLUSTER_SIZE)])


    share_key = models.CharField(default=generate_share_key, max_length=10)
    queued_for_deletion = models.BooleanField(default=False)
    toolsets = models.ManyToManyField("ToolSet", help_text="You can select multiple tools to activate",
                                      through='ToolActivation')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="creator", null=True)
    allowed_users = models.ManyToManyField(User, related_name="allowed_users")
    is_public = models.BooleanField(default=True)
    status = models.SmallIntegerField(default=0)

    updated = models.DateTimeField()
    created = models.DateTimeField()

    @property
    def total_node_count(self):
        return self.cluster_size + 1

    @property
    def current_simple_status_msg(self):
        status_msg = {
            0: 'Creating',
            1: 'Connecting',
            2: 'Online',
            4: 'Connection error',
            5: 'Deleted'
        }
        return status_msg.get(self.status, "Status code unknown")

    @property
    def task_queued_count(self):
        return Task.objects.filter(mpi_cluster=self.id).exclude(status_code=200).exclude(status_code=401).count()

    #     401 terminal status

    def get_absolute_url(self):
        return reverse('mpi-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return "{0} @ {1}".format(self.cluster_name, self.cluster_ip)

    def change_status(self, status):
        self.refresh_from_db()
        self.status = status
        self.save()

    def save(self, *args, **kwargs):
        # Update timestamps
        if not self.id:
            self.created = timezone.now()
        self.updated = timezone.now()
        super(MPICluster, self).save(*args, **kwargs)

@python_2_unicode_compatible
class ToolActivation(models.Model):
    mpi_cluster = models.ForeignKey(MPICluster, on_delete=models.CASCADE)
    toolset = models.ForeignKey("ToolSet", on_delete=models.CASCADE)
    # activated = models.BooleanField(default=False)
    status = models.SmallIntegerField(default=0)

    class Meta:
        unique_together = ('mpi_cluster', 'toolset')

    def __str__(self):
        return "{0} activation for {1}".format(self.toolset.display_name, self.mpi_cluster.cluster_name)

    def save(self, *args, **kwargs):
        self.mpi_cluster.updated = timezone.now()
        super(ToolActivation, self).save(*args, **kwargs)

    @property
    def current_status_msg(self):
        if self.status == 2:
            return "Activated"
        elif self.status == 1:
            return "Queued for activation"
        elif self.status == 0:
            return 'Not selected for activation'



def get_default_package_name(display_name):
    pattern = re.compile('[\W]+')
    pattern.sub('', display_name).lower()


@python_2_unicode_compatible
class ToolSet(models.Model):
    display_name = models.CharField(max_length=50, unique=True)
    p2ctool_name = models.CharField(max_length=50, unique=True)
    simple_name = models.CharField(max_length=50, unique=True, blank=True, null=True)
    package_name = models.CharField(max_length=50, )
    description = models.TextField(max_length=300, null=True, blank=True)
    source_url = models.URLField(blank=True)
    created = models.DateTimeField()

    def __str__(self):
        return self.display_name

    @property
    def short_description(self):
        return (self.description[:200] + '...') if len(self.description) > 200 else self.description

    class Meta:
        unique_together = ('display_name', 'p2ctool_name', 'package_name')
        ordering = ['display_name']

    def save(self, *args, **kwargs):
        if self.package_name is None:
            pattern = re.compile('[\W]+')
            self.package_name = pattern.sub('', self.display_name).lower()

        if self.simple_name is None:
            self.simple_name = re.sub(r'[\s_/-]', '', self.display_name.lower())

        if not self.id:
            self.created = timezone.now()


        super(ToolSet, self).save(*args, **kwargs)


# def get_default_tool_view_name(display_name):
#     return display_name + "View"
#
#
# def get_default_tool_executable_name(display_name):
#     return display_name + "Executable"

@python_2_unicode_compatible
class Tool(models.Model):
    display_name = models.CharField(max_length=50,
                                    unique=True)  # e.g. format is display_name = ToolName, executable_name=ToolNameExecutable. view_name = ToolNameExecutable
    executable_name = models.CharField(max_length=50, blank=True)  # Executable
    simple_name = models.CharField(max_length=50, blank=True)
    view_name = models.CharField(max_length=50, blank=True)
    description = models.TextField(max_length=300, default="No description provided")
    toolset = models.ForeignKey(ToolSet, on_delete=models.CASCADE, related_name='subtools')
    created = models.DateTimeField()

    @property
    def short_description(self):
        return (self.description[:200] + '...') if len(self.description) > 200 else self.description

    class Meta:
        unique_together = ('display_name', 'executable_name', 'view_name', 'simple_name')
        ordering = ['display_name']


    def __str__(self):
        return self.display_name

    def save(self, *args, **kwargs):
        # if self.simple_name is None:
        #     self.simple_name = self.display_name.lower().replace(' ','')

        if not self.id:  # on instance created
            self.created = timezone.now()
            # if not self.simple_name:
            #     self.simple_name = re.sub(r'\s+|\_+','-',self.display_name).lower()

        super(Tool, self).save(*args, **kwargs)

        # @property
        # def simple_name(self):
        #     return self.display_name.lower().replace(' ', '-')

def get_sentinel_mpi():
    return MPICluster.objects.get_or_create(cluster_name="deleted cluster", defaults={'status': 5})[0]


@python_2_unicode_compatible
class Task(models.Model):
    priority = models.PositiveSmallIntegerField(default=3)  # 1=(reserved) p2c tool activate, 2=high, 3=normal
    task_data = models.TextField(max_length=500, blank=True)
    # additional_info = models.CharField(max_length=500, blank=True)
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    mpi_cluster = models.ForeignKey(MPICluster, on_delete=models.CASCADE, null=True)
    status_msg = models.TextField(default="Task Created", max_length=300)
    status_code = models.SmallIntegerField(default=0)

    updated = models.DateTimeField()
    created = models.DateTimeField()

    def __str__(self):
        return "Task {0} {1}@{2}".format(self.id,self.tool.display_name, self.mpi_cluster.cluster_name)

    def save(self, *args, **kwargs):
        # Update timestamps
        created = False
        if not self.id:
            created = True
            self.created = timezone.now()

        self.updated = timezone.now()

        # create toolactivation if does not exist
        ToolActivation.objects.update_or_create(mpi_cluster_id=self.mpi_cluster_id, toolset_id=self.tool.toolset_id,
                                             defaults={'status': 1})
        super(Task, self).save(*args, **kwargs)

        # placed below super since instance does not have pk until saved
        # this code results to a bug .. super().save probably triggers post_save instead of the triggering after the whole function
        # if created:
        #     # Create tasklog stating task is created
        #     self.change_status(status_code=100, status_msg="Task created")

    @property
    def simple_status_msg(self):
        status_msgs = {
            000: "Unknown",
            100: "Initializing",
            101: "Queued",
            150: "Started",
            151: "Processing",
            152: "Processing",
            153: "Processing",
            154: "Processing",
            200: "Success",
            400: "Error",
            401: "Error",
            500: "Error",
        }

        return status_msgs.get(self.status_code, "Status code %d not recognized" % self.status_code)

    def change_status(self, **kwargs):
        status_code = kwargs.get('status_code', self.status_code)
        status_msg = kwargs.get('status_msg')
        self.status_code = status_code
        self.status_msg = self.simple_status_msg
        self.save()
        TaskLog.objects.create(status_code=self.status_code, status_msg=self.status_msg, task=self)

    @property
    def task_dirname(self):
        return 'task_{0}'.format(self.id)

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

    @property
    def completion_rate(self):
        status_code = self.status_code
        completion_rates = {
            000: 0,
            100: 0,
            101: 5,
            150: 10,
            151: 20,
            152: 40,
            153: 60,
            154: 80,
            200: 100,
            400: 90,
            401: 100,
            500: 100,
        }
        return completion_rates.get(status_code, 0)

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

    def get_output_image_files_urls(self):
        output_images_urls = []

        for f in self.output_files.all():
            ext = os.path.splitext(f.filename)[1]
            if ext.lower() in ['.jpg', '.jpeg', '.bmp', '.gif', '.png']:
                output_images_urls.append(
                    {
                        'url': f.get_direct_url(),
                        'filename': f.filename
                    }
                )
        return output_images_urls

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
        if self.files.filter(render_with_jsmol=True).exists():
            output_files = self.output_files.filter(render_with_jsmol=True)
            for f in output_files:
                jsmol_files_absolute_uris.append(
                    {"uri": request.build_absolute_uri(reverse('skylab_file_url',
                                                               kwargs={"task_id": self.id,
                                                                       "type": "output", "filename": f.filename})),
                     "filename": f.filename}
                )

            input_files = self.input_files.filter(render_with_jsmol=True)
            for f in input_files:
                jsmol_files_absolute_uris.append(
                    {"uri": request.build_absolute_uri(reverse('skylab_file_url',
                                                               kwargs={"task_id": self.id,
                                                                       "type": "input", "filename": f.filename})),
                     "filename": f.filename}
                )

        return jsmol_files_absolute_uris



def get_upload_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    upload_path = instance.upload_path
    return 'task_{0}/{1}/{2}'.format(instance.task_id, upload_path, filename)

@python_2_unicode_compatible
class SkyLabFile(models.Model):
    type = models.PositiveSmallIntegerField()  # 1=input, 2=output
    upload_path = models.CharField(max_length=200, blank=True)
    file = models.FileField(upload_to=get_upload_path, blank=True)
    filename = models.CharField(max_length=200)
    render_with_jsmol = models.BooleanField(default=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="files")

    # @property
    # def filename(self):
    #     return os.path.basename(self.file.name)


    def __str__(self):
        return str(self.filename)

    def get_direct_url(self):
        return reverse('skylab_file_url',
                       kwargs={'task_id': self.task_id, 'type': 'output' if self.type == 2 else 'input',
                               'filename': self.filename})

    def save(self, *args, **kwargs):
        if not self.upload_path:
            self.upload_path = "input" if self.type == 1 else "output"
        if self.file:
            self.filename = os.path.basename(self.file.name)
            if os.path.splitext(self.filename)[1].lower() in settings.JSMOL_SUPPORTED_FILE_EXT:
                self.render_with_jsmol = True

        if not self.id: #on create check if already exists
            try:
                obj = SkyLabFile.objects.get(filename=self.filename, upload_path=self.upload_path, task_id=self.task_id, type=self.type)
                super(SkyLabFile, obj).save(*args, **kwargs)
                return
            except SkyLabFile.DoesNotExist:
                pass #No duplicates


        super(SkyLabFile, self).save(*args, **kwargs)

@python_2_unicode_compatible
class TaskLog(models.Model):
    status_code = models.PositiveSmallIntegerField()
    status_msg = models.TextField(max_length=300)
    timestamp = models.DateTimeField()
    task = models.ForeignKey(Task, on_delete=models.CASCADE)


    def __str__(self):
        return "Log for Task {1} Date : {2}".format(self.task_id, self.task_id, self.timestamp.ctime())

    def save(self, *args, **kwargs):
        # django.utils.timezone is more reliable vs datetime.datetime.now()
        # reference : http://stackoverflow.com/questions/1737017/django-auto-now-and-auto-now-add
        self.task.updated = timezone.now()
        self.timestamp = timezone.now()
        super(TaskLog, self).save(*args, **kwargs)
