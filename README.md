# Machine Learning Lab
Command line interface for the management of arbitrary machine learning tasks.

# Pre-requisites
The Lab uses MongoDB to manage active projects and experiments. Ensure that Mongo is installed and running on localhost:27017

# Installation
```
git clone https://github.com/beringresearch/lab
cd lab
virtualenv -p python3 lab
pip install --editable .
```

# Command Glossary
The Lab embodies three broad concepts:
* project - utility to create and manage ML projects
* expr - utility to create and manage ML experiments
* job - a basic queue for sequential (for now) execution of multiple experiments

# Using the Lab
## Managing Lab Projects
New projects are created in a current working directory.
```
lab project create iris
    Project created {id=a8150c15}
```

All projects have consistent directory structure:
```
.
|____project.json
|____experiments
|____data
```

To view existing projects:
```
lab project ls

id       | name    | directory
----------+---------+-------------------------------------------------
 e325bb3b | colon   | /Users/ignat/Documents/Bering/Projects/Wren/lab
 b72e56ca | myeloma | /Users/ignat/Documents/Bering/Projects/Wren/lab
 04d72282 | men1    | /Users/ignat/Documents/Bering/Projects/Wren/lab
 a8150c15 | iris    | /Users/ignat/Desktop
```

A project can be removed using its identifier:
```
lab project rm a8150c15
```

## Managing Lab Experiments
To create a new experiment, ensure that you are in the __experiments__ folder of your project and run:
```
lab expr create
    experiment created {id=ce2a6ac8}
```

The Lab generates a new experiment folder with a random UUID. Each experiment directory has a consistent structure:
```
.
|____train.R
|____experiment.json
```

To list existing eperimets:
```
lab ls
```

To remove an experiment:
```
lab expr rm ce2a6ac8
```

Take a look at /examples/train.py and /examples/experiment.json files to explore experimental set up.

To run an experiment:
```
lab expr run ce2a6ac8
```
