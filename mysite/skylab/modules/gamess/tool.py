import re
import shlex
import shutil

from skylab.models import ToolActivity, SkyLabFile
from skylab.modules.base_tool import P2CToolGeneric

cluster_password = "mpiuser"

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
    def print_msg(self, msg):
        print "Gamess (Tool Activity %d) : %s" % (self.id, msg)

    def run_tool(self, **kwargs):
        self.handle_input_files()
        exec_string = ToolActivity.objects.get(pk=self.id).exec_string
        print exec_string
        dir = "/mirror/tool_activity_%d" % (self.id)
        print dir
        export_path = "/mirror/gamess"
        fix = "sudo /sbin/sysctl -w kernel.shmmax=500000000"
        fix_shmmax = self.shell.spawn(shlex.split(fix), use_pty=True)
        fix_shmmax.stdin_write(cluster_password + "\n")
        fix_shmmax.wait_for_result()
        self.print_msg("Running %s" % exec_string)
        exec_shell =  self.shell.run(["sh","-c","export PATH=$PATH:%s; echo $PATH; %s;" % (export_path,exec_string)], cwd=dir)
        p = re.compile("EXECUTION\sOF\sGAMESS\sTERMINATED\s(?P<exit_status>\S+)")
        m = p.search(exec_shell.output)
        print exec_shell.output
        self.print_msg(m.group("exit_status"))

        p = re.compile("ERROR,\s(?P<error_msg>.+)")
        m = p.search(exec_shell.output)
        if m is not None:   #todo: more advanced catching
            print (m.group("error_msg"))
        # 2>&1 | tee nh3.hess.log;
        self.print_msg("Finished command execution")
        #todo: run exec


    # get_input_files()
    #   run command
    #   send_output_files back to server
    # raise not

    def handle_output_files(self, **kwargs):
        pass

    def changeStatus(self, status):
        pass
