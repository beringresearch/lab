import os
import dill

import pandas as pd

from pymongo import MongoClient

class Experiment:
    def __init__(self):
        None

    def list(self):
        client = MongoClient()
        mongodb = client.lab
        experiments = mongodb.experiments

        listing = list(experiments.find())

        experiment = []
        for iteration in listing:
            experiment.append([iteration['_id'], iteration['method'],
                iteration['y']])


        table = [['id', 'method', 'response']]
        for element in range(0, len(experiment)):
            table.append(experiment[element])

        table = pd.DataFrame(table, columns = table[0])
        table = table.drop(table.index[0])
        return table

    def load(self, identifier):
        client = MongoClient()
        mongodb = client.lab
        experiments = mongodb.experiments

        listing = experiments.find_one({"_id": identifier})
        ewd = listing['ewd']
        output = listing['results']
        path = os.path.join(ewd, output)

        for file in os.listdir(path):
                if file.endswith('.pkl'):
                    path = os.path.join(ewd, output, file)
                    model = dill.load(open(path, 'rb'))

        features = listing['x']

        return model, features


