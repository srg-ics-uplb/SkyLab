from __future__ import unicode_literals

import os

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.validators import RegexValidator
from django.db import models
from django.utils.encoding import python_2_unicode_compatible



# @python_2_unicode_compatible
# class
def get_available_tools():
    dirs =  [(lst,lst)  for lst in os.listdir('skylab/modules') if not os.path.isfile(os.path.join('skylab/modules',lst)) and not lst.startswith("_")]
    return dirs

@python_2_unicode_compatible
class MPI_Cluster(models.Model):
    MAX_MPI_CLUSTER_SIZE = 10

    cluster_ip = models.GenericIPAddressField()

    alphanumeric = RegexValidator(r'^[0-9a-zA-Z]*$', 'Only alphanumeric characters are allowed.')
    cluster_name = models.CharField(max_length=50, unique=True, validators=[alphanumeric], help_text='This is required to be unique. e.g. chem-205-gamess-12-12345')

    CLUSTER_SIZE_CHOICES = zip(range(1, MAX_MPI_CLUSTER_SIZE+1), range(1, MAX_MPI_CLUSTER_SIZE+1))
    cluster_size = models.SmallIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(MAX_MPI_CLUSTER_SIZE)], help_text="This specifies the number of nodes in your cluster. Max = %d" % MAX_MPI_CLUSTER_SIZE)

    tool_list = get_available_tools()
    print tool_list
    supported_tool = models.CharField(choices=tool_list, max_length=100, help_text='A cluster only supports one tool in this version')
    creator_id = models.ForeignKey(User, on_delete=models.CASCADE)
    shared_to_public = models.BooleanField(default=True)

    def __str__(self):
        return self.cluster_name



# Create your models here.
# @python_2_unicode_compatible
# class Tool(Models.model):
# 	tool_name
# 	tool_description
# 	tool_usage

# 	def __str__(self):
# 		return self.tool_text

# @python_2_unicode_compatible
# class ToolActivity(Models.model):
# 	# id given
# 	user_id = models.ForeignKey(User, on_delete=models.CASCADE)
# 	tool_name = models.CharField(max_length=50)
# 	status = models.CharField(max_length=200)
# 	cluster_ip = models.CharField(max_length=16)
# 	cluster_size = models.IntegerField()
# 	# input_directory 
# 	# output_directory
# 	time_started = models.DateTimeField('time_started')
# 	time_finished = models.DateTimeField('time_finished')
