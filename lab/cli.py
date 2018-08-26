import click
import os
import yaml

from lab import Project

@click.group()
def cli():
    '''Machine Learning Lab'''
    pass


@click.command('run')
def run_project():
    if os.path.isfile('labfile.yaml'):
        p = Project('labfile.yaml')
        p.start_run()
    else:
        raise Exception('Directory is not a valid Lab Project. Initiate a labfile.yaml and run again.')

@click.command('create')
@click.argument('name', required = True)
def create_project(name):
    with open(name+'.yaml', 'w') as file:
            meta = {'name': name,
                    'entry_points': None}
            yaml.dump(meta, file, default_flow_style=False)

cli.add_command(run_project)

if __name__ == '__main__':
    cli()
