import yaml
import subprocess
import os

_DEFAULT_USER_ID = 'unknown'

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Project():
    def __init__(self, labfile, verbose=True):
        with open(labfile, 'r') as file:
            config = yaml.load(file)

        self.name = config['name']
        self.entry_points = config['entry_points']
        self.user_id = _get_user_id()
        self.labfile = labfile
        self.verbose = verbose

    def start_run(self):
        os.chdir(os.path.dirname(self.labfile))
        for key in self.entry_points:
            command = self.entry_points[key]['command']
            command = command.split()
            if self.verbose:
                print(bcolors.OKGREEN + "Processing " + command[1])
            subprocess.call(command)


def _get_user_id():
    """Get the ID of the user for the current run."""
    try:
        import pwd
        import os
        return pwd.getpwuid(os.getuid())[0]
    except ImportError:
        return _DEFAULT_USER_ID