# Register your models here.
from django.contrib import admin

from skylab.models import ToolSet, Task, TaskLog, MPICluster, ToolActivation, Tool, SkyLabFile

admin.site.register(ToolSet)
admin.site.register(Task)
admin.site.register(TaskLog)
admin.site.register(MPICluster)
admin.site.register(ToolActivation)
admin.site.register(Tool)
admin.site.register(SkyLabFile)
