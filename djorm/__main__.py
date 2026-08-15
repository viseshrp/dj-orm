'\nInvokes djorm when the django module is run as a script.\n\nExample: python -m django check\n'

from djorm.core import management

if __name__ == "__main__":
    management.execute_from_command_line()
