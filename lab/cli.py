import click
import os
import uuid
import yaml
import tabulate
import subprocess

import warnings
import pandas as pd
import numpy as np

from lab import project_init, create_venv

working_directory = os.getcwd()
warnings.filterwarnings("ignore")

@click.group()
def cli():
    '''Machine Learning Lab'''
    pass

@click.command('init')
@click.argument('name', type=str, default=str(uuid.uuid4()))
def lab_init(name):
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
    home_dir = os.path.dirname(os.path.realpath(script))  
    if not os.path.exists(os.path.join(home_dir, '.venv')):
        click.echo('virtual environment not found. Creating one for this project')
        create_venv(home_dir)

    python_bin = os.path.join(home_dir, '.venv', 'bin/python')
    subprocess.call([python_bin, script])

@click.command('ls')
@click.argument('sort_by', required = False)
def compare_experiments(sort_by = None):
    models_directory = 'models'
    logs_directory = 'logs'
    
    if os.path.isdir(models_directory):
        experiments = next(os.walk(models_directory))[1]
    else:
        raise Exception("lab ls must be run from a directory that contains models folder.")
    
    TICK = '█'

    comparisons = []    
    for e in experiments:
        metrics_file = os.path.join(models_directory, e, 'metrics.yaml')
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

    # Create visualisation of numeric metrics
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

cli.add_command(lab_init)
cli.add_command(lab_run)
cli.add_command(compare_experiments)

if __name__ == '__main__':
    cli()
