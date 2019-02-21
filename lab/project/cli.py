import click
import uuid
import glob
import os
import venv as ve
import sys
import datetime
import yaml
import subprocess
import shutil
from minio import Minio
from minio.error import ResponseError

import tabulate
import pandas as pd
import numpy as np

@click.command('ls')
@click.argument('sort_by', required=False)
def lab_ls(sort_by=None):
    """ Compare multiple Lab Experiments """
    models_directory = 'experiments'
    logs_directory = 'logs'
    TICK = '█'

    if not os.path.exists(models_directory):
        click.secho('This directory does not appear to have a valid '
                    'Lab Project structure.\nRun <lab init> to create one.',
                    fg='red')
        raise click.Abort()

    experiments = next(os.walk(models_directory))[1]
    if len(experiments) == 0:
        click.secho("It looks like you've started a brand new project. "
                    'Run your first experiment to generate a list of metrics.',
                    fg='blue')
        raise click.Abort()
    comparisons = []

    for e in experiments:
        metrics_file = os.path.join(models_directory, e, 'metrics.yaml')
        try:
            with open(metrics_file, 'r') as file:
                metrics = yaml.load(file)
            for k, v in metrics.items():
                metrics[k] = round(v, 2)

            metrics_list = list(metrics.values())

            meta_file = os.path.join(logs_directory, e, 'meta.yaml')
            with open(meta_file, 'r') as file:
                meta = yaml.load(file)

            record = [meta['experiment_uuid'], meta['source'],
                      str(meta['start_time'].date())] + metrics_list
            comparisons.append(record)
        except FileNotFoundError:
            pass

    # Create visualisation of numeric metrics
    A = pd.DataFrame(comparisons)
    meta_data = A[[0, 1, 2]]
    metrics_data = A.drop([0, 1, 2], axis=1)

    row_max = metrics_data.abs().max(axis=0)
    scaled_metrics_data = metrics_data.abs().divide(row_max, axis=1)
    scaled_metrics_data = scaled_metrics_data.fillna(value=0)

    sparklines = np.empty(shape=metrics_data.shape, dtype=object)
    for row in range(metrics_data.shape[0]):
        for column in range(metrics_data.shape[1]):
            value = metrics_data.iloc[row, column]
            scaled_value = scaled_metrics_data.iloc[row, column]
            scaled_value = scaled_value
            spark = (format(value, '.2f') + ': ' +
                     TICK * int(round(scaled_value*10)))
            sparklines[row, column] = spark

    result = pd.concat([meta_data, pd.DataFrame(sparklines)], axis=1)
    result.columns = (['Experiment', 'Source', 'Date'] +
                      list(metrics.keys()))

    if sort_by is not None:
        result.sort_values(by=[sort_by], axis=0,
                           ascending=False, inplace=True)

    header = ['Experiment', 'Source', 'Date'] + list(metrics.keys())
    click.echo(tabulate.tabulate(result.values, headers=header))

    # Check the last time lab project was synced with minio
    with open(os.path.join('config', 'runtime.yaml'), 'r') as file:
            minio_config = yaml.load(file)
            push_time = datetime.datetime.fromtimestamp(0)
            try:
                push_time = datetime.datetime.strptime(minio_config['last_push'], '%Y-%m-%d %H:%M:%S.%f')
                now_time = datetime.datetime.now()
                td = now_time-push_time
                (days, hours) = (td.days, td.seconds//3600)
            except:
                (days, hours) = (0, 0)
    
    click.secho('\nLast push: '+str(days)+'d, ' + str(hours)+'h ago',
                fg='yellow')

    # Find the latest file and print its timestamp
    list_of_files = glob.glob(os.path.join(os.getcwd(), '*'))
    latest_file = max(list_of_files, key=os.path.getctime)
    latest_file_timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(latest_file))

    recommend = ' | Project is in sync with remote'
    if latest_file_timestamp > push_time:
        recommend = ' | Recommend to run <lab push>'
    click.secho('Last modified: '+str(latest_file_timestamp)+recommend,
                fg='yellow')


@click.command(name='notebook')
@click.option('--notebook', is_flag=True)
def lab_notebook(notebook):
    """ Launch a jupyter notebook """
    if not os.path.isdir('.venv'):
        click.secho("Doesn't looks like this is a valid "
                    'Lab Project as .venv is missing.', fg='red')
        raise click.Abort()

    if not os.path.isdir('config'):
        click.secho("Doesn't looks like this is a valid "
                    'Lab Project as config is missing.', fg='red')
        raise click.Abort()
    
    with open(os.path.join(os.getcwd(),
              'config', 'runtime.yaml'), 'r') as file:
        config = yaml.load(file)
    project_name = config['name'] + '_' + ''.join(e for e in config['timestamp'] if e.isalnum())

    _launch_lab_notebook(project_name, notebook)

def _launch_lab_notebook(project_name, notebook):

    venv_dir = os.path.join(os.getcwd(), '.venv')
    subprocess.call([venv_dir + '/bin/pip', 'install', 'ipykernel'])
    subprocess.call([venv_dir + '/bin/ipython', 'kernel', 'install', '--user', '--name='+project_name])

    call='lab'
    if notebook:
        call='notebook'
    subprocess.call([venv_dir + '/bin/jupyter', call,
        '--NotebookApp.notebook_dir=notebooks'])

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
    
    home_dir = os.getcwd()
    click.secho('Checking global lab version...', fg='blue')
    # Extract lab version from virtual environment
    pyversion = '%s.%s' % (sys.version_info[0], sys.version_info[1])
    venv = '%s/lib/python%s/site-packages/%s' % ('.venv', pyversion, 'lab')

    python_bin = os.path.join(home_dir, '.venv', 'bin/python')
    call = 'import lab; print(lab.__version__)'
    venv_lab_version = subprocess.check_output([python_bin, '-c', '%s' % call])
    venv_lab_version = venv_lab_version.decode('ascii').rstrip()

    import lab
    global_lab_version = lab.__version__

    if global_lab_version != venv_lab_version:
        click.secho('It appears that your Lab Project was built using a '
                    'different Lab version (' + venv_lab_version + ').',
                    fg='blue')
        if click.confirm('Do you want to update lab in this project?'):
            try:
                pkgobj = __import__('lab')
            except Exception as e:
                print(e)
                sys.exit(1)

            pkgdir = os.path.dirname(pkgobj.__file__)
            if os.path.exists(venv):
                shutil.rmtree(venv)
            shutil.copytree(pkgdir, venv)

    click.secho('Updating environment using requirements.txt', fg='blue')
    venv_dir = os.path.join(os.getcwd(), '.venv')
    subprocess.call([venv_dir + '/bin/pip', 'install',
                    '-r', 'requirements.txt'])
    

@click.command('pull')
@click.option('--tag', type=str, help='minio host nickname', required=True)
@click.option('--bucket', type=str, required=True,
              help='minio bucket name')
@click.option('--project', type=str, required=True,
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
@click.option('--info', is_flag=True)
@click.option('--tag', type=str, help='minio host nickname', default=None)
@click.option('--bucket', type=str, default=str(uuid.uuid4()),
              help='minio bucket name')
@click.option('--prune', is_flag=True)
@click.argument('path', type=str, default='.')
def lab_push(info, tag, bucket, path, prune):
    """ Push Lab Experiment to minio """    
    models_directory = 'experiments'
    logs_directory = 'logs'
    config_directory = 'config'

    home_dir = os.path.expanduser('~')
    lab_dir = os.path.join(home_dir, '.lab')
    if not os.path.exists(lab_dir):
        click.secho('Lab is not configured to connect to minio. '
                    'Run <lab config> to set up access points.',
                    fg='red')
        raise click.Abort()

    if not (os.path.exists(models_directory) & os.path.exists(logs_directory) & os.path.exists(config_directory)):
        click.secho('This directory lacks a valid Lab Project directory '
                    'structure. Run <lab init> to create one.',
                    fg='blue')
        raise click.Abort()

    if info:
        with open(os.path.join(config_directory, 'runtime.yaml'), 'r') as file:
            minio_config = yaml.load(file)         
        click.secho('Last push: '+minio_config['last_push'], fg='blue')
    else:
        _push_to_minio(tag, bucket, path, prune)

def _create_venv(project_name):
    # Create a virtual environment
    venv_dir = os.path.join(project_name, '.venv')

    environment = ve.EnvBuilder(symlinks=True, with_pip=True)
    environment.create(venv_dir)

    subprocess.call([venv_dir + '/bin/pip', 'install', '--upgrade', 'pip'])

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

def _pull_from_minio(tag, bucket, project_name):
    home_dir = os.path.expanduser('~')
    lab_dir = os.path.join(home_dir, '.lab')
    project_dir = os.path.join(os.getcwd(), project_name)

    try:
        with open(os.path.join(lab_dir, 'config.yaml'), 'r') as file:
            minio_config = yaml.load(file)[tag]
    except:
        click.secho('Invalid global minio connection tag.', fg='red')
        raise click.Abort()
    
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

def _push_to_minio(tag, bucket, path, prune):
    home_dir = os.path.expanduser('~')
    lab_dir = os.path.join(home_dir, '.lab')

    try:
        with open(os.path.join(lab_dir, 'config.yaml'), 'r') as file:
            minio_config = yaml.load(file)[tag]
    except KeyError as e:
        click.secho('Unable to connect to host '+tag, fg='red')
        raise click.Abort()

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

    # Prune remote if needed
    if prune:
        if click.confirm('WARNING: pruning will remove all remote files not '
                         'found in your current project. Do you want to continue?', abort=True):
            try:
                remote_objects = minioClient.list_objects(bucket, prefix=project_name, recursive=True)
                remote_objects = [obj.object_name for obj in remote_objects]
                for del_err in minioClient.remove_objects(bucket, remote_objects):
                    print("Deletion Error: {}".format(del_err))
            except ResponseError as err:
                print(err)        

    try:
        for i in range(len(input_objects)):
            minioClient.fput_object(bucket, output_objects[i],
                                    input_objects[i])
            print('Succesfully processed '+input_objects[i])
        
        with open(os.path.join('config', 'runtime.yaml'), 'r') as file:
            minio_config = yaml.load(file)
        minio_config['last_push'] = str(datetime.datetime.now())
        
        with open(os.path.join('config', 'runtime.yaml'), 'w') as file:
            yaml.safe_dump(minio_config, file, default_flow_style=False)

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
               'last_push': '',               
               'venv': '.venv'}

    with open(os.path.join(project_name,
              'config', 'runtime.yaml'), 'w') as file:
        yaml.dump(runtime, file, default_flow_style=False)
