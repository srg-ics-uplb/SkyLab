import json
import math
import os.path
import shutil
import time

import spur
from django.conf import settings

from skylab.models import Task, SkyLabFile
from skylab.modules.basetool import P2CToolGeneric, mkdir_p

cluster_password = settings.CLUSTER_PASSWORD


class AutoDock4Executable(P2CToolGeneric):
    def __init__(self, **kwargs):
        super(AutoDock4Executable, self).__init__(self, **kwargs)
        self.working_dir = os.path.join(self.remote_task_dir, 'workdir')
        self.input_upload_dir = self.working_dir

    def handle_input_files(self, **kwargs):
        self.task.change_status(status_msg='Uploading input files', status_code=151)
        self.logger.debug(self.log_prefix + 'Uploading input files')
        files = self.task.files.filter(type=1)
        sftp = self.shell._open_sftp_client()
        sftp.chdir(self.input_upload_dir)
        for f in files:
            self.logger.debug(self.log_prefix + "Uploading " + f.filename)
            sftp.putfo(f.file, f.filename)  # At this point, you are in remote_path
            self.logger.debug(self.log_prefix + "Uploaded " + f.filename)
        sftp.close()

    def run_tool(self, **kwargs):
        self.task.change_status(status_msg='Task started', status_code=150)

        task_remote_subdirs = ['workdir', 'output']
        self.clear_or_create_dirs(task_remote_subdirs=task_remote_subdirs)
        self.handle_input_files()

        self.task.change_status(status_msg="Executing tool script", status_code=152)
        command = json.loads(self.task.command_list)[0]

        retries = 0
        exit_loop = False
        error = False
        while not exit_loop:
            self.logger.debug(self.log_prefix + u'Running {0:s}'.format(command))
            try:
                exec_shell = self.shell.run(
                    ['sh', '-c', command],
                    cwd=self.working_dir
                )
                self.logger.debug(self.log_prefix + exec_shell.output)
                self.logger.debug(self.log_prefix + "Finished command exec")
                exit_loop = True  # exit loop

            except spur.RunProcessError as err:
                if err.return_code == -1:  # no return code received
                    self.logger.error(
                        self.log_prefix + 'No response from server. Retrying command ({0})'.format(command))
                else:
                    self.logger.error(self.log_prefix + 'RuntimeError: ' + err.message)
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

        if error:
            self.task.change_status(
                status_msg='Task execution error! See .log file for more information', status_code=400)
        else:
            self.logger.debug(self.log_prefix + 'Finished command list execution')

            self.task.change_status(status_msg='Tool execution successful',
                                    status_code=153)

        self.handle_output_files()

    def handle_output_files(self, **kwargs):
        self.task.change_status(status_msg='Retrieving output files', status_code=154)
        self.logger.debug(self.log_prefix + 'Sending output files to server')
        media_root = settings.MEDIA_ROOT

        remote_dir = self.task.task_dirname

        sftp = self.shell._open_sftp_client()
        remote_path = self.working_dir
        remote_files = sftp.listdir(path=remote_path)
        input_files = SkyLabFile.objects.filter(type=1, task=self.task)
        input_filenames = [file.filename for file in input_files]

        # remove input files in workdir
        for remote_file in remote_files:
            remote_filepath = os.path.join(remote_path, remote_file)
            if remote_file in input_filenames:
                sftp.remove(remote_filepath)  # delete after transfer

        zip_filename = self.task.task_dirname + "-output.zip" % self.task.id
        local_zip_filepath = os.path.join(media_root, "%s/output/%s" % (remote_dir, zip_filename))
        remote_zip_filepath = os.path.join(self.remote_task_dir, zip_filename)

        self.shell.run(["zip", "-r", zip_filename, "output"], cwd=self.remote_task_dir)
        self.shell.run(["zip", "-r", "-g", zip_filename, "workdir"], cwd=self.remote_task_dir)

        sftp.get(remote_zip_filepath, local_zip_filepath)
        sftp.close()
        # with self.shell.open("/mirror/%s/%s" % (remote_dir, zip_filename), "rb") as remote_file:
        #     with open(local_zip_filepath, "wb") as local_file:  # transfer to media/tool_activity_%d/output
        #         shutil.copyfileobj(remote_file, local_file)

        with open(local_zip_filepath, "rb") as local_file:  # attach transferred file to database
            new_file = SkyLabFile.objects.create(type=2, task=self.task)
            new_file.file.name = os.path.join(os.path.join(self.task.task_dirname, 'output'),
                                              new_file.filename)
            new_file.save()

        if not self.task.tasklog_set.filter(status_code=400).exists():
            self.task.change_status(status_code=200, status_msg="Output files received. No errors encountered")
        else:
            self.task.change_status(status_code=401, status_msg="Output files received. Errors encountered")

        self.logger.info(self.log_prefix + 'Done. Output files sent')

        # Delete remote task directory
        self.shell.run(['rm', '-r', self.remote_task_dir])

class AutoGrid4Executable(P2CToolGeneric):
    def __init__(self, **kwargs):
        super(AutoGrid4Executable, self).__init__(self, **kwargs)
        self.working_dir = os.path.join(self.remote_task_dir, 'workdir')

    def handle_input_files(self, **kwargs):
        self.shell.run(["sh", "-c", "mkdir -p tool_activity_%d/output" % self.id])
        Task.objects.filter(pk=self.id).update(status="Fetching input files")
        files = SkyLabFile.objects.filter(input_files__pk=self.id)
        for f in files:
            sftp = self.shell._open_sftp_client()
            mkdir_p(sftp, 'tool_activity_%d/workdir' % self.id)
            sftp.putfo(f.file, f.filename)  # At this point, you are in remote_path
            sftp.close()

    # raise not implemented error
    def print_msg(self, msg):
        print ("AutoGrid (Tool Activity %d) : %s" % (self.id, msg))

    def run_tool(self, **kwargs):
        self.task.change_status(status_msg='Task started', status_code=150)

        self.handle_input_files()

        exec_string = Task.objects.get(pk=self.id).exec_string
        Task.objects.filter(pk=self.id).update(status="Executing task command")

        self.print_msg("Running %s" % exec_string)


        exec_shell = self.shell.run(["sh", "-c", exec_string], cwd=self.working_dir)
        # cwd=self.working_dir)

        self.print_msg(exec_shell.output)

        self.print_msg("Finished command execution")
        Task.objects.filter(pk=self.id).update(status="Finished command execution", status_code=2)

        self.handle_output_files()

        Task.objects.filter(pk=self.id).update(status="Task finished")

    def handle_output_files(self, **kwargs):
        Task.objects.filter(pk=self.id).update(status="Handling output files")
        self.print_msg("Sending output files to server")
        media_root = getattr(settings, "MEDIA_ROOT")

        remote_dir = "tool_activity_%d" % self.id
        os.makedirs(os.path.join(media_root, "%s/output" % remote_dir))
        output_filename = "AutoGridOutput_%d.zip" % self.id
        server_zip_filepath = os.path.join(media_root, "%s/output/%s" % (remote_dir, output_filename))

        sftp = self.shell._open_sftp_client()
        remote_path = "/mirror/tool_activity_%d/workdir/" % self.id

        remote_files = sftp.listdir(path=remote_path)

        input_files = SkyLabFile.objects.filter(input_files__pk=self.id)
        input_filenames = [file.filename for file in input_files]

        # remove input files in workdir
        for remote_file in remote_files:
            remote_filepath = os.path.join(remote_path, remote_file)
            if remote_file in input_filenames:
                sftp.remove(remote_filepath)  # delete after transfer
        sftp.close()

        self.shell.run(["zip", "-r", output_filename, "output"], cwd="/mirror/tool_activity_%d/" % self.id)
        self.shell.run(["zip", "-r", "-g", output_filename, "workdir"], cwd="/mirror/tool_activity_%d/" % self.id)

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
            tool_activity = Task.objects.get(pk=self.id)
            tool_activity.output_files.add(new_file)
            tool_activity.save()
            local_file.close()
