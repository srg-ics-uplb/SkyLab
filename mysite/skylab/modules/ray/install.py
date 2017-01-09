from skylab.bootskylab import add_tools_to_toolset
from skylab.models import ToolSet


def insert_to_db():
    toolset_dict = {
        'display_name': 'Ray',
        'package_name': __name__.replace('.install', ''),
        'p2ctool_name': 'ray',
        'description': 'Ray is a parallel software that computes de novo genome assemblies with next-generation sequencing data.',
        'source_url': 'http://denovoassembler.sourceforge.net/'
    }

    toolset, created = ToolSet.objects.update_or_create(package_name=toolset_dict['package_name'],
                                                        p2ctool_name=toolset_dict['p2ctool_name'],
                                                        defaults={'display_name': toolset_dict['display_name'],
                                                                  'description': toolset_dict.get('description',
                                                                                                  'No description provided'),
                                                                  'source_url': toolset_dict.get('source_url',
                                                                                                 'No link provided')
                                                                  }
                                                        )

    # if you followed the naming convention for classes, you do not need to provide values for executable_name and view_name
    tools = [
        {'display_name': 'Ray',
         'description': 'The main executable for Ray'
         # "executable_name": "RayExecutable",
         # "view_name":"RayView",
         },
    ]

    add_tools_to_toolset(tools, toolset)  # add tool db entries and associate them with toolset
