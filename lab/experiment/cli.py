import click
import os
import subprocess
import yaml
import shutil
import sys
import tabulate
import pandas as pd
import numpy as np

from lab.project.cli import _create_venv


@click.command('rm')
@click.argument('experiment_id', required=True)
def lab_rm(experiment_id):
    """ Remove a Lab Experiment """
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



@click.command('run')
@click.argument('script', required=True)
def lab_run(script):
    """ Run a training script """

    try:
        with open(os.path.join(os.getcwd(),
                               'config', 'runtime.yaml'), 'r') as file:
            config = yaml.load(file)
            home_dir = config['path']
    except FileNotFoundError:
        click.secho('Having trouble parsing configuration file for this '
                    "project. It's likely that this is either not a "
                    'Lab Project or the Project was created with an older '
                    'version of Lab.\n',
                    fg='red')
        raise click.Abort()
    except KeyError:
        click.secho('Looks like this Project was configured with an earlier '
                    'version of Lab. Check that config/runtime.yaml file '
                    'has a valid path key and value.', fg='red')
        raise click.Abort()
    else:
        # Update project directory if it hasn't been updated
        if home_dir != os.getcwd():
            config['path'] = os.getcwd()
            with open(os.path.join(os.getcwd(),
                      'config', 'runtime.yaml'), 'w') as file:
                yaml.dump(config, file, default_flow_style=False)

    if not os.path.exists(os.path.join(home_dir, '.venv')):
        click.secho('Virtual environment not found. '
                    'Creating one for this project',
                    fg='blue')
        _create_venv(home_dir)

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
        if click.confirm('Do you want to sync?'):
            try:
                pkgobj = __import__('lab')
            except Exception as e:
                print(e)
                sys.exit(1)

            pkgdir = os.path.dirname(pkgobj.__file__)
            if os.path.exists(venv):
                shutil.rmtree(venv)
            shutil.copytree(pkgdir, venv)

    python_bin = os.path.join(home_dir, '.venv', 'bin/python')
    subprocess.call([python_bin, script])


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
