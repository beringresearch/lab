import click
import os
import yaml
import tabulate
import warnings
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

from lab.server import _run_server
from lab import Project


@click.group()
def cli():
    '''Machine Learning Lab'''
    pass

@click.command('serve')
@click.argument('experiment_id', required = True)
@click.argument('model_name', required = True)
def serve_model(experiment_id, model_name):
    _run_server(experiment_id, model_name)

@click.command('run')
@click.argument('labdir', default = '.', required = False)
def run_project(labdir='.'):
    labfile = os.path.join(labdir, 'labfile.yaml')
    if os.path.isfile(labfile):
        p = Project(labfile)
        p.start_run()
    else:
        raise Exception('Directory is not a valid Lab Project. Initiate a labfile.yaml and run again.')

@click.command('create')
@click.argument('name', required = True)
def create_project(name):
    with open('labfile.yaml', 'w') as file:
            meta = {'name': name,
                    'entry_points': None}
            yaml.dump(meta, file, default_flow_style=False)

@click.command('ls')
@click.argument('sort_by', required = False)
def compare_experiments(sort_by = None):
    experiment_directory = 'labrun'
    
    if os.path.isdir(experiment_directory):
        experiments = next(os.walk(experiment_directory))[1]
    else:
        raise Exception("lab ls must be run from a directory that contains labruns folder.")
    
    TICK = '█'

    comparisons = []    
    for e in experiments:
        metrics_file = os.path.join(experiment_directory, e, 'metrics.yaml')
        with open(metrics_file, 'r') as file:
            metrics = yaml.load(file)
        for k, v in metrics.items():
            metrics[k] = round(v, 2)        
        
        metrics_list = list(metrics.values())
        
        meta_file = os.path.join(experiment_directory, e, 'meta.yaml')
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


cli.add_command(run_project)
cli.add_command(serve_model)
cli.add_command(create_project)
cli.add_command(compare_experiments)

if __name__ == '__main__':
    cli()
