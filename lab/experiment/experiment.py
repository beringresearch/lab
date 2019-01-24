import datetime
import uuid
import os
import sys
import yaml
import numpy
import warnings
import pickle

warnings.filterwarnings(action='ignore', category=DeprecationWarning)

_DEFAULT_USER_ID = 'unknown'

class Experiment():
    def __init__(self):        
        pass

    def create_run(self, run_uuid = None, user_id = None, home_dir = None,
                   timestamp = None, metrics = None, parameters = None,
                   feature_names = None, models = dict()):        
        self.uuid = str(uuid.uuid4())[:8]
        self.user_id = _get_user_id()
        self.timestamp = timestamp 
        self.metrics = metrics  
        self.parameters = parameters
        self.feature_names = feature_names
        self.source = sys.argv[0]
        #self.home_dir = os.path.dirname(os.path.realpath(sys.argv[0]))        
        self.home_dir = os.path.dirname(os.path.dirname(os.path.dirname(sys.executable))) # hacky but will do for now
        self.models = models
        
        
    def start_run(self, fun):        
        self.create_run(user_id = _get_user_id(), timestamp = datetime.datetime.now())
        run_uuid = self.uuid        
        models_directory = os.path.join(self.home_dir, 'experiments', run_uuid)        
        logs_directory = os.path.join(self.home_dir, 'logs', run_uuid)          
        
        try:
            fun()    
        except Exception as e:
            print(e)
        else:
            os.makedirs(models_directory)
            os.makedirs(logs_directory)

            # Log run metadata
            meta_file = os.path.join(logs_directory, 'meta.yaml')
            with open(meta_file, 'w') as file:
                meta = {'artifact_uri': os.path.dirname(os.path.abspath(models_directory)),
                        'source': self.source,
                        'start_time': self.timestamp,
                        'end_time': datetime.datetime.now(),
                        'experiment_uuid': self.uuid,
                        'user_id': self.user_id}
                yaml.dump(meta, file, default_flow_style=False)
        
            # Log metrics
            metrics_file = os.path.join(models_directory, 'metrics.yaml')
            with open(metrics_file, 'w') as file:
                yaml.dump(self.metrics, file, default_flow_style=False)

            # Log parameters
            parameters_file = os.path.join(models_directory, 'parameters.yaml')
            with open(parameters_file, 'w') as file:
                yaml.dump(self.parameters, file, default_flow_style=False)

            # Log features
            feature_file = os.path.join(models_directory, 'features.yaml')
            with open(feature_file, 'w') as file:
                yaml.dump(self.feature_names, file, default_flow_style=False)

            # Log models            
            for filename in self.models.keys():
                model_file = os.path.join(models_directory, filename+'.pkl')
                pickle.dump(self.models[filename], open(model_file, 'wb'))

    def log_features(self, feature_names):
        """ Log feature names

            Parameters
            ----------
            feature_names: array
                Feature names or indices to be logged
        """
        self.feature_names = list(feature_names)

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

    def log_model(self, key, value):
        run_uuid = self.uuid
        self.models[key] = value        

    # Experimental feature - API is bound to change!
    def log_artifact(self, artifact, filename):
        run_uuid = self.uuid
        models_directory = os.path.join(self.home_dir, 'experiments', run_uuid)

        destination = os.path.join(models_directory, filename)
        file_name, file_extension = os.path.splitext(filename)
        if file_extension == '.png':
            artifact.savefig(destination)

        
def _get_user_id():
    """Get the ID of the user for the current run."""
    try:
        import pwd
        import os
        return pwd.getpwuid(os.getuid())[0]
    except ImportError:
        return _DEFAULT_USER_ID
