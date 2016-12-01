from skylab.bootskylab import add_tools_to_toolset
from skylab.models import ToolSet


def insert_to_db():
    toolset_dict = {
        'display_name': 'AutoDock 4',
        'package_name': __name__.replace('.install', ''),
        'p2ctool_name': 'autodock',
        'description': 'AutoDock is a suite of automated docking tools. It is designed to predict how small molecules, '
                       'such as substrates or drug candidates, bind to a receptor of known 3D structure.',
        'source_url': 'http://autodock.scripps.edu/'
    }

    toolset, created = ToolSet.objects.update_or_create(p2ctool_name=toolset_dict['p2ctool_name'],
                                                        defaults={'display_name': toolset_dict['display_name'],
                                                                  'description': toolset_dict.get('description',
                                                                                                  'No description provided'),
                                                                  'source_url': toolset_dict.get('source_url',
                                                                                                 'No link provided'),
                                                                  'package_name': toolset_dict.get('package_name')
                                                                  }
                                                        )

    # Ff you followed the naming convention for classes,
    #   you do not need to provide values for executable_name and view_name
    tools = [
        {'display_name': 'autogrid4',
         # 'executable_name': 'AutoGrid4Executable',
         # 'view_name': 'AutogridView',
         'description': 'Pre-calculates grids to be used by autodock4',
         },
        {'display_name': 'autodock4',
         # 'executable_name': 'AutoDock4Executable',
         # 'view_name': 'Autodoc4kView',
         'description': 'Performs the docking of the ligand to a set of grids describing the target protein',
         },
    ]

    add_tools_to_toolset(tools, toolset)  # associate tools to toolset
