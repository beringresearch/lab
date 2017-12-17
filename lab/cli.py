import click
import uuid
import json
import os
import shutil
import datetime
import subprocess
from train import train_r
from pymongo import MongoClient
from terminaltables import SingleTable


def execute_learner(identifier=''): 
    client = MongoClient()
    db = client.lab
    experiments = db.experiments

    if identifier == '':
        with open('experiment.json', 'r') as f:
            experiment = json.load(f) 
    else:
        listing = experiments.find_one({"_id": identifier})
        with open(os.path.join(listing['ewd'], 'experiment.json'), 'r') as f:
            experiment = json.load(f) 

    experiments.update({'_id': experiment['_id']}, {"$set": experiment}, upsert=False)
    
    ewd = experiment['ewd'] 
    experimentjson = os.path.join(ewd, 'experiment.json')
    learner = os.path.join(ewd, experiment['learner']) 
   
    cmd = [experiment['command'], experiment['args'], learner, experimentjson]  
    stdout = open(os.path.join(ewd, 'stdout.log'), 'w')
    stderr = open(os.path.join(ewd, 'stderr.log'), 'w')
    subprocess.call(cmd, shell=False, stdout=stdout, stderr=stderr)

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

    project = {}
    project['name'] = name
    project['_id'] = projectid
    project['timestamp'] = timestamp
    project['pwd'] = os.path.join(os.getcwd(), name)
    project['ewd'] = os.path.join(os.getcwd(), 'experiments')
    project['data'] = os.path.join(os.getcwd(), name, 'data')
       
    projectdir = name

    if not os.path.exists(projectdir):
        os.makedirs(projectdir)
        
        datadir = os.path.join(projectdir, 'data')
        exprdir = os.path.join(projectdir, 'experiments')
 
        os.makedirs(datadir)
        os.makedirs(exprdir)

        with open(os.path.join(project['pwd'], 'project.json'), 'w') as f:
            json.dump(project, f, sort_keys = False, indent=2)


        client = MongoClient()
        db = client.lab 
        projects = db.projects
        projects.insert_one(project).inserted_id

        click.echo('Project created {id=' + projectid + '}') 

# List existing lab projects
@click.command('ls')
def ls_project():
    '''List all projects'''
    client = MongoClient()
    db = client.lab
    projects = db.projects

    listing = list(projects.find())

    project = []
    for iteration in listing: 
        project.append([iteration['_id'], iteration['name'], os.path.split(iteration['ewd'])[0]])

    table = [['id', 'name', 'directory']]
    for n in range(0, len(project)):
        table.append(project[n])
    
    click.echo(SingleTable(table).table)

@click.command('rm')
@click.argument('identifier')
def rm_project(identifier):
    '''Remove project by IDENTIFIER''' 
    client = MongoClient()
    db = client.lab
    projects = db.projects

    listing = projects.find_one({"_id": identifier})
    pwd = listing['pwd']
    
    if os.path.exists(pwd):
        shutil.rmtree(pwd) 
    
    projects.remove({"_id": identifier})

    click.echo('Removed project {id=%s}' % identifier)



# Experiment Group
@click.group()
def expr():
    '''Experiment methods'''
    pass

# Create a new Experiment 
@click.command('create')
def create_experiment():
    '''Create a new experiment'''
    timestamp = str(datetime.datetime.utcnow())
    exprid = str(uuid.uuid4())[:8]

    experiment = {}
    experiment['_id'] = exprid
    experiment['timestamp'] = timestamp
    experiment['ewd'] = os.path.join(os.getcwd(), exprid)
    experiment['command'] = 'Rscript'
    experiment['args'] = '--vanilla'
    experiment['data'] = ''
    experiment['x'] = []
    experiment['y'] = ''
    experiment['learner'] = 'train.R'
    experiment['seed'] = [123, 234, 345, 456]
    experiment['train'] = 0.8
    experiment['validate'] = 0.1
    experiment['test'] = 0.1
    experiment['method'] = ''
    experiment['options'] = {}

    search = {}
    search['rounds'] = 100
    search['optimise'] = 'macroF1'
    search['maximise'] = 'TRUE'
    experiment['search'] = search
    experiment['results'] = 'output'

    os.makedirs(experiment['ewd'])
         
    with open(os.path.join(experiment['ewd'], 'experiment.json'), 'w') as f:
        json.dump(experiment, f, sort_keys = False, indent=2)

    with open(os.path.join(experiment['ewd'], 'train.R'), 'w') as f:
        f.write(train_r())

    client = MongoClient()
    db = client.lab 
    experiments = db.experiments
    experiments.insert_one(experiment).inserted_id

    click.echo('Experiment created {id=' + exprid + '}') 

# List existing lab experiments
@click.command('ls')
def ls_experiment():
    '''List all registered experiments'''
    client = MongoClient()
    db = client.lab
    experiments = db.experiments

    listing = list(experiments.find())

    experiment = []
    for iteration in listing: 
        experiment.append([iteration['_id'], iteration['method'], iteration['y'],
            os.path.split(iteration['ewd'])[0]])
   
    table = [['id', 'method', 'response', 'directory']]
    for n in range(0, len(experiment)):
        table.append(experiment[n])
    
    click.echo(SingleTable(table).table)

# Duplicate a specific experiment
@click.command('duplicate')
@click.argument('identifier')
def duplicate_experiment(identifier):
    '''Duplicate experiment with an IDENTIFIER'''
    timestamp = str(datetime.datetime.utcnow())
    exprid = str(uuid.uuid4())[:8]
  
    client = MongoClient()
    db = client.lab
    experiments = db.experiments
    experiment = experiments.find_one({"_id": identifier})

    ewd = experiment['ewd']
    experiment['_id'] = exprid
    experiment['timestamp'] = timestamp
    experiment['ewd'] = os.path.join(os.getcwd(), exprid)

    experiments.insert_one(experiment).inserted_id
    
    os.makedirs(experiment['ewd'])
    shutil.copy2(os.path.join(ewd, 'experiment.json'), experiment['ewd'])
    shutil.copy2(os.path.join(ewd, experiment['learner']), experiment['ewd'])

    with open(os.path.join(experiment['ewd'], 'experiment.json'), 'w') as f:
        json.dump(experiment, f, sort_keys = False, indent=2)

    click.echo("Created experiment {id=%s}" % exprid)



@click.command('rm')
@click.argument('identifier')
def rm_experiment(identifier):
    '''Permanently remove experiment by IDENTIFIER'''
    client = MongoClient()
    db = client.lab
    experiments = db.experiments

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
@click.argument('identifier', required=True)
@click.argument('metric', required=False, default='accuracy')
def perf_experiment(identifier, metric): 
    '''Show performance by exp IDENTIFIER and METRIC'''
    client = MongoClient()
    db = client.lab
    experiments = db.experiments

    listing = experiments.find_one({"_id": identifier})
    ewd = listing['ewd']
    results = os.path.join(ewd, listing['results'])

    performances = [pos_json for pos_json in os.listdir(results) if pos_json.endswith('.json')]

    m = []
    for p in performances:
        with open(os.path.join(results, p), 'r') as f:
            e = json.load(f)
            m.append(e['performance'][metric])

    table = [performances, m]
    click.echo("Performance metric: %s" % metric)
    click.echo(SingleTable(table).table)

 
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
    db = client.lab
    jobs = db.jobs
    experiments = db.experiments

    listing = experiments.find_one({"_id": identifier})
    jobs.insert_one(listing).inserted_id

    click.echo('Job listing created {id=%s}' % identifier)

@click.command('ls')
def ls_job():
    '''List all existing jobs in a queue'''
    client = MongoClient()
    db = client.lab
    jobs = db.jobs

    listing = list(jobs.find())

    experiment = []
    for iteration in listing: 
        experiment.append([iteration['_id'], iteration['method'], iteration['y'],
            os.path.split(iteration['ewd'])[0]])
   
    table = [['id', 'method', 'response', 'directory']]
    for n in range(0, len(experiment)):
        table.append(experiment[n])
    
    click.echo(SingleTable(table).table)

@click.command('run')
def run_job():
    '''Sequentially run all jobs'''
    timestamp = str(datetime.datetime.utcnow())
    click.echo('Starting on %s' % timestamp)
       
    client = MongoClient()
    db = client.lab
    jobs = db.jobs

    listing = list(jobs.find())

    for job in listing:
        identifier = job['_id']
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

job.add_command(add_job)
job.add_command(run_job)
job.add_command(ls_job)

cli.add_command(project)
cli.add_command(expr)
cli.add_command(ls_experiment)
cli.add_command(job)



if __name__ == '__main__': 
    cli()
