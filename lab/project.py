import os
import json
import shutil

import pandas as pd

from pymongo import MongoClient


class Project:
    def __init__(self):
        None

    def remove(self, identifier):
        client = MongoClient()
        mongodb = client.lab
        projects = mongodb.projects

        listing = projects.find_one({"_id": identifier})
        pwd = listing['pwd']
        if os.path.exists(pwd):
            shutil.rmtree(pwd)

        projects.remove({"_id": identifier})


    def info(self, identifier):
        client = MongoClient()
        mongodb = client.lab
        projects = mongodb.projects

        listing = projects.find_one({"_id": identifier})
        ewd = listing['ewd']
        experiments = os.listdir(ewd)

        summary = []
        
        for e in experiments:
            experiment = json.load(open(os.path.join(ewd, e, 'experiment.json')))
            jsonpath = os.path.join(ewd, e, experiment['results'])
            for file in os.listdir(jsonpath):
                if file.endswith('.json'):
                    performance = json.load(open(os.path.join(ewd, e, 
                        experiment['results'], file)))
            summary.append(performance)

        table = [['model-id', 'accuracy', 'f1-score', 'precision', 'recall']]
        for element in range(0, len(experiments)):
            id = experiments[element]
            accuracy = round(summary[element]['accuracy'], 2)
            f1score =  [ round(elem, 2) for elem in summary[element]['f1-score'] ]
            precision =  [ round(elem, 2) for elem in summary[element]['precision'] ]
            recall =  [ round(elem, 2) for elem in summary[element]['recall'] ]
            table.append([id, accuracy, f1score, precision, recall])

        table = pd.DataFrame(table, columns = table[0])
        table = table.drop(table.index[0])
        return table


    def list(self):
        client = MongoClient()
        mongodb = client.lab
        projects = mongodb.projects

        listing = list(projects.find())

        project_list = []
    
        for iteration in listing:
            project_list.append([iteration['_id'], iteration['name'],
                                os.path.dirname(os.path.dirname(iteration['ewd']))])

        table = [['id', 'name', 'directory']]
        for element in range(0, len(project_list)):
            table.append(project_list[element])

        table = pd.DataFrame(table, columns = table[0])
        table = table.drop(table.index[0])
        return table

