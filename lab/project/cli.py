import click
import uuid
import os
import venv as ve
import sys
import datetime
import yaml
import subprocess
import shutil
from minio import Minio
from minio.error import ResponseError


@click.command(name='init')
@click.option('--name', type=str, default=str(uuid.uuid4()),
              help='environment name')
def lab_init(name):
    """ Initialise a new Lab Project """
    if not os.path.isfile('requirements.txt'):
        click.secho('requirements.txt is not found in the '
                    'current working directory.', fg='red')
        raise click.Abort()

    if os.path.isdir(name):
        click.secho('Project '+name+' already exists.', fg='red')
        raise click.Abort()
    else:
        _project_init(name)

@click.command(name='update')
def lab_update():
    """ Update Lab Environment from Project's requirements.txt """
    if not os.path.isdir('.venv'):
        click.secho("Doesn't looks like this is a valid "
                    'Lab Project as .venv is missing.', fg='red')
        raise click.Abort()
    if not os.path.isfile('requirements.txt'):
        click.secho('requirements.txt file is missing.', fg='red')
        raise click.Abort()
    
    click.secho('Updating environemnt using requirements.txt', fg='blue')
    venv_dir = os.path.join(os.getcwd(), '.venv')
    subprocess.call([venv_dir + '/bin/pip', 'install',
                    '-r', 'requirements.txt'])
    


def _create_venv(project_name):
    # Create a virtual environment
    venv_dir = os.path.join(project_name, '.venv')

    environment = ve.EnvBuilder(symlinks=True, with_pip=True)
    environment.create(venv_dir)

    subprocess.call([venv_dir + '/bin/pip', 'install', 'pyyaml'])
    subprocess.call([venv_dir + '/bin/pip', 'install', 'cloudpickle'])
    subprocess.call([venv_dir + '/bin/pip', 'install', 'minio'])
    subprocess.call([venv_dir + '/bin/pip', 'install',
                    '-r', 'requirements.txt'])

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

@click.command('pull')
@click.option('--tag', type=str, help='minio host nickname')
@click.option('--bucket', type=str, default=str(uuid.uuid4()),
              help='minio bucket name')
@click.option('--project', type=str, default=str(uuid.uuid4()),
              help='Lab Project name')
def lab_pull(tag, bucket, project):
    """ Pulls Lab Experiment from minio to current directory """
    home_dir = os.path.expanduser('~')
    project_dir = os.path.join(os.getcwd(), project)
    lab_dir = os.path.join(home_dir, '.lab')

    if not os.path.exists(lab_dir):
        click.secho('Lab is not configured to connect to minio. '
                    'Run <lab config> to set up access points.',
                    fg='red')
        raise click.Abort()


    if not os.path.exists(project_dir):
        os.makedirs(project_dir)
        _pull_from_minio(tag, bucket, project)
    else:
        click.secho('Directory '+project+' already exists.', fg='red')
        raise click.Abort()
    


@click.command('push')
@click.option('--tag', type=str, help='minio host nickname')
@click.option('--bucket', type=str, default=str(uuid.uuid4()),
              help='minio bucket name')
@click.argument('path', type=str, default=os.getcwd())
def lab_push(tag, bucket, path):
    """ Push Lab Experiment to minio """
    models_directory = 'experiments'
    logs_directory = 'logs'

    home_dir = os.path.expanduser('~')
    lab_dir = os.path.join(home_dir, '.lab')
    if not os.path.exists(lab_dir):
        click.secho('Lab is not configured to connect to minio. '
                    'Run <lab config> to set up access points.',
                    fg='red')
        raise click.Abort()

    if not (os.path.exists(models_directory) & os.path.exists(logs_directory)):
        click.secho('This directory lacks a valid Lab Project directory '
                    'structure. Run <lab init> to create one.',
                    fg='blue')
        raise click.Abort()

    _push_to_minio(tag, bucket, path)


def _pull_from_minio(tag, bucket, project_name):
    home_dir = os.path.expanduser('~')
    lab_dir = os.path.join(home_dir, '.lab')
    project_dir = os.path.join(os.getcwd(), project_name)

    with open(os.path.join(lab_dir, 'config.yaml'), 'r') as file:
        minio_config = yaml.load(file)[tag]
    
    hostname = minio_config['minio_endpoint']
    accesskey = minio_config['minio_accesskey']
    secretkey = minio_config['minio_secretkey']

    minioClient = Minio(hostname,
                        access_key=accesskey,
                        secret_key=secretkey,
                        secure=False)

    if not minioClient.bucket_exists(bucket):
        click.secho('Bucket '+bucket+ ' is not found on remote', fg='red')
        raise click.Abort()
    try:
        objects = minioClient.list_objects(bucket, prefix=project_name, recursive=True)
        for obj in objects:
            object_name = obj.object_name
            print('Downloading '+object_name)
            minioClient.fget_object(bucket, object_name, os.path.join(os.getcwd(), object_name))
    except ResponseError as err:
        print(err)

def _push_to_minio(tag, bucket, path):
    home_dir = os.path.expanduser('~')
    lab_dir = os.path.join(home_dir, '.lab')

    with open(os.path.join(lab_dir, 'config.yaml'), 'r') as file:
        minio_config = yaml.load(file)[tag]

    with open(os.path.join(path, 'config/runtime.yaml'), 'r') as file:
        config = yaml.load(file)

    project_name = config['name']

    hostname = minio_config['minio_endpoint']
    accesskey = minio_config['minio_accesskey']
    secretkey = minio_config['minio_secretkey']

    input_objects = []
    output_objects = []
    exclude = set(['.venv'])
    for root, d_names, f_names in os.walk(path, topdown=True):
        d_names[:] = [d for d in d_names if d not in exclude]
        for f in f_names:
            input_objects.append(os.path.join(root, f))
            output_objects.append(os.path.join(project_name,
                                               root.strip('./'), f))

    minioClient = Minio(hostname,
                        access_key=accesskey,
                        secret_key=secretkey,
                        secure=False)

    if not minioClient.bucket_exists(bucket):
        minioClient.make_bucket(bucket, location='eu-west-1')

    try:
        for i in range(len(input_objects)):
            minioClient.fput_object(bucket, output_objects[i],
                                    input_objects[i])
            print('Succesfully processed '+input_objects[i])
    except ResponseError as err:
        print(err)


def _project_init(project_name):
    pyversion = '%s.%s' % (sys.version_info[0], sys.version_info[1])

    # Create project structure
    os.mkdir(project_name)
    os.mkdir(os.path.join(project_name, 'notebooks'))
    os.mkdir(os.path.join(project_name, 'data'))
    os.mkdir(os.path.join(project_name, 'logs'))
    os.mkdir(os.path.join(project_name, 'experiments'))
    os.mkdir(os.path.join(project_name, 'config'))

    open(os.path.join(project_name, 'README.md'), 'a').close()

    file = open(os.path.join(project_name, '.gitignore'), 'w')
    file.write('.venv/')
    file.close()

    # Copy requirements.txt file
    shutil.copyfile('requirements.txt', project_name+'/requirements.txt')

    # Create a virtual environment
    _create_venv(project_name)

    # Create runtime configuration
    runtime = {'name': project_name,
               'path': os.path.join(os.getcwd(), project_name),
               'description': None,
               'python': pyversion,
               'timestamp': str(datetime.datetime.now()),
               'venv': '.venv'}

    with open(os.path.join(project_name,
              'config', 'runtime.yaml'), 'w') as file:
        yaml.dump(runtime, file, default_flow_style=False)
