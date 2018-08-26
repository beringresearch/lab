import click
import os
import yaml
import tabulate

from lab.server import _run_server
from lab import Project


@click.group()
def cli():
    '''Machine Learning Lab'''
    pass

@click.command('serve')
@click.argument('model_id', required = True)
def serve_model(model_id):
    _run_server(model_id)

@click.command('run')
@click.argument('labdir', required = False)
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

@click.command('ui')
def compare_experiments():
    experiment_directory = 'labrun'
    
    if os.path.isdir(experiment_directory):
        experiments = next(os.walk(experiment_directory))[1]
    else:
        raise("lab ls must be run from a directory that contains labruns folder.")

    
    TICK = '▇'

    comparisons = []
    
    for e in experiments:
        metrics_file = os.path.join(experiment_directory, e, 'metrics.yaml')
        with open(metrics_file, 'r') as file:
            metrics = yaml.load(file)

        for k, v in metrics.items():
            metrics[k] = round(v, 2)

        meta_file = os.path.join(experiment_directory, e, 'meta.yaml')
        with open(meta_file, 'r') as file:
            meta = yaml.load(file)
        
        record = [meta['experiment_uuid'], meta['user_id'], str(meta['start_time'].date()), metrics]
        comparisons.append(record)
        
    header = ['Experiment', 'User', 'Time', 'Metrics']

    click.echo(tabulate.tabulate(comparisons, headers = header))
        

        


cli.add_command(run_project)
cli.add_command(serve_model)
cli.add_command(create_project)
cli.add_command(compare_experiments)

if __name__ == '__main__':
    cli()
