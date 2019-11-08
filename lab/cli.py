import click
import os
import warnings
import yaml
import sys
import pkg_resources

from minio import Minio
from urllib3.exceptions import MaxRetryError

from lab.project import cli as lab_project
from lab.experiment import cli as lab_experiment

working_directory = os.getcwd()
warnings.filterwarnings("ignore")


@click.group()
def cli():
    """
Bering's Machine Learning Lab

Copyright 2019 Bering Limited. https://beringresearch.com
"""


# Project
cli.add_command(lab_project.lab_init)
cli.add_command(lab_project.lab_push)
cli.add_command(lab_project.lab_pull)
cli.add_command(lab_project.lab_ls)
cli.add_command(lab_project.lab_update)
cli.add_command(lab_project.lab_notebook)

# Experiment
cli.add_command(lab_experiment.lab_run)
cli.add_command(lab_experiment.lab_rm)
cli.add_command(lab_experiment.lab_show)


# Lab configuration
@click.group()
def config():
    """ Global Lab configuration """
    pass


@click.command('info')
def lab_info():
    """ Display system-wide information """
    import multiprocessing
    import platform

    lab_version = pkg_resources.require('lab-ml')[0].version

    system_version = str(sys.version_info[0]) + '.' + \
        str(sys.version_info[1]) + \
        '.' + str(sys.version_info[2])
    home_dir = os.path.expanduser('~')
    lab_dir = os.path.join(home_dir, '.lab')

    # Test connection
    if not os.path.exists(lab_dir):
        n_minio_hosts = 0
    else:
        with open(os.path.join(lab_dir, 'config.yaml'), 'r') as file:
            minio_config = yaml.safe_load(file)
        n_minio_hosts = len(minio_config.keys())

    click.echo('😎  Lab version: '+str(lab_version))
    click.echo('Minio hosts: '+str(n_minio_hosts)+'\n')
    click.echo('Operating System: '+platform.system())
    click.echo('Python version: '+system_version)
    click.echo('CPUs: '+str(multiprocessing.cpu_count()))


@click.command('minio')
@click.option('--tag', type=str, help='helpful minio host tag', required=True)
@click.option('--endpoint', type=str, help='minio endpoint address',
              required=True)
@click.option('--accesskey', type=str, help='minio access key', required=True)
@click.option('--secretkey', type=str, help='minio secret key', required=True)
def minio_config(tag, endpoint, accesskey, secretkey):
    """ Setup remote minio host """
    home_dir = os.path.expanduser('~')
    lab_dir = os.path.join(home_dir, '.lab')

    # Test connection
    if not os.path.exists(lab_dir):
        os.makedirs(lab_dir)

    try:
        minioClient = Minio(endpoint,
                            access_key=accesskey,
                            secret_key=secretkey,
                            secure=False)
        minioClient.list_buckets()
    except MaxRetryError:
        click.secho('Cannot connect to minio instance. Check your credentials '
                    'and hostname. Ensure that endpoint is not prefixed with'
                    'http or https.', fg='red')
        raise click.Abort()

    # Create configuration
    config = {'minio_endpoint': endpoint,
              'minio_accesskey': accesskey,
              'minio_secretkey': secretkey}

    if os.path.exists(os.path.join(lab_dir, 'config.yaml')):
        with open(os.path.join(lab_dir, 'config.yaml'), 'r') as file:
            minio_config = yaml.safe_load(file)
            if tag in minio_config.keys():
                click.secho('Host tag '+tag+' already exists in your '
                            'configuration. Try a different name.', fg='red')
                raise click.Abort()

            minio_config[tag] = config
    else:
        minio_config = {}
        minio_config[tag] = config

    with open(os.path.join(lab_dir, 'config.yaml'), 'w') as file:
        yaml.safe_dump(minio_config, file, default_flow_style=False)


cli.add_command(config)
cli.add_command(lab_info)
config.add_command(minio_config)

if __name__ == '__main__':
    cli()
