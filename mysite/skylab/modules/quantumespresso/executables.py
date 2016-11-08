import json
import math
import os.path
import stat
import time

import spur
from django.conf import settings

from skylab.models import SkyLabFile
from skylab.modules.basetool import P2CToolGeneric


# current implementation installs via apt-get install quantum-espresso
class QuantumEspressoExecutable(P2CToolGeneric):
    def __init__(self, **kwargs):
        super(QuantumEspressoExecutable, self).__init__(**kwargs)
        self.pseudo_dir = os.path.join(self.remote_task_dir, 'pseudodir')
        self.tmp_dir = os.path.join(self.remote_task_dir, 'tempdir')
        self.network_pseudo_download_url = "http://www.quantum-espresso.org/wp-content/uploads/upf_files/"
        # suggestion is to download all pseudopotentials and host them in a webserver for faster retrieval

    def handle_input_files(self, **kwargs):
        self.task.change_status(status_msg='Uploading input files', status_code=151)
        self.logger.debug(self.log_prefix + 'Uploading input files')

        files = SkyLabFile.objects.filter(type=1, task=self.task)  # fetch input files for this task
        self.logger.debug(self.log_prefix + 'Opening SFTP client')
        sftp = self.shell._open_sftp_client()
        self.logger.debug(self.log_prefix + 'Opened SFTP client')
        sftp.chdir(os.path.join(self.remote_task_dir, 'input'))  # cd /mirror/task_xx/input

        for f in files:
            self.logger.debug(self.log_prefix + "Uploading " + f.filename)
            sftp.putfo(f.file, f.filename, callback=self.sftp_file_transfer_callback)  # copy file object to cluster as f.filename in the current dir
            self.logger.debug(self.log_prefix + "Uploaded " + f.filename)


        pseudopotentials = json.loads(self.task.task_data).get("pseudopotentials", None)
        if pseudopotentials:
            self.logger.debug(self.log_prefix + 'Downloading pseudopotentials')
            # pseudopotential_urls = []

            command = 'curl '
            for pseudo_file in pseudopotentials:
                url = os.path.join(self.network_pseudo_download_url, pseudo_file)
                # pseudopotential_urls.append(url)
                command += '-O ' + url
                self.logger.debug(self.log_prefix + 'Downloading '+ url)
                self.shell.run(["sh","-c", command], cwd=self.pseudo_dir)
                self.logger.debug(self.log_prefix + 'Downloaded file')


            # command = 'printf "{urls}" > urls.txt && wget -i urls.txt'.format(urls='\n'.join(pseudopotential_urls))
            # self.logger.debug(self.log_prefix + 'Command: ' + command)
            # download_shell = self.shell.run(["sh", "-c", command], cwd=self.pseudo_dir)
            # self.logger.debug(self.log_prefix + download_shell.output)
            self.logger.debug(self.log_prefix + 'Downloaded pseudopotentials')

        sftp.close()
        self.logger.debug(self.log_prefix + 'Closed SFTP client')

    def run_commands(self, **kwargs):
        # change export path QE will be installed via p2c-tools
        # export_path = None
        # export_path = "/mirror/espresso-5.4.0/bin"

        env_vars = {"TMP_DIR": self.tmp_dir, "PSEUDO_DIR": self.pseudo_dir, "LC_ALL": 'C'}
        # if export_path:
        #     env_vars['PATH'] = '$PATH:{0}'.format(export_path)

        env_var_command_template = 'export {key}={value};'
        env_command = ''
        for key, value in env_vars.iteritems():
            env_command += env_var_command_template.format(key=key, value=value)

        task_data = json.loads(self.task.task_data)

        command_list = task_data['command_list']

        error = False
        for command in command_list:
            retries = 0
            exit_loop = False

            while not exit_loop:  # try while not exit
                self.logger.debug(self.log_prefix + u'Running {0:s}'.format(command))
                try:
                    # export commands does not persist with spur at least
                    exec_shell = self.shell.run(
                        ['sh', '-c', env_command + command],  # run command with env_command
                        cwd=self.working_dir  # run at remote task dir
                    )

                    # clear tempdir
                    command = 'rm -rf *'
                    exec_shell = self.shell.run(
                        ['sh', '-c', env_command + command],  # run command with env_command
                        cwd=self.tmp_dir  # run at remote task dir
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
                                        settings.TRY_WHILE_NOT_EXIT_MAX_TIME)  # exponential wait with max
                        self.logger.debug('Waiting {0}s until next retry'.format(wait_time))
                        time.sleep(wait_time)

            if error:
                self.task.change_status(
                    status_msg='Task execution error! See .log file for more information', status_code=400)
            else:
                self.logger.debug(self.log_prefix + 'Finished command list execution')

                self.task.change_status(status_msg='Tool execution successful',
                                        status_code=153)

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
        for remote_file in remote_files:
            remote_filepath = os.path.join(remote_path, remote_file)
            if not stat.S_ISDIR(sftp.stat(remote_filepath).st_mode):  # if regular file

                local_filepath = os.path.join(local_path, remote_file)

                self.logger.debug(self.log_prefix + ' Retrieving ' + remote_file)
                sftp.get(remote_filepath, local_filepath, callback=self.sftp_file_transfer_callback)  # transfer file
                self.logger.debug(self.log_prefix + ' Received ' + remote_file)
                sftp.remove(remote_filepath)  # delete file after transfer

                # register newly transferred file as skylabfile
                # at the very least pw.x output files seems to be compatible with jsmol
                new_file = SkyLabFile.objects.create(type=2, task=self.task)
                jsmol_output_files = json.loads(self.task.task_data).get('jsmol_output_files',None)
                if jsmol_output_files:
                    if remote_file in jsmol_output_files:  #if marked as jsmol compatible
                        new_file.render_with_jsmol = True
                new_file.file.name = os.path.join(os.path.join(self.task.task_dirname, 'output'),
                                                  remote_file)  # manual assignment to model filefield
                new_file.save()  # save changes

        sftp.close()
        self.logger.debug(self.log_prefix + 'Closed SFTP client')

        self.shell.run(['rm', '-rf', self.remote_task_dir])  # Delete remote task directory

        if not self.task.status_code == 400:
            self.task.change_status(status_code=200, status_msg="Output files received. No errors encountered")
        else:
            self.task.change_status(status_code=401, status_msg="Output files received. Errors encountered")

        self.logger.info(self.log_prefix + 'Done. Output files sent')

    def run_tool(self, **kwargs):
        self.task.change_status(status_msg='Task started', status_code=150)
        task_remote_subdirs = ['input', 'output', 'pseudodir', 'tempdir']
        self.clear_or_create_dirs(task_remote_subdirs=task_remote_subdirs)
        self.handle_input_files()
        self.run_commands()
        self.handle_output_files()

