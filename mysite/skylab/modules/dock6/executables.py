import json
import math
import os.path
import time
import stat
import socket

import spur
from django.conf import settings

from skylab.models import SkyLabFile
from skylab.modules.basetool import P2CToolGeneric

class GridExecutable(P2CToolGeneric):
    def __init__(self, **kwargs):
        super(GridExecutable, self).__init__(**kwargs)
        self.working_dir = os.path.join(self.remote_task_dir, "workdir")  # dir where commands will be called

    def handle_input_files(self, **kwargs):
        self.task.change_status(status_msg='Uploading input files', status_code=151)
        self.logger.debug(self.log_prefix + 'Uploading input files')

        files = SkyLabFile.objects.filter(type=1, task=self.task)  # fetch input files for this task
        self.logger.debug(self.log_prefix + 'Opening SFTP client')
        sftp = self.shell._open_sftp_client()  # returns a paramiko SFTPClient instance
        sftp.get_channel().settimeout(300.0)  # set timeout for sftp operations
        self.logger.debug(self.log_prefix + "Set timeout to {0}".format(sftp.get_channel().gettimeout()))
        self.logger.debug(self.log_prefix + 'Opened SFTP client')
        sftp.chdir(self.working_dir)  # cd /mirror/task_xx/workdir

        for f in files:
            while True:
                try:
                    self.logger.debug(self.log_prefix + "Uploading " + f.filename)
                    # upload file to remote cluster
                    sftp.putfo(f.file, f.filename, callback=self.sftp_file_transfer_callback)
                    self.logger.debug(self.log_prefix + "Uploaded " + f.filename)
                    break
                except (socket.timeout, EOFError):
                    self.logger.debug(self.log_prefix + "Retrying for " + f.filename)
                    time.sleep(2)
        sftp.close()  # close sftp client
        self.logger.debug(self.log_prefix + 'Closed SFTP client')

    def run_commands(self, **kwargs):
        self.task.change_status(status_msg="Executing tool script", status_code=152)

        command_list = json.loads(self.task.task_data)['command_list']  # load json array

        # dock6 and grid does not need export
        error = False
        for command in command_list:
            retries = 0
            exit_loop = False

            while not exit_loop:  # try while not exit
                self.logger.debug(self.log_prefix + u'Running {0:s}'.format(command))
                try:
                    # export commands does not persist with spur at least
                    exec_shell = self.shell.run(
                        ['sh', '-c', command],
                        cwd=self.working_dir  # execute commands from self.working_dir
                    )

                    self.logger.debug(self.log_prefix + "Finished command exec")
                    exit_loop = True  # exit loop

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
                    if not exit_loop:  # if task will be retried
                        retries += 1
                        wait_time = min(math.pow(2, retries),
                                        settings.TRY_WHILE_NOT_EXIT_MAX_TIME)  # exponential wait with max
                        self.logger.debug('Waiting {0}s until next retry'.format(wait_time))
                        time.sleep(wait_time)

        if error:
            self.task.change_status(
                status_msg='Task execution error! See output file for more information', status_code=400)
        else:
            self.logger.debug(self.log_prefix + 'Finished command list execution')

            self.task.change_status(status_msg='Tool execution successful',
                                    status_code=153)

    def run_tool(self, **kwargs):  # main function
        self.task.change_status(status_msg='Task started', status_code=150)
        task_remote_subdirs = ['output', 'workdir']  # task subdirectories
        self.clear_or_create_dirs(task_remote_subdirs=task_remote_subdirs)  # clear or create task subdirectories
        self.handle_input_files()  # upload input files to remote cluster
        self.run_commands()  # execute tool commands
        self.handle_output_files()  # retrieve output files from remote cluster

    def handle_output_files(self, **kwargs):
        self.task.change_status(status_msg='Retrieving output files', status_code=154 if not self.task.status_code >= 400 else self.task.status_code)

        self.logger.debug(self.log_prefix + 'Sending output files to server')
        media_root = getattr(settings, "MEDIA_ROOT")

        input_files = SkyLabFile.objects.filter(type=1, task=self.task)  # more optimized instead of using related tables
        input_filenames = [file.filename for file in input_files]

        local_dir = u'{0:s}/output/'.format(self.task.task_dirname)
        local_path = os.path.join(media_root, local_dir)  # absolute path for local dir

        self.logger.debug(self.log_prefix + 'Opening SFTP client')
        sftp = self.shell._open_sftp_client()
        self.logger.debug(self.log_prefix + 'Opened SFTP client')

        remote_path = self.working_dir
        remote_files = sftp.listdir(path=remote_path)

        sftp.get_channel().settimeout(300.0)
        self.logger.debug(self.log_prefix + "Set timeout to {0}".format(sftp.get_channel().gettimeout()))


        for remote_file in remote_files:
            remote_filepath = os.path.join(remote_path, remote_file)
            if not stat.S_ISDIR(sftp.stat(remote_filepath).st_mode):  # if regular file
                if not remote_file in input_filenames:  # do not retrieve input files
                    local_filepath = os.path.join(local_path, remote_file)

                    self.logger.debug(self.log_prefix + ' Retrieving ' + remote_file)
                    sftp.get(remote_filepath, local_filepath,
                             callback=self.sftp_file_transfer_callback)  # transfer file
                    self.logger.debug(self.log_prefix + ' Received ' + remote_file)
                    # no need to remove files since parent directory (task folder) will be deleted
                    # sftp.remove(remote_filepath)  # delete file after transfer

                    # register newly transferred file as skylabfile
                    new_file = SkyLabFile.objects.create(type=2, task=self.task)  # gamess output file can be rendered with jsmol
                    new_file.file.name = os.path.join(os.path.join(self.task.task_dirname, 'output'),
                                                      remote_file)  # manual assignment to model filefield
                    new_file.save()  # save changes

        # for tool's other output files
        zip_filename = self.task.task_dirname + "-other-outputs.zip"
        local_zip_filepath = os.path.join(media_root, "%s/output/%s" % (self.task.task_dirname, zip_filename))
        remote_zip_filepath = os.path.join(self.remote_task_dir, zip_filename)

        self.shell.run(["zip", "-r", zip_filename, "output"], cwd=self.remote_task_dir)
        # self.shell.run(["zip", "-r", "-g", zip_filename, "workdir"], cwd=self.remote_task_dir)

        self.logger.debug(self.log_prefix + ' Retrieving ' + zip_filename)
        sftp.get(remote_zip_filepath, local_zip_filepath, callback=self.sftp_file_transfer_callback)  # get remote zip
        self.logger.debug(self.log_prefix + ' Received ' + zip_filename)
        sftp.close()  # close sftp client
        self.logger.debug(self.log_prefix + 'Closed SFTP client')

        with open(local_zip_filepath, "rb") as local_file:  # attach transferred file to database
            new_file = SkyLabFile.objects.create(type=2, task=self.task)
            new_file.file.name = os.path.join(os.path.join(self.task.task_dirname, 'output'),
                                              zip_filename)
            new_file.save()

        if not self.task.status_code == 400:
            self.task.change_status(status_code=200, status_msg="Output files received. No errors encountered")
        else:
            self.task.change_status(status_code=401, status_msg="Output files received. Errors encountered")

        self.logger.info(self.log_prefix + 'Done. Output files sent')

        # Delete remote task directory
        self.shell.run(['rm', '-r', self.remote_task_dir])

class Dock6Executable(GridExecutable):  # dock6 executable if implemented will exactly be the same as grid executable
    pass
