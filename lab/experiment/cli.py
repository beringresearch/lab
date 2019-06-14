import click
import os
import subprocess
import yaml
import shutil
import sys
import graphviz

from lab.project.cli import _create_venv
from lab.experiment import show_experiment


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


@click.command('show')
@click.argument('experiment_id', required=False)
def lab_show(experiment_id=None):
    """ Show a Lab Experiment """
    models_directory = 'experiments'

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

    if experiment_id is None:
        experiments = next(os.walk('experiments'))[1]
        p = graphviz.Digraph(name='lab_project', format='png')
        p.graph_attr['rankdir'] = 'LR'

        for e in experiments:
            p.subgraph(show_experiment(e))
    else:
        experiment_dir = os.path.join('experiments', experiment_id)
        if not os.path.exists(experiment_dir):
            click.secho("Can't find experiment ["+experiment_id+'] in the current '
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

    if not os.path.exists(os.path.join(home_dir, '.venv')):
        click.secho('Virtual environment not found. '
                    'Creating one for this project',
                    fg='blue')
        _create_venv(home_dir)

    # Extract lab version from virtual environment
    click.secho('Intializing', fg='cyan')
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

    click.secho('Running '+str(script), fg='green')
    subprocess.call([python_bin] + list(script))
    click.secho('Finished!', fg='green')
