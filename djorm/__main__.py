"""
Invokes djorm when the djorm module is run as a script.

Example: python -m djorm migrate
"""

from djorm.core import management


if __name__ == "__main__":
    management.execute_from_command_line()
