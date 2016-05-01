import shutil

from skylab.models import ToolActivity, SkyLabFile
from skylab.modules.base_tool import P2CToolGeneric


class gamess_tool(P2CToolGeneric):
    def __init__(self, **kwargs):
        self.shell = kwargs.get('shell')
        self.id = kwargs.get('id')

        pass

    def handle_input_files(self, **kwargs):
        dir = "tool_activity_%d" % self.id
        x = self.shell.run(["sh","-c","mkdir %s" % dir])
        print x.output
        f = SkyLabFile.objects.get(toolactivity__pk=self.id)
        self.input_filename = f.filename
        # for f in files:
        with self.shell.open("/mirror/%s/" % dir + f.filename, "wb") as remote_file:
            with f.file as local_file:
                shutil.copyfileobj(local_file, remote_file)
            remote_file.close()


    # raise not implemented error

    def run_tool(self, **kwargs):
        self.handle_input_files()
        exec_string = ToolActivity.objects.get(pk=self.id).exec_string
        print exec_string
        dir = "/mirror/tool_activity_%d" % self.id
        print dir
        export_path = "/mirror/gamess"
        print self.shell.run(["sh","-c","export PATH=$PATH:%s; echo $PATH; cd %s; rungms %s 01;" % (export_path,dir,self.input_filename)]).output
        # 2>&1 | tee nh3.hess.log;

        #todo: run exec


    # get_input_files()
    #   run command
    #   send_output_files back to server
    # raise not

    def handle_output_files(self, **kwargs):
        pass

    def changeStatus(self, status):
        pass
