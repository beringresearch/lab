import yaml
import subprocess

_DEFAULT_USER_ID = 'unknown'

class Project():
    def __init__(self, labfile):
        with open(labfile, 'r') as file:
            config = yaml.load(file)

        self.name = config['name']
        self.entry_points = config['entry_points']
        self.user_id = _get_user_id()

    def start_run(self):
        for key in self.entry_points:            
            command = self.entry_points[key]['command']
            command = command.split()
            subprocess.call(command)


def _get_user_id():
    """Get the ID of the user for the current run."""
    try:
        import pwd
        import os
        return pwd.getpwuid(os.getuid())[0]
    except ImportError:
        return _DEFAULT_USER_ID