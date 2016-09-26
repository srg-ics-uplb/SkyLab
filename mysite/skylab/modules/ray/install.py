from skylab.models import ToolSet
from skylab.modules.basetool import add_tools_to_toolset


def insert_to_db():
    toolset_name = 'Ray'
    package_name = __name__.replace(".install", '')
    toolset_description = 'Ray is a parallel software that computes de novo genome assemblies with next-generation sequencing data'
    toolset_source_url = 'http://denovoassembler.sourceforge.net/'

    toolset, created = ToolSet.objects.get_or_create(display_name=toolset_name, package_name=package_name,
                                                     description=toolset_description, source_url=toolset_source_url)

    # if you followed the naming convention for classes, you do not need to provide values for executable_name and view_name
    tools = [
        {'display_name': 'Ray',
         # "executable_name": "RayExecutable",
         # "view_name":"RayView",
         },
    ]

    add_tools_to_toolset(tools, toolset)
