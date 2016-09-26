from skylab.models import ToolSet
from skylab.modules.basetool import add_tools_to_toolset


def insert_to_db():
    toolset_name = 'Dock 6'
    package_name = __name__.replace('.install', '')
    toolset_description = 'AutoDock is a suite of automated docking tools. It is designed to predict how small molecules, ' \
                          'such as substrates or drug candidates, bind to a receptor of known 3D structure.'
    toolset_source_url = 'http://autodock.scripps.edu/'

    toolset, created = ToolSet.objects.get_or_create(display_name=toolset_name, package_name=package_name,
                                                     description=toolset_description, source_url=toolset_source_url)

    # if you followed the naming convention for classes, you do not need to provide values for executable_name and view_name
    tools = [
        {'display_name': 'Dock 6',
         # 'executable_name': 'Dock6Executable',
         # 'view_name':'Dock6View',
         'description': 'Pre-calculates grids to be used by AutoDock',
         },
        {'display_name': 'Grid',
         # 'executable_name': 'GridExecutable',
         # 'view_name':'GridView',
         'description': 'Performs the docking of the ligand to a set of grids describing the target protein',
         },
    ]

    add_tools_to_toolset(tools, toolset)
