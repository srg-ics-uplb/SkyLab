from skylab.bootskylab import add_tools_to_toolset
from skylab.models import ToolSet


def insert_to_db():
    toolset_dict = {
        'display_name': 'GAMESS',
        'package_name': __name__.replace('.install', ''),
        'p2ctool_name': 'gamess',
        'description': 'The General Atomic and Molecular Electronic Structure System (GAMESS) '
                       'is a general ab initio quantum chemistry package. '
                       'Briefly, GAMESS can compute SCF wavefunctions ranging from RHF, ROHF, UHF, GVB, and MCSCF.',
        'source_url': 'http://www.msg.ameslab.gov/gamess/'
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
        {'display_name': 'GAMESS',
         # "executable_name": "GAMESSExecutable",
         # "view_name":"GAMESSView",
         'description': 'GAMESS can compute SCF wavefunctions ranging from RHF, ROHF, UHF, GVB, and MCSCF'
         },

    ]

    add_tools_to_toolset(tools, toolset)
