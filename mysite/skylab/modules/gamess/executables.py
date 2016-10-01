import json
import os
import re
import shutil
import sys
import time

import spur
from django.conf import settings

from skylab.models import SkyLabFile
from skylab.modules.basetool import P2CToolGeneric


class GAMESSExecutable(P2CToolGeneric):
    def __init__(self, **kwargs):
        self.shell = kwargs.get('shell')
        self.task = kwargs.get('task')
        # self.id = kwargs.get('id')

        self.working_dir = '/mirror/' + self.task.task_dirname

        # clear scr folder
        remote_path = '/mirror/scr/'
        sftp = self.shell._open_sftp_client()
        remote_files = sftp.listdir(path=remote_path)
        for remote_file in remote_files:
            remote_filepath = os.path.join(remote_path, remote_file)
            sftp.remove(remote_filepath)  # delete after transfer
        sftp.close()

        # clear or create task folder
        self.shell.run(
            ['sh', '-c', 'if [ -d {0} ]; then rm -rf {0}/*; else mkdir {0}; fi'.format(self.task.task_dirname)])



        super(GAMESSExecutable, self).__init__(self, **kwargs)


    def handle_input_files(self, **kwargs):
        self.task.change_status(status_msg='Uploading input files', status_code=151)

        files = SkyLabFile.objects.filter(task=self.task.id, type=1)
        for f in files:
            with self.shell.open('/mirror/{0}/{1}'.format(self.task.task_dirname, f.filename), 'wb') as remote_file:
                with f.file as local_file:
                    shutil.copyfileobj(local_file, remote_file)


    def handle_output_files(self, **kwargs):
        self.task.change_status(status_msg='Retrieving output files', status_code=154)
        self.print_msg('Sending output files to server')
        media_root = settings.MEDIA_ROOT

        try:
            os.makedirs(os.path.join(media_root, self.task.task_dirname + '/output'))
        except OSError:
            pass
            # no need to delete contained files since they are deleted automatically if skylabfile object is deleted
            # os.removedirs(os.path.join(media_root, self.task_folder+'/output'))
            # os.makedirs(os.path.join(media_root, self.task_folder + '/output'))

        # self.filename = os.path.splitext(f.filename)[0]
        files = SkyLabFile.objects.filter(task=self.task.id, type=1)
        for f in files:
            filename = os.path.splitext(f.filename)[0]
            local_dir = '{0}/output/{1}.log'.format(self.task.task_dirname, filename)
            server_path = os.path.join(media_root, local_dir)
            # print "/mirror/%s/%s.log" % (remote_dir, self.filename)
            # print server_path

            # with statement automatically closes the file
            try:
                with self.shell.open('/mirror/{0:s}/{1:s}.log'.format(self.task.task_dirname, filename),
                                     "rb") as remote_file:
                    with open(server_path, 'wb') as local_file:  # transfer to media/task_%d/output
                        shutil.copyfileobj(remote_file, local_file)

                with open(server_path, "rb") as local_file:  # attach transferred file to database
                    new_file = SkyLabFile.objects.create(type=2, upload_path=u'task_{0:d}/output'.format(self.task.id),
                                                         filename=u'{0:s}.log'.format(filename), render_with_jsmol=True,
                                                         task=self.task)
                    new_file.file.name = local_dir
                    new_file.save()
            except IOError:
                # since handle output files will still be called even if an error happened
                # if there is an error in execution, there probably would be missing matching output files for each input
                print ("Cannot read " + filename + ".log in remote cluster", sys.exc_info())

        local_dir = u'{0:s}/output/'.format(self.task.task_dirname)
        server_path = os.path.join(media_root, local_dir)
        sftp = self.shell._open_sftp_client()
        remote_path = '/mirror/scr/'

        # retrieve then delete produced scratch files
        remote_files = sftp.listdir(path=remote_path)
        for remote_file in remote_files:
            remote_filepath = os.path.join(remote_path, remote_file)
            local_filepath = os.path.join(server_path, remote_file)
            sftp.get(remote_filepath, local_filepath)
            with open(local_filepath, "rb") as local_file:
                new_file = SkyLabFile.objects.create(type=2, task=self.task,
                                                     upload_path=u'tool_activity_{0:d}/output'.format(self.task.id),
                                                     filename=remote_file)
                new_file.file.name = os.path.join(new_file.upload_path, new_file.filename)
                new_file.save()
                local_file.close()

            sftp.remove(remote_filepath)  # delete after transfer
        sftp.close()

        #self.print_msg(self.shell.run(["ls"]).output)

        if self.task.tasklog_set.latest('timestamp').status_code != 400:
            self.task.change_status(status_code=200, status_msg="Output files received. No errors encountered")
        else:
            self.task.change_status(status_code=400, status_msg="Output files received. Errors encountered")

        self.print_msg('Done. Output files sent')

        # Delete remote working directory
        self.shell.run(['rm', '-r', self.working_dir])


    # raise not implemented error
    def print_msg(self, msg):
        print ('Gamess (Tool Activity {0:d}) : {1:s}'.format(self.task.id, msg))


    def run_tool(self, **kwargs):
        self.task.change_status(status_msg='Task started', status_code=150)
        self.handle_input_files()

        export_path = '/mirror/gamess'
        self.task.change_status(status_msg="Executing tool script", status_code=152)

        command = 'sudo /sbin/sysctl -w kernel.shmmax=500000000'
        shmax_fixer = self.shell.spawn(['sh', '-c', command], use_pty=True)
        shmax_fixer.stdin_write(settings.CLUSTER_PASSWORD + "\n")
        shmax_fixer.wait_for_result()

        command_list = json.loads(self.task.command_list)
        error = False
        for command in command_list:
            while True:
                self.print_msg(u'Running {0:s}'.format(command))
                try:
                    exec_shell = self.shell.run(
                        ['sh', '-c', 'export PATH=$PATH:{0:s}; echo $PATH; {1:s};'.format(export_path, command)],
                        cwd=self.working_dir
                    )
                    break
                except spur.RunProcessError as err:
                    if err.return_code == -1:  # no return code received
                        self.print_msg('No response from server. Retrying command ({0})'.format(command))
                    else:
                        self.print_msg('RuntimeError: ' + err.stderr_output)
                        error = True
                        break
                    pass
                except spur.ssh.ConnectionError:
                    self.print_msg('Connection error. Retrying command ({0})'.format(command))
                finally:
                    time.sleep(5)

            if not error:
                p = re.compile("EXECUTION\sOF\sGAMESS\sTERMINATED\s(?P<exit_status>\S+)")
                m = p.search(exec_shell.output)
                # print (exec_shell.output)
                if m is not None:
                    self.print_msg(m.group('exit_status'))

                    p = re.compile("ERROR,\s(?P<error_msg>.+)")
                    error = p.search(exec_shell.output)
                    if error is not None:  # todo: more advanced catching
                        print (u'Error: {0:s}'.format(error.group('error_msg')))
                        error = True
                else:
                    error = True

        if error:
            self.task.change_status(
                status_msg='Task execution error! See .log file for more information', status_code=400)
        else:
            self.print_msg('Finished command execution')

            self.task.change_status(status_msg='Tool execution successful',
                                    status_code=153)

        self.handle_output_files()


class Dummy(object):
    def __init__(self):
        print ("Hello world")
