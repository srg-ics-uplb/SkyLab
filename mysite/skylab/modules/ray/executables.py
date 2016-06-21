import os.path
import re
import shutil

from django.conf import settings

from skylab.models import ToolActivity, SkyLabFile
from skylab.modules.base_tool import P2CToolGeneric

cluster_password = settings.CLUSTER_PASSWORD


# source: http://stackoverflow.com/questions/14819681/upload-files-using-sftp-in-python-but-create-directories-if-path-doesnt-exist
def mkdir_p(sftp, remote_directory):
    """Change to this directory, recursively making new folders if needed.
    Returns True if any folders were created."""
    if remote_directory == '/':
        # absolute path so change directory to root
        sftp.chdir('/')
        return
    if remote_directory == '':
        # top-level relative directory must exist
        return
    try:
        sftp.chdir(remote_directory)  # sub-directory exists
    except IOError:
        dirname, basename = os.path.split(remote_directory.rstrip('/'))
        mkdir_p(sftp, dirname)  # make parent directories
        sftp.mkdir(basename)  # sub-directory missing, so created it
        sftp.chdir(basename)
        return True


class RayExecutable(P2CToolGeneric):
    def __init__(self, **kwargs):
        self.shell = kwargs.get('shell')
        self.id = kwargs.get('id')
        self.working_dir = "/mirror/tool_activity_%d" % self.id
        ToolActivity.objects.filter(pk=self.id).update(status="Task started", status_code=1)
        super(RayExecutable, self).__init__(self, **kwargs)

    def handle_input_files(self, **kwargs):
        ToolActivity.objects.filter(pk=self.id).update(status="Fetching input files")
        files = SkyLabFile.objects.filter(input_files__pk=self.id)
        for f in files:
            sftp = self.shell._open_sftp_client()
            mkdir_p(sftp, f.upload_path)
            sftp.putfo(f.file, '.')  # At this point, you are in remote_path
            sftp.close()

    # raise not implemented error
    def print_msg(self, msg):
        print ("Gamess (Tool Activity %d) : %s" % (self.id, msg))

    def run_tool(self, **kwargs):
        self.handle_input_files()

        export_path = "/mirror/Ray-2.3.1/build"

        exec_string = ToolActivity.objects.get(pk=self.id).exec_string
        ToolActivity.objects.filter(pk=self.id).update(status="Executing task command")

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
                ToolActivity.objects.filter(pk=self.id).update(status="Finished command execution", status_code=2)

        else:
            ToolActivity.objects.filter(pk=self.id).update(status="Error! See .log file for more information",
                                                           status_code=4)

        self.handle_output_files()

        ToolActivity.objects.filter(pk=self.id).update(status="Task finished")

    def handle_output_files(self, **kwargs):
        ToolActivity.objects.filter(pk=self.id).update(status="Handling output files")
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
            tool_activity.output_files.add(new_file)
            tool_activity.save()
            local_file.close()
        # retrieve and delete after produced scratch files
        local_dir = "%s/output/" % remote_dir
        server_path = os.path.join(media_root, local_dir)
        sftp = self.shell._open_sftp_client()
        remote_path = "/mirror/scr/"

        remote_files = sftp.listdir(path=remote_path)
        for remote_file in remote_files:
            remote_filepath = os.path.join(remote_path, remote_file)
            local_filepath = os.path.join(server_path, remote_file)
            sftp.get(remote_filepath, local_filepath)
            with open(local_filepath, "rb") as local_file:
                new_file = SkyLabFile.objects.create(upload_path="tool_activity_%d/output" % self.id,
                                                     filename=remote_file)
                new_file.file.name = os.path.join(new_file.upload_path, new_file.filename)
                new_file.save()
                tool_activity = ToolActivity.objects.get(pk=self.id)
                tool_activity.output_files.add(new_file)
                tool_activity.save()
                local_file.close()
            # todo: insert code for sending file
            sftp.remove(remote_filepath)  # delete after transfer
        sftp.close()

        ToolActivity.objects.filter(pk=self.id).update(status="Finished handling output files")
        self.print_msg("Output files sent")

    def changeStatus(self, status):
        pass
