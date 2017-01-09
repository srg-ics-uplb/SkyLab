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


# Executable class for running autodock4 tasks
class Autodock4Executable(P2CToolGeneric):
    def __init__(self, **kwargs):
        super(Autodock4Executable, self).__init__(**kwargs)
        self.working_dir = os.path.join(self.remote_task_dir, 'workdir')  # directory where commands will be executed
        # self.input_upload_dir = self.working_dir

    # this function uploads input files to the remote cluster
    def handle_input_files(self, **kwargs):

        self.task.change_status(status_msg='Uploading input files', status_code=151)
        self.logger.debug(self.log_prefix + 'Uploading input files')
        files = self.task.files.filter(type=1)  # query task input files

        self.logger.debug(self.log_prefix + 'Opening SFTP client')
        sftp = self.shell._open_sftp_client()  # returns an instance of paramiko's SFTPClient
        self.logger.debug(self.log_prefix + 'Opened SFTP client')

        sftp.get_channel().settimeout(300.0)  # timeout for sftp read/write commands
        self.logger.debug(self.log_prefix + "Set timeout to {0}".format(sftp.get_channel().gettimeout()))

        sftp.chdir(self.working_dir)  # change directory to /mirror/task_xx/workdir
        for f in files:
            while True:
                try:
                    self.logger.debug(self.log_prefix + "Uploading " + f.filename)
                    # transfer file to remote cluster
                    sftp.putfo(f.file, f.filename, callback=self.sftp_file_transfer_callback)
                    self.logger.debug(self.log_prefix + "Uploaded " + f.filename)
                    break

                except (socket.timeout, EOFError):  # if timeout is reached before command is completed

                    self.logger.debug(self.log_prefix + "Retrying for " + f.filename)
                    time.sleep(2)

        sftp.close()  # close sftp client

    def run_commands(self, **kwargs):
        self.task.change_status(status_msg="Executing tool script", status_code=152)
        command = json.loads(self.task.task_data)['command_list'][0]   # get command by parsing json

        retries = 0
        exit_loop = False
        error = False
        while not exit_loop:
            self.logger.debug(self.log_prefix + u'Running {0:s}'.format(command))
            try:
                exec_shell = self.shell.run(
                    ['sh', '-c', command],
                    cwd=self.working_dir  # call commands from self.working_dir
                )
                self.logger.debug(self.log_prefix + exec_shell.output)
                self.logger.debug(self.log_prefix + "Finished command exec")

                exit_loop = True   # exit loop

            except spur.RunProcessError as err:
                if err.return_code == -1:   # no return code received
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
                # if command execution will be retried
                if not exit_loop:
                    retries += 1

                    wait_time = min(math.pow(2, retries), settings.TRY_WHILE_NOT_EXIT_MAX_TIME)  # exponential wait
                    self.logger.debug('Waiting {0}s until next retry'.format(wait_time))
                    time.sleep(wait_time)

        if not error:
            #on success
            self.logger.debug(self.log_prefix + 'Finished command list execution')

            self.task.change_status(status_msg='Tool execution successful',
                                    status_code=153)

    # main function
    def run_tool(self, **kwargs):
        self.task.change_status(status_msg='Task started', status_code=150)

        task_remote_subdirs = ['workdir', 'output']  # task subdirectories
        # create or clear required remote directories
        self.clear_or_create_dirs(task_remote_subdirs=task_remote_subdirs)
        self.handle_input_files()  # upload input files to remote cluster
        self.run_commands()  # run tool commands
        self.handle_output_files()  # retrieve task output files from remote cluster

    def handle_output_files(self, **kwargs):
        self.task.change_status(status_msg='Retrieving output files', status_code=154 if not self.task.status_code >= 400 else self.task.status_code)
        self.logger.debug(self.log_prefix + 'Sending output files to server')
        media_root = getattr(settings, "MEDIA_ROOT")

        local_dir = u'{0:s}/output/'.format(self.task.task_dirname)
        local_path = os.path.join(media_root, local_dir)  # absolute path for local dir

        self.logger.debug(self.log_prefix + 'Opening SFTP client')
        sftp = self.shell._open_sftp_client()
        self.logger.debug(self.log_prefix + 'Opened SFTP client')

        remote_path = os.path.join(self.remote_task_dir, 'output')

        # retrieve then delete produced output files
        remote_files = sftp.listdir(path=remote_path)  # list dirs and files in remote path

        sftp.get_channel().settimeout(180.0)
        self.logger.debug(self.log_prefix + "Set timeout to {0}".format(sftp.get_channel().gettimeout()))
        for remote_file in remote_files:
            remote_filepath = os.path.join(remote_path, remote_file)
            if not stat.S_ISDIR(sftp.stat(remote_filepath).st_mode):  # if regular file

                local_filepath = os.path.join(local_path, remote_file)
                while True:
                    try:
                        self.logger.debug(self.log_prefix + ' Retrieving ' + remote_file)
                        # transfer file
                        sftp.get(remote_filepath, local_filepath, callback=self.sftp_file_transfer_callback)
                        self.logger.debug(self.log_prefix + ' Received ' + remote_file)
                        break
                    except (socket.timeout, EOFError):
                        self.logger.debug(self.log_prefix + ' Retrying for ' + remote_file)
                        time.sleep(2)

                # register newly transferred file as skylabfile
                new_file = SkyLabFile.objects.create(type=2, task=self.task)
                new_file.file.name = os.path.join(os.path.join(self.task.task_dirname, 'output'),
                                                  remote_file)  # manual assignment to model filefield
                new_file.save()  # save changes

        sftp.close()  # close sftp client
        self.logger.debug(self.log_prefix + 'Closed SFTP client')
        self.shell.run(['rm', '-rf', self.remote_task_dir])  # Delete remote task directory

        if not self.task.status_code == 400:
            self.task.change_status(status_code=200, status_msg="Output files received. No errors encountered")
        else:
            self.task.change_status(status_code=401, status_msg="Output files received. Errors encountered")

        self.logger.info(self.log_prefix + 'Done. Output files sent')



class Autogrid4Executable(P2CToolGeneric):
    def __init__(self, **kwargs):
        super(Autogrid4Executable, self).__init__(**kwargs)
        self.working_dir = os.path.join(self.remote_task_dir, 'workdir')  # directory where tool commands will be called

    def handle_input_files(self, **kwargs):
        self.task.change_status(status_msg='Uploading input files', status_code=151)
        self.logger.debug(self.log_prefix + 'Uploading input files')

        files = self.task.files.filter(type=1)  # query task input files

        self.logger.debug(self.log_prefix + 'Opening SFTP client')
        sftp = self.shell._open_sftp_client()  # returns an instance of paramiko's SFTPClient
        self.logger.debug(self.log_prefix + 'Opened SFTP client')

        sftp.get_channel().settimeout(300.0)  # timeout for sftp read/write operations
        self.logger.debug(self.log_prefix + "Set timeout to {0}".format(sftp.get_channel().gettimeout()))

        sftp.chdir(self.working_dir)  # cd /mirror/task_xx/workdir
        for f in files:
            while True:
                try:
                    self.logger.debug(self.log_prefix + "Uploading " + f.filename)
                    # upload input file to remote cluster
                    sftp.putfo(f.file, f.filename, callback=self.sftp_file_transfer_callback)
                    self.logger.debug(self.log_prefix + "Uploaded " + f.filename)
                    break
                except (socket.timeout, EOFError):  # if timeout is reached before upload is completed
                    self.logger.debug(self.log_prefix + "Retrying for " + f.filename)
                    time.sleep(2)
        sftp.close()  # close sftp client
        self.logger.debug(self.log_prefix + 'Closed SFTP client')

    def run_commands(self, **kwargs):
        self.task.change_status(status_msg="Executing tool script", status_code=152)
        command = json.loads(self.task.task_data)['command_list'][0]  # get command by parsing json string from db

        self.task.change_status(status_msg="Executing tool script", status_code=152)
        retries = 0
        exit_loop = False
        error = False

        while not exit_loop:
            self.logger.debug(self.log_prefix + u'Running {0:s}'.format(command))
            try:
                exec_shell = self.shell.run(
                    ['sh', '-c', command],
                    cwd=self.working_dir  # run commands in self.working_dir
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
                if not exit_loop: # if command execution will be retried
                    retries += 1
                    wait_time = min(math.pow(2, retries), settings.TRY_WHILE_NOT_EXIT_MAX_TIME)  # exponential wait
                    self.logger.debug('Waiting {0}s until next retry'.format(wait_time))
                    time.sleep(wait_time)

        if not error:  # on success
            self.logger.debug(self.log_prefix + 'Finished command list execution')

            self.task.change_status(status_msg='Tool execution successful',
                                    status_code=153)

    def run_tool(self, **kwargs):  # main function
        self.task.change_status(status_msg='Task started', status_code=150)

        task_remote_subdirs = ['workdir', 'output']  # task subdirectories
        # create or clear required task subdirectories
        self.clear_or_create_dirs(task_remote_subdirs=task_remote_subdirs)
        self.handle_input_files()  # upload input files to remote cluster
        self.run_commands()  # execute tool commands
        self.handle_output_files()  # retrieve output files from remote cluster

    def handle_output_files(self, **kwargs):
        self.task.change_status(status_msg='Retrieving output files', status_code=154 if not self.task.status_code >= 400 else self.task.status_code)

        self.logger.debug(self.log_prefix + 'Sending output files to server')
        media_root = getattr(settings, "MEDIA_ROOT")

        remote_dir = self.task.task_dirname

        self.logger.debug(self.log_prefix + 'Opening SFTP client')
        sftp = self.shell._open_sftp_client()  # open sftp client
        self.logger.debug(self.log_prefix + 'Opened SFTP client')

        sftp.get_channel().settimeout(300.0)  # timeout for sftp operations
        self.logger.debug(self.log_prefix + "Set timeout to {0}".format(sftp.get_channel().gettimeout()))

        remote_path = self.working_dir
        remote_files = sftp.listdir(path=remote_path)
        input_files = SkyLabFile.objects.filter(type=1, task=self.task)
        input_filenames = [file.filename for file in input_files]

        # remove input files in workdir
        for remote_file in remote_files:
            remote_filepath = os.path.join(remote_path, remote_file)
            if remote_file in input_filenames:
                sftp.remove(remote_filepath)  # delete remote file

        zip_filename = self.task.task_dirname + "-output.zip"  # output zip filename
        local_zip_filepath = os.path.join(media_root, "%s/output/%s" % (remote_dir, zip_filename))
        remote_zip_filepath = os.path.join(self.remote_task_dir, zip_filename)

        # create output zip
        self.shell.run(["zip", "-r", zip_filename, "output"], cwd=self.remote_task_dir)
        self.shell.run(["zip", "-r", "-g", zip_filename, "workdir"], cwd=self.remote_task_dir)

        while True:
            try:
                self.logger.debug(self.log_prefix + ' Retrieving ' + zip_filename)
                sftp.get(remote_zip_filepath, local_zip_filepath, callback=self.sftp_file_transfer_callback)
                self.logger.debug(self.log_prefix + ' Received ' + zip_filename)
                break
            except (socket.timeout, EOFError):
                self.logger.debug(self.log_prefix + ' Retrying for ' + zip_filename)
                time.sleep(2)

        sftp.close()  # close sftp client
        self.logger.debug(self.log_prefix + 'Closed SFTP client')

        # attach transferred file to database
        new_file = SkyLabFile.objects.create(type=2, task=self.task)
        new_file.file.name = os.path.join(os.path.join(self.task.task_dirname, 'output'),
                                          zip_filename)
        new_file.save()

        # Delete remote task directory
        self.shell.run(['rm', '-rf', self.remote_task_dir])

        if not self.task.status_code == 400:
            self.task.change_status(status_code=200, status_msg="Output files received. No errors encountered")
        else:
            self.task.change_status(status_code=401, status_msg="Output files received. Errors encountered")

        self.logger.info(self.log_prefix + 'Done. Output files sent')

