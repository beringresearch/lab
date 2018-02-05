''' Command line interface to Machine Learning Lab '''
import uuid
import json
import os
import shutil
import datetime
import subprocess
import click
from tabulate import tabulate
from train import train_r
from pymongo import MongoClient
from pkg_resources import Requirement, resource_filename

from .alerts import EmailAlerter

try:
    email_settings_filepath = resource_filename(Requirement.parse("lab"), "email_config_testing.json")
except:
    print('Could not load email settings config file.')
finally:
    email_alerter = EmailAlerter.from_filepath(email_settings_filepath)


def execute_learner(identifier=''):
    '''Main function that executes shell script'''
    client = MongoClient()
    mongodb = client.lab
    experiments = mongodb.experiments

    if identifier == '':
        with open('experiment.json', 'r') as file:
            experiment = json.load(file)
    else:
        listing = experiments.find_one({"_id": identifier})
        with open(os.path.join(listing['ewd'], 'experiment.json'), 'r') as file:
            experiment = json.load(file)

    experiments.update({'_id': experiment['_id']}, {"$set": experiment}, upsert=False)
    ewd = experiment['ewd']
    experimentjson = os.path.join(ewd, 'experiment.json')
    learner = os.path.join(ewd, experiment['learner'])
    cmd = [experiment['command'], experiment['args'], learner, experimentjson]
    cmd = filter(None, cmd)
    stdout = open(os.path.join(ewd, 'stdout.log'), 'w')
    stderr = open(os.path.join(ewd, 'stderr.log'), 'w')
    
    try:
        subprocess.check_call(cmd, shell=False, stdout=stdout, stderr=stderr)
        print('Completed running {}'.format(ewd))
        email_alerter.send_message(experiment['name'], ewd, success=True)
    except Exception as e:
        print('Error encountered running experiment {}.'.format(ewd))
        print(e)
        email_alerter.send_message(experiment['name'], ewd, success=False)

@click.group()
def cli():
    '''Machine Learning Lab'''
    pass


# Project Group
@click.group()
def project():
    '''Project commands'''
    pass

# Create a new Project
@click.command('create')
@click.argument('name')
def create_project(name):
    '''Create a new project with NAME.'''
    timestamp = str(datetime.datetime.utcnow())
    projectid = str(uuid.uuid4())[:8]

    project_list = {}
    project_list['name'] = name
    project_list['_id'] = projectid
    project_list['timestamp'] = timestamp
    project_list['pwd'] = os.path.join(os.getcwd(), name)
    project_list['ewd'] = os.path.join(os.getcwd(), name, 'experiments')
    project_list['data'] = os.path.join(os.getcwd(), name, 'data')
    projectdir = name

    if not os.path.exists(projectdir):
        os.makedirs(projectdir)
        datadir = os.path.join(projectdir, 'data')
        exprdir = os.path.join(projectdir, 'experiments')
        os.makedirs(datadir)
        os.makedirs(exprdir)

        with open(os.path.join(project_list['pwd'], 'project.json'), 'w') as file:
            json.dump(project_list, file, sort_keys=False, indent=2)

        client = MongoClient()
        mongodb = client.lab
        projects = mongodb.projects
        projects.insert_one(project_list)

        click.echo('Project created {id=' + projectid + '}')

# List existing lab projects
@click.command('ls')
def ls_project():
    '''List all projects'''
    client = MongoClient()
    mongodb = client.lab
    projects = mongodb.projects

    listing = list(projects.find())

    project_list = []
    for iteration in listing:
        project_list.append([iteration['_id'], iteration['name'],
                             os.path.split(iteration['ewd'])[0]])

    table = [['id', 'name', 'directory']]
    for element in range(0, len(project_list)):
        table.append(project_list[element])
    click.echo(tabulate(table, tablefmt='presto', headers='firstrow'))

# Remove a lab project
@click.command('rm')
@click.argument('identifier')
def rm_project(identifier):
    '''Remove project by IDENTIFIER'''
    client = MongoClient()
    mongodb = client.lab
    projects = mongodb.projects

    listing = projects.find_one({"_id": identifier})
    pwd = listing['pwd']
    if os.path.exists(pwd):
        shutil.rmtree(pwd)

    projects.remove({"_id": identifier})

    click.echo('Removed project {id=%s}' % identifier)

# Run all experiments in a project
@click.command('run')
@click.argument('identifier')
def run_project(identifier):
    ''' Run all experiments associated with the project IDENTIFIER'''
    client = MongoClient()
    mongodb = client.lab
    projects = mongodb.projects

    listing = projects.find_one({"_id": identifier})
    ewd = listing['ewd']    

    for experiment_id in os.listdir(ewd):
        click.echo('Running experiment {id=%s}' % experiment_id)
        execute_learner(experiment_id)
    
    click.echo('Executed project {id=%s}' % identifier)

# Experiment Group
@click.group()
def expr():
    '''Experiment methods'''
    pass

# Create a new Experiment
@click.command('create')
@click.argument('name', default='', required=False)
def create_experiment(name):
    '''Create a new experiment'''
    timestamp = str(datetime.datetime.utcnow())
    exprid = str(uuid.uuid4())[:8]

    if name == "":
        name = exprid

    experiment = {}
    experiment['_id'] = exprid
    experiment['name'] = name
    experiment['timestamp'] = timestamp
    experiment['ewd'] = os.path.join(os.getcwd(), exprid)
    experiment['command'] = 'Rscript'
    experiment['args'] = '--vanilla'
    experiment['data'] = ''
    experiment['x'] = []
    experiment['y'] = ''
    experiment['learner'] = 'train.R'
    experiment['method'] = ''
    experiment['options'] = {}
    experiment['seed'] = '123'
    experiment['results'] = 'output'

    os.makedirs(experiment['ewd'])

    with open(os.path.join(experiment['ewd'], 'experiment.json'), 'w') as file:
        json.dump(experiment, file, sort_keys=False, indent=2)

    with open(os.path.join(experiment['ewd'], 'train.R'), 'w') as file:
        file.write(train_r())

    client = MongoClient()
    mongodb = client.lab
    experiments = mongodb.experiments
    experiments.insert_one(experiment)

    click.echo('Experiment created {id=' + exprid + '}')

# List existing lab experiments
@click.command('ls')
def ls_experiment():
    '''List all registered experiments'''
    client = MongoClient()
    mongodb = client.lab
    experiments = mongodb.experiments

    listing = list(experiments.find())

    experiment = []
    for iteration in listing:
        experiment.append([iteration['_id'], iteration['name'], iteration['method'],
                           iteration['y'],
                           os.path.split(iteration['ewd'])[0]])

    table = [['id', 'name', 'method', 'response', 'directory']]
    for element in range(0, len(experiment)):
        table.append(experiment[element])

    click.echo(tabulate(table, tablefmt='presto', headers='firstrow'))


# Duplicate a specific experiment
@click.command('duplicate')
@click.argument('identifier')
def duplicate_experiment(identifier):
    '''Duplicate experiment with an IDENTIFIER'''
    timestamp = str(datetime.datetime.utcnow())
    exprid = str(uuid.uuid4())[:8]

    client = MongoClient()
    mongodb = client.lab
    experiments = mongodb.experiments
    experiment = experiments.find_one({"_id": identifier})

    ewd = experiment['ewd']
    experiment['_id'] = exprid
    experiment['timestamp'] = timestamp
    experiment['ewd'] = os.path.join(os.getcwd(), exprid)

    experiments.insert_one(experiment)

    os.makedirs(experiment['ewd'])
    shutil.copy2(os.path.join(ewd, 'experiment.json'), experiment['ewd'])
    shutil.copy2(os.path.join(ewd, experiment['learner']), experiment['ewd'])

    with open(os.path.join(experiment['ewd'], 'experiment.json'), 'w') as file:
        json.dump(experiment, file, sort_keys=False, indent=2)

    click.echo("Created experiment {id=%s}" % exprid)


# Remove an experiment
@click.command('rm')
@click.argument('identifier')
def rm_experiment(identifier):
    '''Permanently remove experiment by IDENTIFIER'''
    client = MongoClient()
    mongodb = client.lab
    experiments = mongodb.experiments

    listing = experiments.find_one({"_id": identifier})
    ewd = listing['ewd']

    if os.path.exists(ewd):
        shutil.rmtree(ewd)

    experiments.remove({"_id": identifier})

    click.echo('Removed experiment {id=%s}' % identifier)

# Run Experiment
@click.command('run')
@click.argument('identifier', default='', required=False)
def run_experiment(identifier):
    '''Run a single experiment by IDENTIFIER'''
    timestamp = str(datetime.datetime.utcnow())
    click.echo('Starting on %s' % timestamp)
    execute_learner(identifier)
    timestamp = str(datetime.datetime.utcnow())
    click.echo('Finished on %s' % timestamp)

# Compare experiments
@click.command('perf')
@click.argument('identifier', required=True, nargs=-1)
@click.argument('metric', required=True, nargs=1)
def perf_experiment(identifier, metric):
    '''Show performance by exp IDENTIFIER and METRIC'''
    client = MongoClient()
    mongodb = client.lab
    experiments = mongodb.experiments

    for i in identifier:
        listing = experiments.find_one({"_id": i})
        ewd = listing['ewd']
        results = os.path.join(ewd, listing['results'])
        performances = [pos_json for pos_json in os.listdir(results) if pos_json.endswith('.json')]

        row = []
        for performance in performances:
            with open(os.path.join(results, performance), 'r') as file:
                experiment = json.load(file)
                row.append(experiment['performance'][metric])
        table = [performances, row]
        click.echo('\n* '+str(i)+': %s' % metric)
        click.echo(tabulate(table, tablefmt='presto', headers='firstrow'))
    click.echo('\n')

# Job Group
@click.group()
def job():
    '''Job methods'''
    pass

@click.command('add')
@click.argument('identifier', default='', required=False)
def add_job(identifier):
    '''Create an experiment job queue by IDENTIFIER'''
    client = MongoClient()
    mongodb = client.lab
    jobs = mongodb.jobs
    experiments = mongodb.experiments

    listing = experiments.find_one({"_id": identifier})
    jobs.insert_one(listing)

    click.echo('Job listing created {id=%s}' % identifier)

@click.command('ls')
def ls_job():
    '''List all existing jobs in a queue'''
    client = MongoClient()
    mongodb = client.lab
    jobs = mongodb.jobs

    listing = list(jobs.find())

    experiment = []
    for iteration in listing:
        experiment.append([iteration['_id'], iteration['method'], iteration['y'],
                           os.path.split(iteration['ewd'])[0]])

    table = [['id', 'method', 'response', 'directory']]
    for element in range(0, len(experiment)):
        table.append(experiment[element])

    click.echo(tabulate(table, tablefmt='presto'))

@click.command('run')
def run_job():
    '''Sequentially run all jobs'''
    timestamp = str(datetime.datetime.utcnow())
    click.echo('Starting on %s' % timestamp)

    client = MongoClient()
    mongodb = client.lab
    jobs = mongodb.jobs

    listing = list(jobs.find())

    for j in listing:
        identifier = j['_id']
        click.echo('Running job {id=%s}' % identifier)
        execute_learner(identifier)
        jobs.delete_one({'_id': identifier})

    timestamp = str(datetime.datetime.utcnow())
    click.echo('Finished on %s' % timestamp)


expr.add_command(create_experiment)
expr.add_command(rm_experiment)
expr.add_command(duplicate_experiment)
expr.add_command(run_experiment)
expr.add_command(perf_experiment)

project.add_command(create_project)
project.add_command(ls_project)
project.add_command(rm_project)
project.add_command(run_project)

job.add_command(add_job)
job.add_command(run_job)
job.add_command(ls_job)

cli.add_command(project)
cli.add_command(expr)
cli.add_command(ls_experiment)
cli.add_command(job)

if __name__ == '__main__':
    cli()
