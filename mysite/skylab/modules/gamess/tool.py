import os
import re
import shlex
import shutil

from django.conf import settings

from skylab.models import ToolActivity, SkyLabFile
from skylab.modules.base_tool import P2CToolGeneric

cluster_password = "mpiuser"

class gamess_tool(P2CToolGeneric):
    def __init__(self, **kwargs):

        self.shell = kwargs.get('shell')
        self.id = kwargs.get('id')
        self.working_dir = "/mirror/tool_activity_%d" % (self.id)
        tool_activity = ToolActivity.objects.get(pk=self.id)
        tool_activity.status = "Task started"
        tool_activity.status_code = 1
        tool_activity.save()
        super(gamess_tool, self).__init__(self, **kwargs)

        pass

    def handle_input_files(self, **kwargs):
        tool_activity = ToolActivity.objects.get(pk=self.id)
        tool_activity.status = "Fetching input files"
        tool_activity.save()
        dir = "tool_activity_%d" % self.id
        x = self.shell.run(["sh", "-c", "mkdir %s" % dir])
        print (x.output)
        f = SkyLabFile.objects.get(input_files__pk=self.id)
        self.filename = os.path.splitext(f.filename)[0]
        # for f in files:
        with self.shell.open("/mirror/%s/" % dir + f.filename, "wb") as remote_file:
            with f.file as local_file:
                shutil.copyfileobj(local_file, remote_file)
            remote_file.close()

    # raise not implemented error
    def print_msg(self, msg):
        print ("Gamess (Tool Activity %d) : %s" % (self.id, msg))

    def run_tool(self, **kwargs):
        self.handle_input_files()

        exec_string = ToolActivity.objects.get(pk=self.id).exec_string

        export_path = "/mirror/gamess"
        fix = "sudo /sbin/sysctl -w kernel.shmmax=500000000"
        fix_shmmax = self.shell.spawn(shlex.split(fix), use_pty=True)
        fix_shmmax.stdin_write(cluster_password + "\n")
        fix_shmmax.wait_for_result()
        ToolActivity.objects.get(pk=self.id).status = "Running %s" % exec_string
        self.print_msg("Running %s" % exec_string)
        exec_shell = self.shell.run(["sh", "-c", "export PATH=$PATH:%s; echo $PATH; %s;" % (export_path, exec_string)],
                                    cwd=self.working_dir)
        p = re.compile("EXECUTION\sOF\sGAMESS\sTERMINATED\s(?P<exit_status>\S+)")
        m = p.search(exec_shell.output)
        print (exec_shell.output)
        if m is not None:
            self.print_msg(m.group("exit_status"))

            p = re.compile("ERROR,\s(?P<error_msg>.+)")
            m = p.search(exec_shell.output)
            if m is not None:  # todo: more advanced catching
                print ("Error: %s" % m.group("error_msg"))
            # 2>&1 | tee nh3.hess.log;
            else:
                self.print_msg("Finished command execution")
                tool_activity = ToolActivity.objects.get(pk=self.id)
                tool_activity.status = "Finished command execution"
                tool_activity.status_code = 2
                tool_activity.save()
        else:
            tool_activity = ToolActivity.objects.get(pk=self.id)
            tool_activity.status = "Error! See .log file for more information"
            tool_activity.status_code = 4
            tool_activity.save()
        self.handle_output_files()

    def handle_output_files(self, **kwargs):
        tool_activity = ToolActivity.objects.get(pk=self.id)
        tool_activity.status = "Handling output files"
        tool_activity.save()
        self.print_msg("Sending output files to server")
        media_root = getattr(settings, "MEDIA_ROOT")

        remote_dir = "tool_activity_%d" % self.id
        os.makedirs(os.path.join(media_root, "%s/output" % remote_dir))
        local_dir = "%s/output/%s.log" % (remote_dir, self.filename)
        server_path = os.path.join(media_root, local_dir)
        # print "/mirror/%s/%s.log" % (remote_dir, self.filename)
        # print server_path
        with self.shell.open("/mirror/%s/%s.log" % (remote_dir, self.filename), "rb") as remote_file:
            with open(server_path, "wb") as local_file:  # transfer to media/tool_activity_%d/output
                shutil.copyfileobj(remote_file, local_file)
                local_file.close()

            remote_file.close()
        with open(server_path, "rb") as local_file:  # attach transferred file to database
            new_file = SkyLabFile.objects.create(upload_path="tool_activity_%d/output" % self.id,
                                                 filename="%s.log" % self.filename)
            new_file.file.name = local_dir
            new_file.save()
            tool_activity = ToolActivity.objects.get(pk=self.id)
            tool_activity.input_files.add(new_file)
            tool_activity.save()
            local_file.close()
        # retrieve and delete after produced scratch files
        local_dir = "%s/output/" % (remote_dir)
        server_path = os.path.join(media_root, local_dir)
        sftp = self.shell._open_sftp_client()
        remotePath = "/mirror/scr/"

        filesInRemotePath = sftp.listdir(path=remotePath)
        for file in filesInRemotePath:
            remoteFilePath = os.path.join(remotePath, file)
            localFilePath = os.path.join(server_path, file)
            sftp.get(remoteFilePath, localFilePath)
            with open(localFilePath, "rb") as local_file:
                new_file = SkyLabFile.objects.create(upload_path="tool_activity_%d/output" % self.id,
                                                     filename=file)
                new_file.file.name = localFilePath
                new_file.save()
                tool_activity = ToolActivity.objects.get(pk=self.id)
                tool_activity.output_files.add(new_file)
                tool_activity.save()
                local_file.close()
            # todo: insert code for sending file
            sftp.remove(remoteFilePath)  # delete after transfer
        sftp.close()

        tool_activity = ToolActivity.objects.get(pk=self.id)
        tool_activity.status = "Finished handling output files"
        tool_activity.save()
        self.print_msg("Output files sent")
    def changeStatus(self, status):
        pass
