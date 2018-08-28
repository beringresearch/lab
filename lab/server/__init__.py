import os
import glob
import numpy as np
import yaml

from flask import Flask, request, jsonify
from sklearn.externals import joblib

app = Flask(__name__)

clf = None
feature_names = None

@app.route("/")
def main():
    return "Basic Lab Server"

@app.route("/predict", methods = ['POST'])
def predict():
    json_ = request.json
    query = np.array(json_)  
    
    prediction = clf.predict(query)
    return jsonify({'prediction': prediction.tolist()})

@app.route("/predict_proba", methods = ['POST'])
def predict_proba():
    json_ = request.json
    query = np.array(json_)
    
    prediction = clf.predict_proba(query)
    return jsonify({'prediction': prediction.tolist()})

@app.route("/classes", methods = ['GET'])
def classes_():
    return jsonify(clf.classes_.tolist())

@app.route("/feature_names", methods = ['GET'])
def get_feature_names():
    return jsonify(feature_names)

def _run_server(model_id):
    global clf
    global feature_names
    
    model_file = glob.glob(os.path.join('labrun', model_id, '*.pkl'))[0]    
    clf = joblib.load(model_file)
    print('Model loaded succesfully.')

    feature_file = os.path.join('labrun', model_id, 'features.yaml')     
    with open(feature_file, 'r') as file:
        feature_names = yaml.load(file)
    print(feature_names)
    print('Features loaded succesfully.')

    app.run(host='0.0.0.0')