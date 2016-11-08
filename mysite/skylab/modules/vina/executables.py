import json
import math
import os.path
import stat
import time

import spur
from django.conf import settings

from skylab.models import SkyLabFile
from skylab.modules.basetool import P2CToolGeneric, mkdir_p


class VinaExecutable(P2CToolGeneric):
    def __init__(self, **kwargs):
        super(VinaExecutable, self).__init__(**kwargs)
        self.working_dir = '/mirror'

    def handle_input_files(self, **kwargs):
        self.task.change_status(status_msg='Uploading input files', status_code=151)
        self.logger.debug(self.log_prefix + 'Uploading input files')

        files = SkyLabFile.objects.filter(type=1, task=self.task)  # input files for this task
        self.logger.debug(self.log_prefix + 'Opening SFTP client')
        sftp = self.shell._open_sftp_client()  # open sftp client
        self.logger.debug(self.log_prefix + 'Opened SFTP client')
        for f in files:
            sftp.chdir(self.remote_task_dir)  # cd /mirror/task_xx
            mkdir_p(sftp, f.upload_path)  # mimics mkdir -p f.upload_path
            self.logger.debug(self.log_prefix + "Uploading " + f.filename)
            sftp.putfo(f.file, f.filename, callback=self.sftp_file_transfer_callback)  # copy file object to cluster as f.filename in the current dir
            self.logger.debug(self.log_prefix + "Uploaded " + f.filename)
        sftp.close()
        self.logger.debug(self.log_prefix + 'Closed SFTP client')

    def run_commands(self, **kwargs):
        self.task.change_status(status_msg="Executing tool script", status_code=152)
        command = json.loads(self.task.task_data)['command_list'][0]  # load json array

        retries = 0
        exit_loop = False
        error = False

        while not exit_loop:
            self.logger.debug(self.log_prefix + u'Running {0:s}'.format(command))
            try:
                # export commands does not persist with spur at least
                exec_shell = self.shell.run(
                    ['sh', '-c', command],
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
                    self.task.change_status(
                        status_msg='RuntimeError: ' + err.message, status_code=400)
                    error = True
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

    def run_tool(self, **kwargs):
        self.task.change_status(status_msg='Task started', status_code=150)
        self.clear_or_create_dirs(task_remote_subdirs=json.loads(self.task.task_data).get('task_remote_subdirs', None))
        self.handle_input_files()
        self.run_commands()
        self.handle_output_files()

    def handle_output_files(self, **kwargs):
        self.task.change_status(status_msg='Retrieving output files', status_code=154)
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
        for remote_file in remote_files:
            remote_filepath = os.path.join(remote_path, remote_file)
            if not stat.S_ISDIR(sftp.stat(remote_filepath).st_mode):  # if regular file

                local_filepath = os.path.join(local_path, remote_file)

                self.logger.debug(self.log_prefix + ' Retrieving ' + remote_file)
                sftp.get(remote_filepath, local_filepath, callback=self.sftp_file_transfer_callback)  # transfer file
                self.logger.debug(self.log_prefix + ' Retrieved ' + remote_file)
                sftp.remove(remote_filepath)  # delete file after transfer

                # register newly transferred file as skylabfile
                new_file = SkyLabFile.objects.create(type=2, task=self.task,
                                                     render_with_jsmol=True)  # gamess output file can be rendered with jsmol
                new_file.file.name = os.path.join(os.path.join(self.task.task_dirname, 'output'),
                                                  remote_file)  # manual assignment to model filefield
                new_file.save()  # save changes
        sftp.close()
        self.logger.debug(self.log_prefix + 'Closed SFTP client')

        # For future use. zip > send to server > extract > attach as skylabfile (render_with_jsmol=True)
        # Transfer via zip.
        # zip_filename = self.task.task_dirname + "-output.zip"
        # local_zip_filepath = os.path.join(media_root, "%s/output/%s" % (self.task.task_dirname, zip_filename))
        # remote_zip_filepath = os.path.join(self.remote_task_dir, zip_filename)
        #
        # self.shell.run(["zip", "-r", zip_filename, "output"], cwd=self.remote_task_dir)
        #
        # sftp = self.shell._open_sftp_client()
        # self.logger.debug(self.log_prefix + ' Retrieving ' + zip_filename)
        # sftp.get(remote_zip_filepath, local_zip_filepath)  # get remote zip
        # self.logger.debug(self.log_prefix + ' Received ' + zip_filename)
        # sftp.remove(remote_zip_filepath)
        # sftp.close()
        #
        # # attach transferred file to database
        # new_file = SkyLabFile.objects.create(type=2, task=self.task)
        # new_file.file.name = os.path.join(os.path.join(self.task.task_dirname, 'output'),
        #                                   zip_filename)
        # new_file.save()



        self.shell.run(['rm', '-rf', self.remote_task_dir])  # Delete remote task directory

        if not self.task.status_code == 400:
            self.task.change_status(status_code=200, status_msg="Output files received. No errors encountered")
        else:
            self.task.change_status(status_code=401, status_msg="Output files received. Errors encountered")

        self.logger.info(self.log_prefix + 'Done. Output files sent')



class VinaSplitExecutable(P2CToolGeneric):
    def __init__(self, **kwargs):
        super(VinaSplitExecutable, self).__init__(**kwargs)
        self.working_dir = os.path.join(self.remote_task_dir,
                                        'output')  # vina split outputs in the current dir where the command is executed

    def handle_input_files(self, **kwargs):
        self.task.change_status(status_msg='Uploading input files', status_code=151)
        self.logger.debug(self.log_prefix + 'Uploading input files')

        files = SkyLabFile.objects.filter(type=1, task=self.task)  # input files for this task
        self.logger.debug(self.log_prefix + 'Opening SFTP client')
        sftp = self.shell._open_sftp_client()  # open sftp client
        self.logger.debug(self.log_prefix + 'Opened SFTP client')
        sftp.chdir(os.path.join(self.remote_task_dir, "output"))  # cd /mirror/task_xx
        for f in files:
            self.logger.debug(self.log_prefix + "Uploading " + f.filename)
            sftp.putfo(f.file, f.filename, callback=self.sftp_file_transfer_callback)  # copy file object to cluster as f.filename in the current dir
            self.logger.debug(self.log_prefix + "Uploaded " + f.filename)
        sftp.close()
        self.logger.debug(self.log_prefix + 'Closed SFTP client')

    def run_commands(self, **kwargs):
        self.task.change_status(status_msg="Executing tool script", status_code=152)
        command_list = json.loads(self.task.task_data)['command_list']  # load json array

        error = False
        for command in command_list:  # todo: make vina_split view support dynamic formset
            retries = 0
            exit_loop = False

            while not exit_loop:
                self.logger.debug(self.log_prefix + u'Running {0:s}'.format(command))
                try:
                    # export commands does not persist with spur at least
                    exec_shell = self.shell.run(
                        ['sh', '-c', command],  # run command with env_command
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

        # remove input file in output directory
        self.logger.debug(self.log_prefix + 'Opening SFTP client')
        sftp = self.shell._open_sftp_client()
        self.logger.debug(self.log_prefix + 'Opened SFTP client')
        sftp.chdir(self.working_dir)
        for f in SkyLabFile.objects.filter(task=self.task, type=1):
            input_file = f.filename
            self.logger.debug(self.log_prefix + 'Removing '+ input_file + 'from working directory')
            sftp.remove(input_file)
            self.logger.debug(self.log_prefix + 'Removed ' + input_file + 'from working directory')

        local_dir = u'{0:s}/output/'.format(self.task.task_dirname)
        local_path = os.path.join(media_root, local_dir)  # absolute path for local dir

        remote_path = os.path.join(self.remote_task_dir, 'output')
        # retrieve then delete produced output files
        remote_files = sftp.listdir(path=remote_path)  # list dirs and files in remote path
        for remote_file in remote_files:
            remote_filepath = os.path.join(remote_path, remote_file)
            if not stat.S_ISDIR(sftp.stat(remote_filepath).st_mode):  # if regular file

                local_filepath = os.path.join(local_path, remote_file)

                self.logger.debug(self.log_prefix + ' Retrieving ' + remote_file)
                sftp.get(remote_filepath, local_filepath, callback=self.sftp_file_transfer_callback)  # transfer file
                self.logger.debug(self.log_prefix + ' Received ' + remote_file)
                sftp.remove(remote_filepath)  # delete file after transfer

                # register newly transferred file as skylabfile
                new_file = SkyLabFile.objects.create(type=2, task=self.task,
                                                     render_with_jsmol=True)  # gamess output file can be rendered with jsmol
                new_file.file.name = os.path.join(os.path.join(self.task.task_dirname, 'output'),
                                                  remote_file)  # manual assignment to model filefield
                new_file.save()  # save changes

        sftp.close()
        self.logger.debug(self.log_prefix + 'Closed SFTP client')

        # For future use. zip > send to server > extract > attach as skylabfile (render_with_jsmol=True)
        # Transfer via zip.
        # zip_filename = self.task.task_dirname + "-output.zip"
        # local_zip_filepath = os.path.join(media_root, "%s/output/%s" % (self.task.task_dirname, zip_filename))
        # remote_zip_filepath = os.path.join(self.remote_task_dir, zip_filename)
        #
        # self.shell.run(["zip", "-r", zip_filename, "output"], cwd=self.remote_task_dir)
        #
        # sftp = self.shell._open_sftp_client()
        # self.logger.debug(self.log_prefix + ' Retrieving ' + zip_filename)
        # sftp.get(remote_zip_filepath, local_zip_filepath)  # get remote zip
        # self.logger.debug(self.log_prefix + ' Received ' + zip_filename)
        # sftp.remove(remote_zip_filepath)
        # sftp.close()
        #
        # # attach transferred file to database
        # new_file = SkyLabFile.objects.create(type=2, task=self.task)
        # new_file.file.name = os.path.join(os.path.join(self.task.task_dirname, 'output'),
        #                                   zip_filename)
        # new_file.save()

        self.shell.run(['rm', '-rf', self.remote_task_dir])  # Delete remote task directory

        if not self.task.status_code == 400:
            self.task.change_status(status_code=200, status_msg="Output files received. No errors encountered")
        else:
            self.task.change_status(status_code=401, status_msg="Output files received. Errors encountered")

        self.logger.info(self.log_prefix + 'Done. Output files sent')

    def run_tool(self, **kwargs):  # the whole task process
        self.task.change_status(status_msg='Task started', status_code=150)
        self.clear_or_create_dirs(task_remote_subdirs=['output'])
        self.handle_input_files()
        self.run_commands()
        self.handle_output_files()
