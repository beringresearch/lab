import datetime
import uuid
import os
import yaml
import pickle
import numpy

from sklearn.externals import joblib

_DEFAULT_USER_ID = 'unknown'

class Experiment():
    def __init__(self):
        pass

    def create_run(self, run_uuid = None, user_id = None, timestamp = None, metrics = None, parameters = None):        
        self.uuid = str(uuid.uuid4())
        self.user_id = _get_user_id()
        self.timestamp = timestamp 
        self.metrics = metrics  
        self.parameters = parameters 
        
    def start_run(self, fun):
        self.create_run(user_id = _get_user_id(), timestamp = datetime.datetime.now())
        run_uuid = self.uuid
        run_directory = os.path.join('labrun', run_uuid)
        os.makedirs(run_directory)
            
        fun()    

        meta_file = os.path.join(run_directory, 'meta.yaml')
        with open(meta_file, 'w') as file:
            meta = {'artifact_uri': os.path.dirname(os.path.abspath(meta_file)),
                    'start_time': self.timestamp,
                    'end_time': datetime.datetime.now(),
                    'experiment_uuid': self.uuid,
                    'user_id': self.user_id}
            yaml.dump(meta, file, default_flow_style=False)
        
        metrics_file = os.path.join(run_directory, 'metrics.yaml')
        with open(metrics_file, 'w') as file:
            yaml.dump(self.metrics, file, default_flow_style=False)

        parameters_file = os.path.join(run_directory, 'parameters.yaml')
        with open(parameters_file, 'w') as file:
            yaml.dump(self.parameters, file, default_flow_style=False)


    def log_metric(self, key, value):
        value = numpy.array(value)
        logged_metric = {}
        logged_metric[key] = value.tolist()

        if self.metrics is None:
            self.metrics = logged_metric
        else:
            self.metrics[key] = value.tolist()

    def log_parameter(self, key, value):
        value = numpy.array(value)
        logged_parameter = {}        
        logged_parameter[key] = value.tolist()

        if self.parameters is None:
            self.parameters = logged_parameter
        else:
            self.parameters[key] = value.tolist()

    def log_model(self, model, filename):
        run_uuid = self.uuid
        run_directory = os.path.join('labrun', run_uuid)
        model_file = os.path.join(run_directory, filename+'.pkl')
        joblib.dump(model, model_file)

        
def _get_user_id():
    """Get the ID of the user for the current run."""
    try:
        import pwd
        import os
        return pwd.getpwuid(os.getuid())[0]
    except ImportError:
        return _DEFAULT_USER_ID
