import os.path
import re
import shutil
import json

from django.conf import settings

from skylab.models import ToolActivity, SkyLabFile
from skylab.modules.base_tool import P2CToolGeneric, mkdir_p

cluster_password = settings.CLUSTER_PASSWORD


class QuantumEspressoExecutable(P2CToolGeneric):
    def __init__(self, **kwargs):
        self.shell = kwargs.get('shell')
        self.id = kwargs.get('id')
        self.working_dir = "/mirror/tool_activity_%d" % self.id
        ToolActivity.objects.get(pk=self.id).change_status(status_msg="Task started", status_code=150)
        super(QuantumEspressoExecutable, self).__init__(self, **kwargs)

    def handle_input_files(self, **kwargs):
        self.shell.run(["sh", "-c", "mkdir tool_activity_%d" % self.id])
        ToolActivity.objects.get(pk=self.id).change_status(status_msg="Fetching input files", status_code=151)
        files = SkyLabFile.objects.filter(input_files__pk=self.id)
        for f in files:
            sftp = self.shell._open_sftp_client()
            mkdir_p(sftp, f.upload_path)
            sftp.putfo(f.file, f.filename)  # At this point, you are in remote_path
            sftp.close()

    # TODO: create pseudo folder. download pseudopotentials

    # raise not implemented error
    def print_msg(self, msg):
        print ("Quantum Espresso (Tool Activity %d) : %s" % (self.id, msg))

    def run_tool(self, **kwargs):
        self.handle_input_files()

        # TODO: create temp folder, create output folder
        # TMP_DIR = "tempdir", PSEUDO_DIR = "/pseudo"

        # TODO: change export path
        export_path = "/mirror/Ray-2.3.1/build"

        # TODO set env_vars
        env_vars = {"PATH": "$PATH:%s" % export_path, "TMP_DIR": "/tempdir", "PSEUDO_DIR": "/pseudo"}

        command_list = json.loads(ToolActivity.objects.get(pk=self.id).command_list)
        ToolActivity.objects.get(pk=self.id).change_status(status_msg="Executing task command", status_code=152)

        # self.print_msg("Running %s" % command_list)

        exec_shell = self.shell.run(["sh", "-c", "export PATH=$PATH:%s; echo $PATH; %s;" % (export_path, exec_string)])
        for command in command_list:
            # TODO: use .format
            # need to set TMP_DIR, PSEUDO_DIR


            exec_shell = self.shell.run(["sh", ""])
        # catch spur.results.RunProcessError
        # cwd=self.working_dir)
        print (exec_shell.output)

        self.print_msg("Finished command execution")
        ToolActivity.objects.get(pk=self.id).change_status(status_msg="Tool execution successful", status_code=153)

        self.handle_output_files()

        ToolActivity.objects.filter(pk=self.id).update(status="Task finished")

    def handle_output_files(self, **kwargs):
        ToolActivity.objects.filter(pk=self.id).update(status="Handling output files")
        self.print_msg("Sending output files to server")
        media_root = getattr(settings, "MEDIA_ROOT")

        remote_dir = "tool_activity_%d" % self.id
        os.makedirs(os.path.join(media_root, "%s/output" % remote_dir))
        output_filename = "RayOutput_%d.zip" % self.id
        server_zip_filepath = os.path.join(media_root, "%s/output/%s" % (remote_dir, output_filename))

        self.shell.run(["zip", "-r", output_filename, "output"], cwd=self.working_dir)

        with self.shell.open("/mirror/%s/%s" % (remote_dir, output_filename), "rb") as remote_file:
            with open(server_zip_filepath, "wb") as local_file:  # transfer to media/tool_activity_%d/output
                shutil.copyfileobj(remote_file, local_file)
                local_file.close()

            remote_file.close()

        with open(server_zip_filepath, "rb") as local_file:  # attach transferred file to database
            new_file = SkyLabFile.objects.create(upload_path="tool_activity_%d/output" % self.id,
                                                 filename=output_filename)
            new_file.file.name = os.path.join(new_file.upload_path, new_file.filename)
            new_file.save()
            tool_activity = ToolActivity.objects.get(pk=self.id)
            tool_activity.output_files.add(new_file)
            tool_activity.save()
            local_file.close()

        error_flag = kwargs.get("error", False)
        if error_flag:
            pass
            # TODO: delete tool_activity_folder

        ToolActivity.objects.filter(pk=self.id).update(status="Finished handling output files")
        self.print_msg("Output files sent")

    def changeStatus(self, status):
        pass
