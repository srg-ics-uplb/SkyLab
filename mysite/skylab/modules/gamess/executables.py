import json
import math
import os
import re
import stat
import time

import spur
from django.conf import settings

from skylab.models import SkyLabFile
from skylab.modules.basetool import P2CToolGeneric


class GamessExecutable(P2CToolGeneric):
    def __init__(self, **kwargs):
        super(GamessExecutable, self).__init__(**kwargs)
        self.working_dir = os.path.join(self.remote_task_dir, 'input')  # this is where the commands will be executed

    def handle_input_files(self, **kwargs):
        self.task.change_status(status_msg='Uploading input files', status_code=151)
        self.logger.debug(self.log_prefix + 'Uploading input files')

        files = SkyLabFile.objects.filter(type=1, task=self.task)  #fetch input files for this task
        self.logger.debug(self.log_prefix + 'Opening SFTP client')
        sftp = self.shell._open_sftp_client()
        self.logger.debug(self.log_prefix + 'Opened SFTP client')
        sftp.chdir(self.working_dir)  # cd /mirror/task_xx/input

        for f in files:
            self.logger.debug(self.log_prefix + "Uploading " + f.filename)
            sftp.putfo(f.file, f.filename, callback=self.sftp_file_transfer_callback)  # copy file object to cluster as f.filename in the current dir
            self.logger.debug(self.log_prefix + "Uploaded " + f.filename)
        sftp.close()
        self.logger.debug(self.log_prefix + 'Closed SFTP client')

    def run_commands(self, **kwargs):
        self.task.change_status(status_msg="Executing tool script", status_code=152)

        # when instance is restarted this settings resets : observation
        command = 'sudo /sbin/sysctl -w kernel.shmmax=500000000'
        shmax_fixer = self.shell.spawn(['sh', '-c', command], use_pty=True)
        shmax_fixer.stdin_write(settings.CLUSTER_PASSWORD + "\n")
        shmax_fixer.wait_for_result()

        command_list = json.loads(self.task.task_data)['command_list']  # load json array

        # spur update_env kwargs can only be used for constant assignments
        # thus, for environment variables must be exported via a command
        export_path = "/mirror/gamess"
        env_command = "export PATH=$PATH:{0};".format(export_path)

        error = False
        for command in command_list:
            retries = 0
            exit_loop = False

            while not exit_loop:  #try while not exit
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
                                        settings.TRY_WHILE_NOT_EXIT_MAX_TIME)  #exponential wait with max
                        self.logger.debug('Waiting {0}s until next retry'.format(wait_time))
                        time.sleep(wait_time)

            if not error:
                # parse exit status from stdout
                p = re.compile("EXECUTION\sOF\sGAMESS\sTERMINATED\s(?P<exit_status>\S+)")
                m = p.search(exec_shell.output)
                if m is not None:
                    self.logger.debug(self.log_prefix + "command exit status: " + m.group('exit_status'))

                    p = re.compile("ERROR,\s(?P<error_msg>.+)")
                    error = p.search(exec_shell.output)
                    if error is not None:
                        print (u'Error: {0:s}'.format(error.group('error_msg')))
                        error = True
                else:
                    error = True


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
                self.logger.debug(self.log_prefix + ' Received ' + remote_file)
                sftp.remove(remote_filepath)  # delete file after transfer

                # register newly transferred file as skylabfile
                new_file = SkyLabFile.objects.create(type=2, task=self.task,
                                                     render_with_jsmol=True)  # gamess output file can be rendered with jsmol
                new_file.file.name = os.path.join(os.path.join(self.task.task_dirname, 'output'),
                                                  remote_file)  # manual assignment to model filefield
                new_file.save()  # save changes

        """
        PER FILE RETRIEVAL (/mirror/scr)
        remote_path = '/mirror/scr/'
        remote_files = sftp.listdir(path=remote_path)
        for remote_file in remote_files:
            remote_filepath = os.path.join(remote_path, remote_file)
            local_filepath = os.path.join(local_path, remote_file)
            self.logger.debug(self.log_prefix + ' Retrieving ' + remote_file)
            sftp.get(remote_filepath, local_filepath)
            self.logger.debug(self.log_prefix + ' Received ' + remote_file)
            with open(local_filepath, "rb") as local_file:
                new_file = SkyLabFile.objects.create(type=2, task=self.task)
                new_file.file.name = os.path.join(new_file.upload_path, remote_file)
                new_file.save()

            sftp.remove(remote_filepath)  # delete after transfer
        """

        # retrieve then delete produced scratch files
        zip_filename = self.task.task_dirname + "-scratch_files.zip"
        local_zip_filepath = os.path.join(media_root, "%s/output/%s" % (self.task.task_dirname, zip_filename))
        remote_zip_filepath = os.path.join(settings.REMOTE_BASE_DIR, zip_filename)

        self.shell.run(["zip", "-r", zip_filename, "scr"])  # zip scr folder
        self.logger.debug(self.log_prefix + 'Downloading '+ zip_filename)
        sftp.get(remote_zip_filepath, local_zip_filepath, callback=self.sftp_file_transfer_callback)  # get remote zip
        self.logger.debug(self.log_prefix + 'Downloaded '+ zip_filename)
        sftp.remove(remote_zip_filepath)
        sftp.close()
        self.logger.debug(self.log_prefix + 'Closed SFTP client')

        # register newly transferred file as skylabfile
        new_file = SkyLabFile.objects.create(type=2, task=self.task)
        new_file.file.name = os.path.join(os.path.join(self.task.task_dirname, 'output'),
                                          zip_filename)
        new_file.save()

        # delete via ssh is faster than sftp
        self.shell.run(['sh', '-c', 'rm -rf scr/*'])  # Clear scratch directory
        self.shell.run(['rm', '-rf', self.remote_task_dir])  # Delete remote task directory

        if not self.task.status_code == 400:
            self.task.change_status(status_code=200, status_msg="Output files received. No errors encountered")
        else:
            self.task.change_status(status_code=401, status_msg="Output files received. Errors encountered")

        self.logger.info(self.log_prefix + 'Done. Output files sent')

    def run_tool(self, **kwargs):
        self.task.change_status(status_msg='Task started', status_code=150)

        additional_dirs = ['/mirror/scr']
        task_remote_subdirs = ['input', 'output']
        self.clear_or_create_dirs(additional_dirs=additional_dirs, task_remote_subdirs=task_remote_subdirs)
        self.handle_input_files()
        self.run_commands()
        self.handle_output_files()


# created for testing purposes only
class Dummy(object):
    def __init__(self):
        print ("Hello world")
