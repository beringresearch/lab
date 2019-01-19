import click
import os
import uuid
import yaml
import tabulate
import subprocess
from minio import Minio

import warnings
import pandas as pd
import numpy as np

from lab import project_init, create_venv, push_to_minio
import lab.version as lab_version

working_directory = os.getcwd()
warnings.filterwarnings("ignore")

@click.group()
def cli():
    """
    \b
       o
       o
     ___
     | |
     | |
     |o|
    .' '.
   /  o  \ 
  :____o__:
  '._____.' Bering's Machine Learning Lab    

    \b
    Quickstart:
    1. Generate requirements.txt
    2. Create a new Lab Environment: lab init --name [NAME]
    3. Create a python script with your experiment
    4. Run the experiment: lab run [NAME]
    5. Check performance: lab ls

    Copyright 2019 Bering Limited. https://beringresearch.com

    """
    pass

@click.command('init')
@click.option('--name', type=str, default=str(uuid.uuid4()), help='environment name')
def lab_init(name):
    """ Initialise a new Lab environment """
    if not os.path.isfile('requirements.txt'):
        click.echo('requirements.txt is not found in the current working directory.')
        raise click.Abort()

    if os.path.isdir(name):
        click.echo('Project '+name+' already exists.')
    else:
        project_init(name)

@click.command('run')
@click.argument('script', required = True)
def lab_run(script):    
    """ Run a training script """
    home_dir = os.path.dirname(os.path.realpath(script))  
    if not os.path.exists(os.path.join(home_dir, '.venv')):
        click.echo('virtual environment not found. Creating one for this project')
        create_venv(home_dir)

    python_bin = os.path.join(home_dir, '.venv', 'bin/python')
    subprocess.call([python_bin, script])

@click.command('ls')
@click.argument('sort_by', required = False)
def compare_experiments(sort_by = None):
    """ Compare multiple Lab Experiments """
    models_directory = 'models'
    logs_directory = 'logs'
    TICK = '█'

    if not os.path.exists(models_directory):
        click.echo('This directory does not appear to contain a valid lab project. Run lab init to create one.')
        click.Context.abort(cli)
    
    experiments = next(os.walk(models_directory))[1]
    if len(experiments) == 0:
        click.echo("It looks like you've started a brand new project. Run your first experiment to generate a list of metrics.")
        click.Context.abort(cli)
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
                            
            record = [meta['experiment_uuid'], meta['source'], str(meta['start_time'].date())] + metrics_list
            comparisons.append(record)
        except:
            pass

    # Create visualisation of numeric metrics
    try:
        A = pd.DataFrame(comparisons)
        meta_data = A[[0, 1, 2]]
        metrics_data = A.drop([0, 1, 2], axis = 1)
    
        row_max = metrics_data.abs().max(axis = 0)    
        scaled_metrics_data = metrics_data.abs().divide(row_max, axis = 1)
        scaled_metrics_data = scaled_metrics_data.fillna(value = 0)
    
        sparklines = np.empty(shape = metrics_data.shape, dtype=object)
        for row in range(metrics_data.shape[0]):
            for column in range(metrics_data.shape[1]):
                value = metrics_data.iloc[row, column]
                scaled_value = scaled_metrics_data.iloc[row, column]
                scaled_value = scaled_value
                spark = format(value, '.2f')+': '+TICK * int(round(scaled_value*10))
                sparklines[row, column] = spark

        result = pd.concat([meta_data, pd.DataFrame(sparklines)], axis = 1)
        result.columns = ['Experiment', 'Source', 'Date'] + list(metrics.keys())    

        if sort_by is not None:
            result.sort_values(by = [sort_by], axis = 0, ascending=False, inplace = True)

        header = ['Experiment', 'Source', 'Date'] + list(metrics.keys())
        click.echo(tabulate.tabulate(result.values, headers = header))
    except:
        pass

@click.command('push')
@click.argument('path', type=str, default=os.getcwd())
def lab_push(path):
    models_directory = 'models'
    logs_directory = 'logs'

    home_dir = os.path.expanduser('~')
    lab_dir = os.path.join(home_dir, '.lab')
    if not os.path.exists(lab_dir):
        click.echo('Lab is not configured to connect to minio. Run lab config to set up access points.')
        click.Context.abort(cli)

    if not (os.path.exists(models_directory) & os.path.exists(logs_directory)):
        click.echo('This directory does not appear to contain a valid lab project. Run lab init to create one.')
        click.Context.abort(cli)
    
    push_to_minio(path)

    

@click.command('config')
@click.option('--endpoint', type=str, help='minio endpoint address')
@click.option('--accesskey', type=str, help='minio access key')
@click.option('--secretkey', type=str, help='minio secret key')
def lab_config(endpoint, accesskey, secretkey):
    """ Configure the lab environment and setup remote file storage"""
    home_dir = os.path.expanduser('~')
    lab_dir = os.path.join(home_dir, '.lab')
    if not os.path.exists(lab_dir):
        os.makedirs(lab_dir)

    try:
        minioClient = Minio(endpoint,
                  access_key=accesskey,
                  secret_key=secretkey,
                  secure=False)
    except:
        click.echo('Cannot connect to minio instance. Check your credentials and hostname. Ensure that endpoint is not prefixed with http or https.')
        click.Context.abort(cli)

    
    config = {'minio_endpoint': endpoint,
              'minio_accesskey': accesskey,
              'minio_secretkey': secretkey}

    with open(os.path.join(lab_dir, 'config.yaml'), 'w') as file:
        yaml.dump(config, file, default_flow_style=False)

cli.add_command(lab_init)
cli.add_command(lab_run)
cli.add_command(compare_experiments)
cli.add_command(lab_config)
cli.add_command(lab_push)

if __name__ == '__main__':
    cli()
