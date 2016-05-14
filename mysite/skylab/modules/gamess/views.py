import json
import os

from django.views.generic import FormView

from skylab.models import ToolActivity, SkyLabFile, MPI_Cluster
from skylab.modules.gamess.forms import use_gamess_form


class use_gamess_view(FormView):
    template_name = "modules/gamess/use_gamess.html"
    form_class = use_gamess_form

    def get_form_kwargs(self):
        # pass "user" keyword argument with the current user to your form
        kwargs = super(use_gamess_view, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return "toolactivity/%d" % self.kwargs['id']

    def form_valid(self, form):
        cluster = MPI_Cluster.objects.get(pk=self.request.POST['mpi_cluster'])
        print cluster
        filename = os.path.splitext(self.request.FILES['inp_file'].name)[0]
        exec_string = "rungms %s 01 1 2>&1 | tee %s.log" % (filename, filename)
        # exec_string = "rungms %s 01" % (filename)
        tool_activity = ToolActivity.objects.create(
            mpi_cluster=cluster, tool_name="gamess", user=self.request.user, exec_string=exec_string
        )
        self.kwargs['id'] = tool_activity.id
        new_file = SkyLabFile.objects.create(upload_path="tool_activity_%d/input" % tool_activity.id,
                                             file=self.request.FILES['inp_file'],
                                             filename=self.request.FILES['inp_file'].name)
        tool_activity.input_files.add(new_file)

        print self.request.FILES['inp_file'].name

        data = {
            "actions": "use_tool",
            "activity": tool_activity.id,
            "tool": tool_activity.tool_name,
            "executable": "gamess",
        }
        message = json.dumps(data)
        print message
        # find a way to know if thread is already running
        send_mpi_message("skylab.consumer.%d" % tool_activity.mpi_cluster.id, message)
        tool_activity.status = "Task Queued"
        return super(Use_Gamess_View, self).form_valid(form)
