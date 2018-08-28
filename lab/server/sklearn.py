import requests
import json
import numpy

def predict(newdata, url = 'http://0.0.0.0:5000/predict'):
    r = requests.post(url = url, json=newdata.tolist())
    result = numpy.array(r.json()['prediction'])
    return result

def predict_proba(newdata, url = 'http://0.0.0.0:5000/predict_proba'):
    r = requests.post(url = url, json=newdata.tolist())
    result = numpy.array(r.json()['prediction'])
    return result

def get_feature_names(url = 'http://0.0.0.0:5000/feature_names'):
    r = requests.get(url = url)
    return r.json()

def classes_(url = 'http://0.0.0.0:5000/classes'):
    r = requests.get(url = url)
    return numpy.array(r.json())


