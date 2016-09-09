import json
import os.path
import shutil

from django.conf import settings

from skylab.models import ToolActivity, SkyLabFile
from skylab.modules.base_tool import P2CToolGeneric, mkdir_p

cluster_password = settings.CLUSTER_PASSWORD


class QuantumEspressoExecutable(P2CToolGeneric):
    def __init__(self, **kwargs):
        self.shell = kwargs.get('shell')
        self.id = kwargs.get('id')
        self.working_dir = "/mirror/tool_activity_{0}".format(self.id)
        self.pseudo_dir = self.working_dir + "/pseudo"
        self.tmp_dir = self.working_dir + "/tempdir"

        ToolActivity.objects.get(pk=self.id).change_status(status_msg="Task started", status_code=150)
        super(QuantumEspressoExecutable, self).__init__(self, **kwargs)

    def handle_input_files(self, **kwargs):
        self.shell.run(["sh", "-c", "mkdir tool_activity_{0}".format(self.id)])
        tool_activity = ToolActivity.objects.get(pk=self.id)
        tool_activity.change_status(status_msg="Fetching input files", status_code=151)
        files = SkyLabFile.objects.filter(input_files__pk=self.id)
        for f in files:
            sftp = self.shell._open_sftp_client()
            mkdir_p(sftp, f.upload_path)
            sftp.putfo(f.file, f.filename)  # At this point, you are in remote_path
            sftp.close()

        self.shell.run(["sh", "-c", "mkdir pseudo;"], cwd=self.working_dir)
        pseudopotentials = json.loads(tool_activity.additional_info).get("pseudopotentials", None)
        if pseudopotentials:
            for pseudo_file in pseudopotentials:
                pass
                # TODO: download pseudopotentials

    # raise not implemented error
    def print_msg(self, msg):
        print ('Quantum Espresso (Tool Activity {0}) : {1}'.format(self.id, msg))

    def run_tool(self, **kwargs):
        self.handle_input_files()

        ToolActivity.objects.get(pk=self.id).change_status(status_msg="Executing task command", status_code=152)
        self.shell.run(["sh", "-c", "mkdir pseudo; mkdir tempdir"], cwd=self.working_dir)
        # TMP_DIR = "tempdir", PSEUDO_DIR = "/pseudo"

        # TODO: change export path
        export_path = "/mirror/espresso-5.4.0/bin"

        # TODO set env_vars
        env_vars = {"PATH": "$PATH:{0}".format(export_path), "TMP_DIR": self.tmp_dir, "PSEUDO_DIR": self.pseudo_dir}

        command_list = json.loads(ToolActivity.objects.get(pk=self.id).command_list)


        # self.print_msg("Running %s" % command_list)

        # exec_shell = self.shell.run(["sh", "-c", "export PATH=$PATH:%s; echo $PATH; %s;" % (export_path, exec_string)])
        for command in command_list:
            exec_shell = self.shell.run(["sh", "-c", command], update_env=env_vars)
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

        remote_dir = 'tool_activity_{0}'.format(self.id)
        os.makedirs(os.path.join(media_root, '{0}/output'.format(remote_dir)))
        output_filename = 'QuantumEspressoOutput_{0}.zip'.format(self.id)
        server_zip_filepath = os.path.join(media_root, '{0}/output/{1}'.format(remote_dir, output_filename))

        self.shell.run(["zip", "-r", output_filename, "output"], cwd=self.working_dir)

        with self.shell.open("/mirror/{0}/{1}".format(remote_dir, output_filename), "rb") as remote_file:
            with open(server_zip_filepath, "wb") as local_file:  # transfer to media/tool_activity_id/output
                shutil.copyfileobj(remote_file, local_file)
                local_file.close()

            remote_file.close()

        with open(server_zip_filepath, "rb") as local_file:  # attach transferred file to database
            new_file = SkyLabFile.objects.create(upload_path='tool_activity_{0}/output'.format(self.id),
                                                 filename=output_filename)
            new_file.file.name = os.path.join(new_file.upload_path, new_file.filename)
            new_file.save()
            tool_activity = ToolActivity.objects.get(pk=self.id)
            tool_activity.output_files.add(new_file)
            tool_activity.save()
            local_file.close()

        # delete tool activity folder
        sftp = self.shell._open_sftp_client()
        sftp.rmdir('/mirror/tool_activity_{0}'.format(self.id))
        sftp.close()

        error_flag = kwargs.get("error", False)
        if not error_flag:
            ToolActivity.objects.get(pk=self.id).change_status(status_code=200, status_msg="Task Finished")
            self.print_msg("Output files sent")
            pass
            # TODO: delete tool_activity_folder
        else:
            pass

    def changeStatus(self, status):
        pass
