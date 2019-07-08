import os
import yaml
import click
import shutil
import subprocess
import venv as ve

lab_project = ['experiments', 'data', 'logs', 'notebooks', 'config']


# Project
def check_minio_config(minio_tag):
    """Check that minio configuration exists"""
    home_dir = os.path.expanduser('~')
    lab_dir = os.path.join(home_dir, '.lab')

    try:
        with open(os.path.join(lab_dir, 'config.yaml'), 'r') as file:
            yaml.load(file)[minio_tag]
    except Exception as e:
        print(str(e))
        click.secho('Invalid global minio connection tag.', fg='red')
        raise click.Abort()


def is_venv(home_dir):
    """Check that virtual environment exists"""
    if not os.path.exists(os.path.join(home_dir, '.venv')):
        click.secho('Virtual environment not found. '
                    'Creating one for this project',
                    fg='blue')
        create_venv(home_dir)


def is_empty_project():
    """Check if there are any experiments in the project"""
    experiments = next(os.walk('experiments'))[1]
    if len(experiments) == 0:
        click.secho("It looks like you've started a brand new project. "
                    'Run your first experiment to generate a list of metrics.',
                    fg='blue')
        raise click.Abort()


def is_lab_project():
    """Check if the current directory is a lab project"""
    _exists = [f for f in lab_project if os.path.exists(f)]

    if len(_exists) != len(lab_project):
        click.secho('This directory does not appear to be a valid '
                    'Lab Project.\nRun <lab init> to create one.',
                    fg='red')
        raise click.Abort()


def create_venv(project_name):
    """Create a lab virtual environment"""
    # Create a virtual environment
    venv_dir = os.path.join(project_name, '.venv')

    try:
        environment = ve.EnvBuilder(system_site_packages=False,
                                    symlinks=True, with_pip=True)
        environment.create(venv_dir)

        subprocess.call([venv_dir + '/bin/pip', 'install',
                         '--upgrade', 'pip'])

        subprocess.call([venv_dir + '/bin/pip',
                         'install', '--upgrade', 'lab-ml'])

        subprocess.call([venv_dir + '/bin/pip', 'install',
                         '-r', 'requirements.txt'])

    except Exception as e:
        shutil.rmtree(venv_dir)
        click.secho('Something went wrong during .venv creation.',
                    fg='red')
        print(str(e))
        raise click.Abort()
