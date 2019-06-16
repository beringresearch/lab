import click
import os
import subprocess
import yaml
import shutil
import sys
import graphviz

from lab.experiment import show_experiment
from lab import is_lab_project, is_empty_project, is_venv


@click.command('rm')
@click.argument('experiment_id', required=True)
def lab_rm(experiment_id):
    """ Remove a Lab Experiment """

    is_lab_project()

    experiment_dir = os.path.join('experiments', experiment_id)
    logs_dir = os.path.join('logs', experiment_id)

    if not os.path.exists(experiment_dir):
        click.secho("Can't find experiment ["+experiment_id+'] in the current '
                    'directory.\nEnsure that you are in Lab Project root',
                    fg='red')
    else:
        shutil.rmtree(experiment_dir)
        shutil.rmtree(logs_dir)
        click.secho('['+experiment_id+'] removed', fg='blue')


@click.command('show')
@click.argument('experiment_id', required=False)
def lab_show(experiment_id=None):
    """ Show a Lab Experiment """

    is_lab_project()
    is_empty_project()

    models_directory = 'experiments'

    experiments = next(os.walk(models_directory))[1]

    if experiment_id is None:
        experiments = next(os.walk('experiments'))[1]
        p = graphviz.Digraph(name='lab_project', format='png')
        p.graph_attr['rankdir'] = 'LR'

        for e in experiments:
            p.subgraph(show_experiment(e))
    else:
        experiment_dir = os.path.join('experiments', experiment_id)
        if not os.path.exists(experiment_dir):
            click.secho(
                "Can't find experiment ["+experiment_id+'] in the current '
                'directory.\nEnsure that you are in Lab Project root',
                fg='red')
            click.Abort()
        else:
            p = show_experiment(experiment_id)

    p.render()


@click.command('run', context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('script', required=False,
                nargs=-1, type=click.UNPROCESSED)
def lab_run(script):
    """ Run a training script """

    home_dir = os.getcwd()

    is_lab_project()
    is_venv(home_dir)

    try:
        with open(os.path.join(os.getcwd(),
                               'config', 'runtime.yaml'), 'r') as file:
            config = yaml.load(file)
            home_dir = config['path']

            # Update project directory if it hasn't been updated
            if home_dir != os.getcwd():
                config['path'] = os.getcwd()
                with open(os.path.join(os.getcwd(),
                                       'config', 'runtime.yaml'), 'w') as file:
                    yaml.dump(config, file, default_flow_style=False)
    except KeyError:
        click.secho('Looks like this Project was configured with an earlier '
                    'version of Lab. Check that config/runtime.yaml file '
                    'has a valid path key and value.', fg='red')
        raise click.Abort()

    # Extract lab version from virtual environment
    click.secho('Intializing', fg='cyan')

    python_bin = os.path.join(home_dir, '.venv', 'bin/python')

    click.secho('Running '+str(script), fg='green')
    subprocess.call([python_bin] + list(script))
    click.secho('Finished!', fg='green')
