import os.path
import re
import shutil

from django.conf import settings

from skylab.models import Task, SkyLabFile
from skylab.modules.base_tool import P2CToolGeneric, mkdir_p

cluster_password = settings.CLUSTER_PASSWORD

class RayExecutable(P2CToolGeneric):
    def __init__(self, **kwargs):
        self.shell = kwargs.get('shell')
        self.id = kwargs.get('id')
        self.working_dir = "/mirror/tool_activity_%d" % self.id
        Task.objects.filter(pk=self.id).update(status="Task started", status_code=1)
        super(RayExecutable, self).__init__(self, **kwargs)

    def handle_input_files(self, **kwargs):
        self.shell.run(["sh", "-c", "mkdir tool_activity_%d" % self.id])
        Task.objects.filter(pk=self.id).update(status="Fetching input files")
        files = SkyLabFile.objects.filter(input_files__pk=self.id)
        for f in files:
            sftp = self.shell._open_sftp_client()
            mkdir_p(sftp, f.upload_path)
            sftp.putfo(f.file, f.filename)  # At this point, you are in remote_path
            sftp.close()

    # raise not implemented error
    def print_msg(self, msg):
        print ("Ray (Tool Activity %d) : %s" % (self.id, msg))

    def run_tool(self, **kwargs):
        self.handle_input_files()

        export_path = "/mirror/Ray-2.3.1/build"

        exec_string = Task.objects.get(pk=self.id).exec_string
        Task.objects.filter(pk=self.id).update(status="Executing task command")

        # todo: download ontologyterms.txt
        # if -gene-ontology is found

        p = re.compile("-gene-ontology")
        m = p.search(exec_string)
        if m is not None:
            self.print_msg(
                "Downloading OntologyTerms from http://geneontology.org/ontology/obo_format_1_2/gene_ontology_ext.obo")
            self.shell.run(["wget", "-O", "OntologyTerms.txt",
                            "http://geneontology.org/ontology/obo_format_1_2/gene_ontology_ext.obo"],
                           cwd=self.working_dir + "/input")

        self.print_msg("Running %s" % exec_string)

        exec_shell = self.shell.run(["sh", "-c", "export PATH=$PATH:%s; echo $PATH; %s;" % (export_path, exec_string)])
        # cwd=self.working_dir)
        print (exec_shell.output)

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
        output_filename = "RayOutput_%d.zip" % self.id
        server_zip_filepath = os.path.join(media_root, "%s/output/%s" % (remote_dir, output_filename))

        self.shell.run(["zip", "-r", output_filename, "output"], cwd=self.working_dir)

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

        Task.objects.filter(pk=self.id).update(status="Finished handling output files")
        self.print_msg("Output files sent")

    def changeStatus(self, status):
        pass
