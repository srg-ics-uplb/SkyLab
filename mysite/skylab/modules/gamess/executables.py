import json
import math
import os
import re
import time

import spur
from django.conf import settings

from skylab.models import SkyLabFile
from skylab.modules.basetool import P2CToolGeneric

MAX_WAIT = settings.TRY_WHILE_NOT_EXIT_MAX_TIME

class GAMESSExecutable(P2CToolGeneric):
    # def __init__(self, **kwargs):
    # self.shell = kwargs.get('shell')
    # self.task = kwargs.get('task')
    # self.logger = kwargs.get('logger')
    # self.log_prefix = kwargs.get('log_prefix')

    # self.working_dir = os.path.join(settings.REMOTE_BASE_DIR, self.task.task_dirname)
    # super(GAMESSExecutable, self).__init__(**kwargs)

    def handle_input_files(self, **kwargs):
        self.task.change_status(status_msg='Uploading input files', status_code=151)
        self.logger.debug(self.log_prefix + 'Uploading input files')

        files = self.task.files.filter(type=1)
        sftp = self.shell._open_sftp_client()
        sftp.chdir(self.working_dir + '/input')

        for f in files:
            # mkdir_p(sftp, f.upload_path)
            self.logger.debug(self.log_prefix + "Uploading " + f.filename)
            sftp.putfo(f.file, f.filename)  # At this point, you are in remote_path
            self.logger.debug(self.log_prefix + "Uploaded " + f.filename)
        sftp.close()


    def handle_output_files(self, **kwargs):
        self.task.change_status(status_msg='Retrieving output files', status_code=154)
        self.logger.debug(self.log_prefix + 'Sending output files to server')
        media_root = settings.MEDIA_ROOT
        # TODO: zip output, extract on receive, then attach as skylabfile

        local_dir = u'{0:s}/output/'.format(self.task.task_dirname)
        local_path = os.path.join(media_root, local_dir)
        sftp = self.shell._open_sftp_client()
        remote_path = '/mirror/scr/'

        # retrieve then delete produced scratch files
        remote_files = sftp.listdir(path=remote_path)
        for remote_file in remote_files:
            remote_filepath = os.path.join(remote_path, remote_file)
            local_filepath = os.path.join(local_path, remote_file)
            self.logger.debug(self.log_prefix + ' Retrieving ' + remote_file)
            self.logger.debug(self.log_prefix + remote_filepath + local_filepath)
            sftp.get(remote_filepath, local_filepath)
            self.logger.debug(self.log_prefix + ' Received ' + remote_file)
            with open(local_filepath, "rb") as local_file:
                new_file = SkyLabFile.objects.create(type=2, task=self.task,
                                                     upload_path=u'{0}/output'.format(self.task.task_dirname),
                                                     filename=remote_file)
                new_file.file.name = os.path.join(new_file.upload_path, new_file.filename)
                new_file.save()

            sftp.remove(remote_filepath)  # delete after transfer

        remote_path = os.path.join(self.working_dir, 'output')

        # retrieve then delete produced scratch files
        remote_files = sftp.listdir(path=remote_path)
        for remote_file in remote_files:
            remote_filepath = os.path.join(remote_path, remote_file)
            local_filepath = os.path.join(local_path, remote_file)
            self.logger.debug(self.log_prefix + ' Retrieving ' + remote_file)
            self.logger.debug(self.log_prefix + remote_filepath + local_filepath)
            sftp.get(remote_filepath, local_filepath)
            self.logger.debug(self.log_prefix + ' Received ' + remote_file)
            with open(local_filepath, "rb") as local_file:
                new_file = SkyLabFile.objects.create(type=2, task=self.task,
                                                     upload_path=u'{0}/output'.format(self.task.task_dirname),
                                                     filename=remote_file)
                new_file.file.name = os.path.join(new_file.upload_path, new_file.filename)
                new_file.save()

            sftp.remove(remote_filepath)  # delete after transfer
        sftp.close()

        # delete via ssh is faster than sftp
        self.shell.run(['sh', '-c', 'rm -rf scr/*'])

        if not self.task.tasklog_set.filter(status_code=400).exists():
            self.task.change_status(status_code=200, status_msg="Output files received. No errors encountered")
        else:
            self.task.change_status(status_code=400, status_msg="Output files received. Errors encountered")

        self.logger.info(self.log_prefix + 'Done. Output files sent')

        # Delete remote working directory
        self.shell.run(['rm', '-r', self.working_dir])

    def run_tool(self, **kwargs):
        self.task.change_status(status_msg='Task started', status_code=150)

        additional_dirs = ['/mirror/scr']
        task_remote_subdirs = ['input', 'output']
        self.clear_or_create_dirs(additional_dirs=additional_dirs, task_remote_subdirs=task_remote_subdirs)
        self.handle_input_files()


        self.task.change_status(status_msg="Executing tool script", status_code=152)

        # command = 'sudo /sbin/sysctl -w kernel.shmmax=500000000'
        # shmax_fixer = self.shell.spawn(['sh', '-c', command], use_pty=True)
        # shmax_fixer.stdin_write(settings.CLUSTER_PASSWORD + "\n")
        # shmax_fixer.wait_for_result()

        command_list = []
        error = False

        files = self.task.files.filter(type=1)
        for f in files:
            filename_without_ext = os.path.splitext(f.filename)[0]

            command = "rungms {0} 01 1 2>&1 | tee ../output/{0}.log".format(filename_without_ext)
            command_list.append(command)

            retries = 0
            exit_loop = False
            export_path = '/mirror/gamess'
            env_vars = {"PATH": "$PATH:" + export_path}

            while not exit_loop:
                self.logger.debug(self.log_prefix + u'Running {0:s}'.format(command))
                #self.task.change_status(status_msg=u'Running {0:s}'.format(command), status_code=152)
                try:
                    exec_shell = self.shell.run(
                        ['sh', '-c', command],
                        cwd=self.working_dir + '/input', update_env=env_vars
                    )
                    self.logger.debug(self.log_prefix + "Finished command exec")
                    exit_loop = True  # exit loop

                except spur.RunProcessError as err:
                    if err.return_code == -1:  # no return code received
                        self.logger.error(
                            self.log_prefix + 'No response from server. Retrying command ({0})'.format(command))
                    else:
                        self.logger.error(self.log_prefix + 'RuntimeError: ' + err.stderr_output)
                        error = True
                        exit_loop = True  # exit loop

                except spur.ssh.ConnectionError:
                    self.logger.error('Connection error. Command: ({0})'.format(command), exc_info=True)
                finally:
                    if not exit_loop:
                        retries += 1
                        wait_time = min(math.pow(2, retries), MAX_WAIT)
                        self.logger.debug('Waiting {0}s until next retry'.format(wait_time))
                        time.sleep(wait_time)

            if not error:
                p = re.compile("EXECUTION\sOF\sGAMESS\sTERMINATED\s(?P<exit_status>\S+)")
                m = p.search(exec_shell.output)
                # print (exec_shell.output)
                if m is not None:
                    self.logger.debug(self.log_prefix + "command exit status: " + m.group('exit_status'))

                    p = re.compile("ERROR,\s(?P<error_msg>.+)")
                    error = p.search(exec_shell.output)
                    if error is not None:  # todo: more advanced catching
                        print (u'Error: {0:s}'.format(error.group('error_msg')))
                        error = True


                else:
                    error = True
                    # output_filename = filename_without_ext + '.log'
                    # self.retrieve_matching_task_path('output/' + output_filename)

        self.task.refresh_from_db()
        self.task.command_list = json.dumps(command_list)
        self.task.save()

        if error:
            self.task.change_status(
                status_msg='Task execution error! See .log file for more information', status_code=400)
        else:
            self.logger.debug(self.log_prefix + 'Finished command execution')

            self.task.change_status(status_msg='Tool execution successful',
                                    status_code=153)

        self.handle_output_files()


class Dummy(object):
    def __init__(self):
        print ("Hello world")
