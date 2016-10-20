from skylab.bootskylab import add_tools_to_toolset
from skylab.models import ToolSet


def insert_to_db():
    toolset_name = 'GAMESS'
    package_name = __name__.replace(".install", '')
    p2ctool_name = 'gamess'
    toolset_description = 'The General Atomic and Molecular Electronic Structure System (GAMESS) ' \
                          'is a general ab initio quantum chemistry package.'
    toolset_source_url = 'http://www.msg.ameslab.gov/gamess/'

    toolset, created = ToolSet.objects.update_or_create(package_name=package_name,
                                                        p2ctool_name=p2ctool_name,
                                                        defaults={'display_name': toolset_name,
                                                                  'description': toolset_description,
                                                                  'source_url': toolset_source_url})

    # if you followed the naming convention for classes, you do not need to provide values for executable_name and view_name
    tools = [
        {'display_name': 'GAMESS',
         # "executable_name": "GAMESSExecutable",
         # "view_name":"GAMESSView",
         'description': 'GAMESS can compute SCF wavefunctions ranging from RHF, ROHF, UHF, GVB, and MCSCF'
         },

    ]

    add_tools_to_toolset(tools, toolset)
