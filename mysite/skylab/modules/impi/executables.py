import json
import math
import os
import stat
import time

import spur
from django.conf import settings

from skylab.models import SkyLabFile
from skylab.modules.basetool import P2CToolGeneric


# 6, 11, 12 (segmentation fault) inherent error
# 3, 4 secondary numeric input needed
#TODO: single sftp open call
class ImpiExecutable(P2CToolGeneric):  # for multiple files with the same operations to run with
    def __init__(self, **kwargs):
        super(ImpiExecutable, self).__init__(**kwargs)
        self.working_dir = os.path.join(self.remote_task_dir, 'output')  # this is where the commands will be executed
        self.output_files = []

    def handle_input_files(self, **kwargs):
        self.task.change_status(status_msg='Uploading input files', status_code=151)
        self.logger.debug(self.log_prefix + 'Uploading input files')

        files = SkyLabFile.objects.filter(type=1, task=self.task)  # fetch input files for this task
        self.logger.debug(self.log_prefix + "Opening SFTP client")
        sftp = self.shell._open_sftp_client()
        sftp.chdir(os.path.join(self.remote_task_dir, 'input'))  # cd /mirror/task_xx/input
        self.logger.debug(self.log_prefix + "Opened SFTP client")

        for f in files:
            self.logger.debug(self.log_prefix + "Uploading " + f.filename)
            sftp.putfo(f.file, f.filename, callback=self.sftp_file_transfer_callback)  # copy file object to cluster as f.filename in the current dir
            self.logger.debug(self.log_prefix + "Uploaded " + f.filename)
        sftp.close()
        self.logger.debug(self.log_prefix + "Closed SFTP client")

    def run_commands(self, **kwargs):
        self.task.change_status(status_msg="Executing tool script", status_code=152)
        task_data = json.loads(self.task.task_data)
        command_list = task_data['command_list']  # load json array
        input_filenames = task_data['input_filenames']

        default_output_filename = 'test_out.jpg'

        export_path = "/mirror/impi"
        env_command = "export PATH=$PATH:{0};".format(export_path)

        error = False

        self.logger.debug(self.log_prefix + "Opening SFTP client")
        sftp = self.shell._open_sftp_client()  # open sftp client
        sftp.chdir(self.working_dir)  # go to working dir
        self.logger.debug(self.log_prefix + "Opened SFTP client")

        for filename in input_filenames:
            command = "impi ../input/" + filename
            retries = 0
            exit_loop = False

            while not exit_loop:  # try while not exit
                self.logger.debug(self.log_prefix + u'Running {0:s}'.format(command))
                try:
                    exec_shell = self.shell.spawn(
                        ['sh', '-c', env_command + command],  # run command with env_command
                        cwd=self.working_dir
                    )

                    for parameter in command_list:
                        exec_shell.stdin_write(str(parameter) + "\n")
                        time.sleep(3)
                    self.logger.debug(self.log_prefix + 'Running exit operation')
                    exec_shell.stdin_write('0\n')

                    # rename output file : (default output file: test_out.jpg)
                    new_output_filename = os.path.splitext(os.path.basename(filename))[0] + '_out.jpg'
                    if default_output_filename != new_output_filename:
                        sftp.rename(default_output_filename, new_output_filename)
                        self.output_files.append(new_output_filename)

                    self.logger.debug(self.log_prefix + "Finished command exec")
                    exit_loop = True  # exit loop
                except IOError as err:
                    self.logger.error(self.log_prefix + 'IOError: ' + err.message)

                except spur.RunProcessError as err:
                    if err.return_code == -1:  # no return code received
                        self.logger.error(
                            self.log_prefix + 'No response from server. Retrying command ({0})'.format(command))
                    else:
                        self.logger.error(self.log_prefix + 'RuntimeError: ' + err.message)
                        error = True  # do not retry
                        self.task.change_status(
                            status_msg='RuntimeError: ' + err.message, status_code=400)
                        exit_loop = True  # exit loop

                except spur.ssh.ConnectionError:
                    self.logger.error('Connection error. Command: ({0})'.format(command), exc_info=True)

                finally:
                    if not exit_loop:
                        retries += 1
                        wait_time = min(math.pow(2, retries),
                                        settings.TRY_WHILE_NOT_EXIT_MAX_TIME)  # exponential wait with max
                        self.logger.debug('Waiting {0}s until next retry'.format(wait_time))
                        time.sleep(wait_time)

        sftp.close()
        self.logger.debug(self.log_prefix + "Closed SFTP client")

        if error:
            self.task.change_status(
                status_msg='Task execution error! See .log file for more information', status_code=400)
        else:
            self.logger.debug(self.log_prefix + 'Finished command list execution')

            self.task.change_status(status_msg='Tool execution successful',
                                    status_code=153)

    def handle_output_files(self, **kwargs):
        self.task.change_status(status_msg='Retrieving output files', status_code=154)
        self.logger.debug(self.log_prefix + 'Sending output files to server')
        media_root = getattr(settings, "MEDIA_ROOT")

        local_dir = u'{0:s}/output/'.format(self.task.task_dirname)
        local_path = os.path.join(media_root, local_dir)  # absolute path for local dir

        self.logger.debug(self.log_prefix + "Opening SFTP client")
        sftp = self.shell._open_sftp_client()
        self.logger.debug(self.log_prefix + "Opened SFTP client")
        remote_path = os.path.join(self.remote_task_dir, 'output')
        sftp.chdir(remote_path)

        # retrieve then delete produced output files

        # hangs on this command, used workaround instead
        # remote_files = sftp.listdir()  # list dirs and files in remote path

        for remote_file in self.output_files:
            remote_filepath = os.path.join(remote_path, remote_file)
            if not stat.S_ISDIR(sftp.stat(remote_filepath).st_mode):  # if regular file

                local_filepath = os.path.join(local_path, remote_file)

                self.logger.debug(self.log_prefix + ' Retrieving ' + remote_file)
                sftp.get(remote_filepath, local_filepath, callback=self.sftp_file_transfer_callback)  # transfer file
                self.logger.debug(self.log_prefix + ' Received ' + remote_file)
                sftp.remove(remote_filepath)  # delete file after transfer

                # register newly transferred file as skylabfile
                new_file = SkyLabFile.objects.create(type=2,
                                                     task=self.task)  # gamess output file can be rendered with jsmol
                new_file.file.name = os.path.join(os.path.join(self.task.task_dirname, 'output'),
                                                  remote_file)  # manual assignment to model filefield
                new_file.save()

        sftp.close()
        self.logger.debug(self.log_prefix + "Closed SFTP client")

        self.shell.run(['rm', '-rf', self.remote_task_dir])  # Delete remote task directory
        self.logger.debug(self.log_prefix + "Deleted remote task dir")

        if not self.task.status_code == 400:
            self.task.change_status(status_code=200, status_msg="Output files received. No errors encountered")
        else:
            self.task.change_status(status_code=401, status_msg="Output files received. Errors encountered")

        self.logger.info(self.log_prefix + 'Done. Output files sent')

    def run_tool(self, **kwargs):
        self.task.change_status(status_msg='Task started', status_code=150)

        task_remote_subdirs = ['input', 'output']
        self.clear_or_create_dirs(task_remote_subdirs=task_remote_subdirs)
        self.handle_input_files()
        self.run_commands()
        self.handle_output_files()
