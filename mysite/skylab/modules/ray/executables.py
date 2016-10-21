import json
import math
import os.path
import time

import spur
from django.conf import settings

from skylab.models import SkyLabFile
from skylab.modules.basetool import P2CToolGeneric, mkdir_p


class RayExecutable(P2CToolGeneric):
    def __init__(self, **kwargs):
        super(RayExecutable, self).__init__(**kwargs)
        self.working_dir = settings.REMOTE_BASE_DIR

    def handle_input_files(self, **kwargs):
        self.task.change_status(status_msg='Uploading input files', status_code=151)
        self.logger.debug(self.log_prefix + 'Uploading input files')

        files = SkyLabFile.objects.filter(type=1, task=self.task)  # input files for this task
        sftp = self.shell._open_sftp_client()  # open sftp client
        for f in files:
            sftp.chdir(self.remote_task_dir)  # cd /mirror/task_xx
            mkdir_p(sftp, f.upload_path)  # mimics mkdir -p f.upload_path
            sftp.putfo(f.file, f.filename)  # At this point, you are f.upload_path
        sftp.close()

    def run_commands(self, **kwargs):
        self.task.change_status(status_msg="Executing tool script", status_code=152)
        command_list = json.loads(self.task.task_data)['command_list']  # load json array

        # spur update_env kwargs can only be used for constant assignments
        # thus, for environment variables must be exported via a command
        export_path = "/mirror/Ray-2.3.1/build"
        env_command = "export PATH=$PATH:{0};".format(export_path)

        error = False
        for command in command_list:
            retries = 0
            exit_loop = False

            while not exit_loop:
                self.logger.debug(self.log_prefix + u'Running {0:s}'.format(command))
                try:
                    # export commands does not persist with spur at least
                    exec_shell = self.shell.run(
                        ['sh', '-c', env_command + command],  #run command with env_command
                        cwd=self.working_dir
                    )

                    self.logger.debug(self.log_prefix + "Finished command exec")
                    exit_loop = True  # exit loop

                except spur.RunProcessError as err:
                    if err.return_code == -1:  # no return code received
                        self.logger.error(
                            self.log_prefix + 'No response from server. Retrying command ({0})'.format(command))
                    else:
                        self.logger.error(self.log_prefix + 'RuntimeError: ' + err.message)
                        error = True
                        self.task.change_status(
                            status_msg='RuntimeError: ' + err.message, status_code=400)
                        exit_loop = True  # exit loop

                except spur.ssh.ConnectionError:
                    self.logger.error('Connection error. Command: ({0})'.format(command), exc_info=True)
                finally:
                    if not exit_loop:
                        retries += 1
                        wait_time = min(math.pow(2, retries), settings.TRY_WHILE_NOT_EXIT_MAX_TIME)
                        self.logger.debug('Waiting {0}s until next retry'.format(wait_time))
                        time.sleep(wait_time)

        if not error:
            self.logger.debug(self.log_prefix + 'Finished command list execution')

            self.task.change_status(status_msg='Tool execution successful',
                                    status_code=153)

    def handle_output_files(self, **kwargs):
        self.task.change_status(status_msg='Retrieving output files', status_code=154)
        self.logger.debug(self.log_prefix + 'Sending output files to server')
        media_root = getattr(settings, "MEDIA_ROOT")

        zip_filename = self.task.task_dirname + "-output.zip"
        local_zip_filepath = os.path.join(media_root, "%s/output/%s" % (self.task.task_dirname, zip_filename))
        remote_zip_filepath = os.path.join(self.remote_task_dir, zip_filename)

        self.shell.run(["zip", "-r", zip_filename, "output"], cwd=self.remote_task_dir)

        sftp = self.shell._open_sftp_client()
        sftp.get(remote_zip_filepath, local_zip_filepath)  # get remote zip
        sftp.close()

        # attach transferred file to database
        new_file = SkyLabFile.objects.create(type=2, task=self.task)
        new_file.file.name = os.path.join(os.path.join(self.task.task_dirname, 'output'),
                                          zip_filename)
        new_file.save()

        self.shell.run(['rm', '-rf', self.remote_task_dir])  # Delete remote task directory

        if not self.task.status_code == 400:
            self.task.change_status(status_code=200, status_msg="Output files received. No errors encountered")
        else:
            self.task.change_status(status_code=401, status_msg="Output files received. Errors encountered")

        self.logger.info(self.log_prefix + 'Done. Output files sent')

    def run_tool(self, **kwargs):  # the whole task process
        self.task.change_status(status_msg='Task started', status_code=150)
        self.handle_input_files()
        self.clear_or_create_dirs(task_remote_subdirs=['input', 'output'])
        self.run_commands()
        self.handle_output_files()
