from skylab.bootskylab import add_tools_to_toolset
from skylab.models import ToolSet


def insert_to_db():
    toolset_name = 'Quantum ESPRESSO'
    package_name = __name__.replace(".install", '')
    p2ctool_name = 'quantum-espresso'
    toolset_description = 'Quantum Espresso is an integrated suite of Open-Source computer codes for electronic-structure ' \
                          'calculations and materials modeling at the nanoscale. It is based on density-functional theory, ' \
                          'plane waves, and pseudopotentials.'
    toolset_source_url = 'http://www.quantum-espresso.org/'

    toolset, created = ToolSet.objects.update_or_create(package_name=package_name,
                                                        p2ctool_name=p2ctool_name,
                                                        defaults={'display_name': toolset_name,
                                                                  'description': toolset_description,
                                                                  'source_url': toolset_source_url})

    # if you followed the naming convention for classes, you do not need to provide values for executable_name and view_name
    tools = [
        {'display_name': 'Quantum ESPRESSO',
         # "executable_name": "QuantumESPRESSOExecutable",
         # "view_name":"QuantumESPRESSOView",
         'description': 'GAMESS can compute SCF wavefunctions ranging from RHF, ROHF, UHF, GVB, and MCSCF'
         },

    ]

    add_tools_to_toolset(tools, toolset)
