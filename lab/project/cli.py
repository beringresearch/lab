import click
import uuid
import glob
import os
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

from lab import is_empty_project, is_lab_project, create_venv,\
    check_minio_config


@click.command('ls')
@click.argument('sort_by', required=False)
def lab_ls(sort_by=None):
    """ Compare multiple Lab Experiments """
    models_directory = 'experiments'
    logs_directory = 'logs'
    TICK = '█'

    is_lab_project()
    is_empty_project()

    experiments = next(os.walk(models_directory))[1]
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

            # Truncate source name if too long
            source_name = meta['source']
            meta['source'] = (source_name[:20] +
                              '..') if len(source_name) > 20 else source_name

            record = [meta['experiment_uuid'], meta['source'],
                      meta['start_time'].strftime("%m/%d/%Y, %H:%M:%S")] + \
                metrics_list
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

    result.sort_values(by=['Date'], axis=0, ascending=False,
                       inplace=True)

    if sort_by is not None:
        result.sort_values(by=[sort_by], axis=0,
                           ascending=False, inplace=True)

    header = ['Experiment', 'Source', 'Date'] + list(metrics.keys())
    click.echo('')
    click.echo(tabulate.tabulate(result.values, headers=header))

    # Check the last time lab project was synced with minio
    with open(os.path.join('config', 'runtime.yaml'), 'r') as file:
            minio_config = yaml.load(file)
            push_time = datetime.datetime.fromtimestamp(0)
            try:
                push_time = \
                    datetime.datetime.strptime(
                        minio_config['last_push'],
                        '%Y-%m-%d %H:%M:%S.%f')

                now_time = datetime.datetime.now()
                td = now_time-push_time
                (days, hours) = (td.days, td.seconds//3600)
            except Exception:
                (days, hours) = (0, 0)

    click.secho('\nLast push: '+str(days)+'d, ' + str(hours)+'h ago',
                fg='yellow')

    # Find the latest file and print its timestamp
    list_of_files = glob.glob(os.path.join(os.getcwd(), '*'))
    latest_file = max(list_of_files, key=os.path.getctime)
    latest_file_timestamp = \
        datetime.datetime.fromtimestamp(os.path.getmtime(latest_file))

    recommend = '| Project is in sync with remote'
    if latest_file_timestamp > push_time:
        recommend = ' | Recommend to run <lab push>'
    click.secho('Last modified: '+str(latest_file_timestamp)+recommend,
                fg='yellow')


@click.command(name='notebook')
def lab_notebook():
    """ Publish Lab project as a jupyter kernel """
    is_lab_project()

    with open(os.path.join(os.getcwd(),
              'config', 'runtime.yaml'), 'r') as file:
        config = yaml.load(file)
    project_name = config['name'] + '_' +\
        ''.join(e for e in config['timestamp'] if e.isalnum())

    click.secho('Generating jupyter kernel for ' + config['name'] + '...',
                fg='cyan')

    try:
        _install_jupyter_kernel(project_name)
        click.secho('Kernel generated: ' + project_name)
    except Exception as e:
        print(e)
        click.secho('Failed to generate kernel.', fg='red')


def _install_jupyter_kernel(project_name):

    venv_dir = os.path.join(os.getcwd(), '.venv')
    subprocess.call([venv_dir + '/bin/pip', 'install', 'ipykernel'])
    subprocess.call([venv_dir + '/bin/ipython', 'kernel', 'install',
                     '--user', '--name='+project_name])


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
        try:
            _project_init(name)
        except Exception as e:
            print(e)
            click.secho('Errors encountered during project initialisation.'
                        'Rolling back..', fg='red')
            raise click.Abort()


@click.command(name='update')
def lab_update():
    """ Update Lab Environment from Project's requirements.txt """
    if not os.path.isfile('requirements.txt'):
        click.secho('requirements.txt file is missing.', fg='red')
        raise click.Abort()

    # Update project directory if it hasn't been updated
    try:
        with open(os.path.join(os.getcwd(),
                               'config', 'runtime.yaml'), 'r') as file:
            config = yaml.load(file)
            home_dir = config['path']

            if home_dir != os.getcwd():
                config['path'] = os.getcwd()
                with open(os.path.join(os.getcwd(),
                                       'config', 'runtime.yaml'), 'w') as file:
                    yaml.dump(config, file, default_flow_style=False)
    except FileNotFoundError:
        click.secho('Having trouble parsing configuration file for this '
                    "project. It's likely that this is either not a "
                    'Lab Project or the Project was created with an older '
                    'version of Lab.\n',
                    fg='red')
        raise click.Abort()

    if not os.path.isdir('.venv'):
        click.secho("Couldn't find .venv. Creating one for you...",
                    fg='blue')
        create_venv('')

    home_dir = os.getcwd()
    venv_dir = os.path.join(home_dir, '.venv')

    click.secho('Updating lab', fg='cyan')
    subprocess.call([venv_dir + '/bin/pip',
                     'install', '--upgrade', 'lab-ml'])

    click.secho('Updating environment using requirements.txt', fg='cyan')
    subprocess.call([venv_dir + '/bin/pip', 'install', '--upgrade',
                    '-r', 'requirements.txt'])


@click.command('pull')
@click.option('--tag', type=str,
              help='minio host nickname', required=False, default=None)
@click.option('--bucket', type=str, required=False, default=None,
              help='minio bucket name')
@click.option('--project', type=str, required=False, default=None,
              help='Lab Project name')
@click.option('--force', is_flag=True)
def lab_pull(tag, bucket, project, force):
    """ Pulls Lab Experiment from minio to current directory """
    home_dir = os.path.expanduser('~')

    lab_dir = os.path.join(home_dir, '.lab')

    if not os.path.exists(lab_dir):
        click.secho('Lab is not configured to connect to minio. '
                    'Run <lab config> to set up access points.',
                    fg='red')
        raise click.Abort()

    if project is not None:
        if os.path.exists(project):
            click.secho('Directory '+project+' already exists.', fg='red')
            raise click.Abort()

    _pull_from_minio(tag, bucket, project, force)


@click.command('push')
@click.option('--info', is_flag=True)
@click.option('--tag', type=str, help='minio host nickname', default=None)
@click.option('--bucket', type=str, default=None,
              help='minio bucket name')
@click.option('--force', is_flag=True)
@click.argument('path', type=str, default='.')
def lab_push(info, tag, bucket, path, force):
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

    if not (os.path.exists(models_directory) &
            os.path.exists(logs_directory) & os.path.exists(config_directory)):
        click.secho('This directory lacks a valid Lab Project directory '
                    'structure. Run <lab init> to create one.',
                    fg='blue')
        raise click.Abort()

    if info:
        with open(os.path.join(config_directory, 'runtime.yaml'), 'r') as file:
            minio_config = yaml.load(file)
        click.secho('Last push: '+minio_config['last_push'], fg='blue')
    else:
        if (tag is None) & (bucket is None):
            try:
                with open(os.path.join(config_directory, 'runtime.yaml'),
                          'r') as file:
                    minio_config = yaml.load(file)
                    tag = minio_config['tag']
                    bucket = minio_config['bucket']
            except KeyError:
                click.secho(
                    'Lab project does not have default tag and bucket configuration. '
                    'Supply --tag and --bucket options and run lab push again.',
                        fg='red')
                raise click.Abort()
        else:
            with open(os.path.join(config_directory, 'runtime.yaml'),
                      'r') as file:
                minio_config = yaml.load(file)
                minio_config['tag'] = tag
                minio_config['bucket'] = bucket
            with open(os.path.join(config_directory, 'runtime.yaml'),
                      'w') as file:
                yaml.safe_dump(minio_config, file, default_flow_style=False)

        _push_to_minio(tag, bucket, path, force)


def _pull_from_minio(tag, bucket, project_name, force):
    click.secho('Looking up remote..', fg='cyan')

    home_dir = os.path.expanduser('~')
    lab_dir = os.path.join(home_dir, '.lab')
    project_dir = os.getcwd()

    _clone = True

    # Extract bucket name and project name from config if they are present
    if (tag is None) & (bucket is None) & (project_name is None):
        _clone = False

        with open(os.path.join(project_dir,
                               'config', 'runtime.yaml'), 'r') as file:
            project_config = yaml.load(file)
            bucket = project_config['bucket']
            project_name = project_config['name']
            tag = project_config['tag']

    check_minio_config(tag)

    # Extract minio configuration
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
        click.secho('Bucket ' + bucket + ' is not found on remote', fg='red')
        raise click.Abort()
    try:
        objects = minioClient.list_objects(bucket, prefix=project_name+'/',
                                           recursive=True)

        remote_objects = [o.object_name for o in objects]

        if _clone is False:
            if force:
                local_objects = []
            else:
                local_objects = _list_dir('.')

                local_objects = [l.replace('./', project_name+'/')
                                 for l in local_objects]

            remote_objects = list(set(remote_objects) - set(local_objects))

        if len(remote_objects) == 0:
            click.secho('Project is in sync with remote. '
                        'Use <lab pull --force> to do a hard pull.',
                        fg='yellow')
            raise click.Abort()

        click.secho('Fetching '+str(len(remote_objects))+' remote objects.',
                    fg='cyan')

        for obj in remote_objects:
            if _clone:
                object_name = obj
            else:
                object_name = ''.join(obj.split(project_name + '/')[1:])
            print('Downloading ' + object_name)
            minioClient.fget_object(bucket, obj,
                                    os.path.join(os.getcwd(), object_name))
    except ResponseError as err:
        print(err)


def _list_dir(path):
    files = []
    # r=root, d=directories, f = files
    for r, d, f in os.walk(path):
        for file in f:
            files.append(os.path.join(r, file))
    return(files)


def _push_to_minio(tag, bucket, path, force):
    home_dir = os.path.expanduser('~')
    lab_dir = os.path.join(home_dir, '.lab')

    try:
        with open('.labignore') as f:
            exclude = set(f.read().splitlines())
    except Exception:
        exclude = set(['.venv'])

    try:
        with open(os.path.join(lab_dir, 'config.yaml'), 'r') as file:
            minio_config = yaml.load(file)[tag]
    except KeyError as e:
        print(str(e))
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
    if force:
        if click.confirm(
            'WARNING: force push will remove all remote files not '
            'found in your current project. Do you want to continue?',
                abort=True):
            try:
                remote_objects = minioClient.list_objects(bucket,
                                                          prefix=project_name,
                                                          recursive=True)
                remote_objects = [obj.object_name for obj in remote_objects]
                for del_err in minioClient.remove_objects(bucket,
                                                          remote_objects):
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
    open(os.path.join(project_name, 'notebooks', 'README.md'), 'a').close()

    file = open(os.path.join(project_name, '.gitignore'), 'w')
    file.write('.venv')
    file.close()

    # ignore these files when pushing lab repo to minio
    file = open(os.path.join(project_name, '.labignore'), 'w')
    file.write('.venv')
    file.write('.ipynb_checkpoints')
    file.close()

    # Copy requirements.txt file
    shutil.copyfile('requirements.txt', project_name+'/requirements.txt')

    # Create a virtual environment
    create_venv(project_name)

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
