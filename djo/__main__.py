"""
Invokes djo when the djo module is run as a script.

Example: python -m djo migrate
"""

from djo.core import management


if __name__ == "__main__":
    management.execute_from_command_line()
