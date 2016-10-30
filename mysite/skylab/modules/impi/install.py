from skylab.bootskylab import add_tools_to_toolset
from skylab.models import ToolSet


def insert_to_db():
    toolset_dict = {
        'display_name': 'Impi',
        'package_name': __name__.replace('.install', ''),
        'p2ctool_name': 'impi',
        'description': 'Image processing tool',
        # 'source_url': 'http://www.quantum-espresso.org/'
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
        {'display_name': 'Impi',
         # "executable_name": "QuantumESPRESSOExecutable",
         # "view_name":"QuantumESPRESSOView",
         'description': 'Image processing tool for JPEG format',
         },

    ]

    add_tools_to_toolset(tools, toolset)
