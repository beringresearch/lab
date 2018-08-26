import os
import glob
import numpy as np

from flask import Flask, request, jsonify
from sklearn.externals import joblib

app = Flask(__name__)
clf = None

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

def _run_server(model_id):
    global clf
    model_file = glob.glob(os.path.join('labrun', model_id, '*.pkl'))[0]
    clf = joblib.load(model_file)
    print('Model loaded succesfully.')
    app.run(host='0.0.0.0')