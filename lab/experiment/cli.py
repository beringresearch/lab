import click
import os
import subprocess
import yaml
import shutil
import sys

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
@click.argument('script', required=True, nargs=-1)
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
    subprocess.call([python_bin] + list(script))