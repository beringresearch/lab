import datetime
import sys

import yaml
import subprocess
import os

import virtualenv as ve

def project_init(name, r):
    # Create project structure
    os.mkdir(name)
    os.mkdir(os.path.join(name, 'notebooks'))
    os.mkdir(os.path.join(name, 'data'))
    os.mkdir(os.path.join(name, 'logs'))
    os.mkdir(os.path.join(name, 'models'))
    os.mkdir(os.path.join(name, 'config'))

    open(os.path.join(name, 'README.md'), 'a').close()

    # Create a virtual environment
    venv_dir = os.path.join(name, '.venv')
    ve.create_environment(venv_dir)

    if r is not None:  
        with open(r, "a") as myfile:
            myfile.write('git+https://github.com/beringresearch/lab')
        subprocess.call([venv_dir + '/bin/pip', 'install', '-r', r])

    # Create runtime configuration
    runtime = {'name': name,
               'description': None,
               'timestamp': str(datetime.datetime.now()),
               'venv': '.venv'}
    with open(os.path.join(name, 'config', 'runtime.yaml'), 'w') as file:
        yaml.dump(runtime, file, default_flow_style=False)