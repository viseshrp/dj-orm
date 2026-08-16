"""
Invokes djrm when the djrm module is run as a script.

Example: python -m djrm migrate
"""

from djrm.core import management


if __name__ == "__main__":
    management.execute_from_command_line()
