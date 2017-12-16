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


@click.group()
def cli():
    pass


# Project Group
@click.group()
def project():
    pass

# Create a new Project 
@click.command('create')
@click.argument('name')
def create_project(name):
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
    client = MongoClient()
    db = client.lab
    projects = db.projects

    listing = list(projects.find())

    project = []
    for iteration in listing: 
        project.append([iteration['_id'], iteration['name'], iteration['timestamp'], os.path.split(iteration['ewd'])[0]])
   
    table = [['id', 'name', 'timestamp', 'directory']]
    for n in range(0, len(project)):
        table.append(project[n])
    
    click.echo(SingleTable(table).table)

@click.command('rm')
@click.argument('identifier')
def rm_project(identifier):
    
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
    pass

# Create a new Experiment 
@click.command('create')
@click.argument('method')
def create_experiment(method):
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
    experiment['method'] = method
    experiment['options'] = {}

    search = {}
    search['rounds'] = 100
    search['optimise'] = 'macroF1'
    search['maximise'] = 'TRUE'
    experiment['search'] = search 

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
@click.argument('expid', default='', required=False)
def run_experiment(expid): 
    jobid = str(uuid.uuid4())[:8]

    client = MongoClient()
    db = client.lab
    experiments = db.experiments

    if expid == '':
        with open('experiment.json', 'r') as f:
            experiment = json.load(f) 
    else:
        listing = experiments.find_one({"_id": expid})
        with open(os.path.join(listing['ewd'], 'experiment.json'), 'r') as f:
            experiment = json.load(f) 


    experiments.update({'_id': experiment['_id']}, {"$set": experiment}, upsert=False)
    
    ewd = experiment['ewd'] 
    experimentjson = os.path.join(ewd, 'experiment.json')
    learner = os.path.join(ewd, experiment['learner']) 
   
    cmd = [experiment['command'], experiment['args'], learner,  '--experiment='+experimentjson,'--jobid='+jobid]
    click.echo('Job started {id=%s}' % jobid) 
    subprocess.check_output(cmd)
    click.echo('Job completed')



expr.add_command(create_experiment)
expr.add_command(rm_experiment)
expr.add_command(duplicate_experiment)

project.add_command(create_project)
project.add_command(ls_project)
project.add_command(rm_project)

cli.add_command(project)
cli.add_command(expr)
cli.add_command(ls_experiment)
cli.add_command(run_experiment)


if __name__ == '__main__':
    cli()
