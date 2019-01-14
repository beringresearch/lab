import datetime
import sys

import yaml
import subprocess
import os
import shutil

import venv as ve

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

    environment = ve.EnvBuilder(symlinks=True, with_pip=True)
    environment.create(venv_dir)
    
    if r is not None:
        #subprocess.call([venv_dir + '/bin/pip', 'install', 'virtualenv'])
        subprocess.call([venv_dir + '/bin/pip', 'install', 'pyyaml'])
        subprocess.call([venv_dir + '/bin/pip', 'install', '-r', r])
    
    # Move lab into the virtual environment
    pkgname = 'lab'    
    pyversion = '%s.%s' % (sys.version_info[0], sys.version_info[1])
    
    try:
        pkgobj = __import__(pkgname)
    except Exception as e:
        print(e)
        sys.exit(1)
    
    pkgdir = os.path.dirname(pkgobj.__file__)
    dst = '%s/lib/python%s/site-packages/%s' % (venv_dir, pyversion, pkgname)
    shutil.copytree(pkgdir, dst)
    

    # Create runtime configuration
    runtime = {'name': name,
               'description': None,
               'python': pyversion
               'timestamp': str(datetime.datetime.now()),
               'venv': '.venv'}
    with open(os.path.join(name, 'config', 'runtime.yaml'), 'w') as file:
        yaml.dump(runtime, file, default_flow_style=False)