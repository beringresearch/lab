import datetime
import sys

import yaml
import subprocess
import os
import shutil

import venv as ve

from shutil import copyfile

def create_venv(project_name):
    # Create a virtual environment
    venv_dir = os.path.join(project_name, '.venv')

    environment = ve.EnvBuilder(symlinks=True, with_pip=True)
    environment.create(venv_dir)
    
    subprocess.call([venv_dir + '/bin/pip', 'install', 'pyyaml'])
    subprocess.call([venv_dir + '/bin/pip', 'install', '-r', 'requirements.txt'])
    
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

def project_init(project_name):
    pyversion = '%s.%s' % (sys.version_info[0], sys.version_info[1])
    
    # Create project structure
    os.mkdir(project_name)
    os.mkdir(os.path.join(project_name, 'notebooks'))
    os.mkdir(os.path.join(project_name, 'data'))
    os.mkdir(os.path.join(project_name, 'logs'))
    os.mkdir(os.path.join(project_name, 'models'))
    os.mkdir(os.path.join(project_name, 'config'))

    open(os.path.join(project_name, 'README.md'), 'a').close()

    # Copy requirements.txt file
    copyfile('requirements.txt', project_name+'/requirements.txt')

    # Create a virtual environment
    create_venv(project_name)
    

    # Create runtime configuration
    runtime = {'name': project_name,
               'description': None,
               'python': pyversion,
               'timestamp': str(datetime.datetime.now()),
               'venv': '.venv'}
    with open(os.path.join(project_name, 'config', 'runtime.yaml'), 'w') as file:
        yaml.dump(runtime, file, default_flow_style=False)

    # Generate a Dockerfile
    #f.write('FROM python:%s\n' % (pyversion))
    #f = open(os.path.join(name, 'Dockerfile'), 'w')
    #f.write('COPY .venv .\n')
    #f.write('COPY config .\n')
    #f.write('COPY data .\n')
    #f.write('COPY logs .\n')
    #f.write('COPY models .\n')
    #f.write('COPY notebooks .\n')
    #f.write('COPY requirements.txt .\n')
    #f.write('COPY README.md .')    
    #f.close()
    