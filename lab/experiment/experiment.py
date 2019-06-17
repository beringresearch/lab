import datetime
import uuid
import os
import sys
import yaml
import numpy
import warnings
import joblib
import graphviz
import json
from distutils.dir_util import copy_tree

warnings.filterwarnings(action='ignore', category=DeprecationWarning)

_DEFAULT_USER_ID = 'unknown'


class Experiment():
    def __init__(self, dataset='<data>'):
        """ Fundamental Lab class for managing a machine learning experiment.

        :param str dataset: description or tag of a dataset used for training.
        """

        self.dataset = dataset

    def create_run(self, run_uuid=None, user_id=None, home_dir=None,
                   timestamp=None, metrics=None, parameters=None,
                   source=None, feature_names=None, models=dict(),
                   artifacts=dict()):
        """ Initialise a Lab experiment run
        """

        self.uuid = str(uuid.uuid4())[:8]
        self.user_id = _get_user_id()
        self.timestamp = timestamp
        self.metrics = metrics
        self.parameters = parameters
        self.feature_names = feature_names
        self.source = ' '.join(sys.argv)
        self.home_dir = os.path.dirname(
                            os.path.dirname(
                                os.path.dirname(sys.argv[0])))
        self.models = models
        self.artifacts = artifacts

    def start_run(self, fun):
        """ Start run and log experiment data as it becomes available.
        """
        self.create_run(user_id=_get_user_id(),
                        timestamp=datetime.datetime.now())
        run_uuid = self.uuid

        models_directory = os.path.join(self.home_dir, 'experiments', run_uuid)
        logs_directory = os.path.join(self.home_dir, 'logs', run_uuid)

        fun()

        os.makedirs(logs_directory)
        os.makedirs(models_directory)

        # Log run metadata
        meta_file = os.path.join(logs_directory, 'meta.yaml')
        with open(meta_file, 'w') as file:
            meta = {'artifact_uri': os.path.dirname(
                                        os.path.abspath(models_directory)),
                    'source': self.source,
                    'start_time': self.timestamp,
                    'end_time': datetime.datetime.now(),
                    'experiment_uuid': self.uuid,
                    'dataset': self.dataset,
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
            model_file = os.path.join(models_directory, filename+'.joblib')
            joblib.dump(self.models[filename], model_file)

        # Log artifacts
        for artifact in self.artifacts.keys():
            destination = os.path.join(models_directory, artifact)
            copy_tree(self.artifacts[artifact], destination)

    def log_artifact(self, key, value):
        """ Log model artifacts
        """
        self.artifacts[key] = value

    def log_features(self, feature_names):
        """ Log feature names
        """
        self.feature_names = list(feature_names)

    def log_metric(self, key, value):
        """ Log performance metrics
        """
        value = numpy.array(value)
        logged_metric = {}
        logged_metric[key] = value.tolist()

        if self.metrics is None:
            self.metrics = logged_metric
        else:
            self.metrics[key] = value.tolist()

    def log_parameter(self, key, value):
        """ Log model hyperparameters
        """
        value = numpy.array(value)
        logged_parameter = {}
        logged_parameter[key] = value.tolist()

        if self.parameters is None:
            self.parameters = logged_parameter
        else:
            self.parameters[key] = value.tolist()

    def log_model(self, key, value):
        """Serialize the model
        """
        self.models[key] = value

    def view(self):
        """ View lab project as a graphviz graph.
        """
        return show_experiment(self.uuid)


def show_experiment(experiment_id):
    try:
        logs = yaml.load(open(os.path.join('logs', experiment_id,
                                           'meta.yaml'), 'r'))
        if logs['dataset'] is None:
            logs['dataset'] = 'N/A'
    except FileNotFoundError:
        print('Not a valid lab experiment')

    col = _get_graphviz_colour()

    try:
        metrics = yaml.load(open(os.path.join('experiments', experiment_id,
                                              'metrics.yaml'), 'r'))
    except FileNotFoundError:
        metrics = {'Metrics': 'None'}

    try:
        parameters = yaml.load(open(os.path.join('experiments', experiment_id,
                                                 'parameters.yaml'), 'r'))
    except FileNotFoundError:
        parameters = {'Parameter': 0.0}

    # Set defaults for empty values
    if parameters is None:
        parameters = {'Parameter': 0.0}

    # Extract only the source file name without arguments
    source = logs['source'].split(' ')[0]

    dot = graphviz.Digraph(format='png',
                           name=logs['experiment_uuid'],
                           node_attr={'shape': 'record'})

    dot.attr('node', color=col)
    dot.attr('edge', color=col)

    dataset_id = logs['dataset']
    #source_id = experiment_id+'_'+logs['source']
    source_id= source
    parameters_id = 'struct_'+experiment_id+'_parameters'
    metrics_id = experiment_id+'_performance'

    dot.node(experiment_id, logs['experiment_uuid'], shape='Mdiamond')
    dot.node(dataset_id, logs['dataset'], shape='Msquare')
    dot.node(source_id, source, shape='rectangle')

    dot.edge(experiment_id, dataset_id)
    dot.edge(dataset_id, source_id)

    with dot.subgraph(name='cluster_hyperparameters_'+experiment_id) as c:
        c.attr(label='Hyperparameters')
        c.attr('node', shape='Mrecord')
        c.attr(color='transparent')
        text = '{'+json.dumps(parameters).replace(',', '|')+'}'
        text = text.replace('"', '')
        c.node(parameters_id, text)

    with dot.subgraph(name='cluster_performance_'+experiment_id) as c:
        c.attr(label='Metrics')
        c.attr('node', shape='Mrecord')
        c.attr(color='transparent')
        text = '{'+json.dumps(metrics).replace(',', '|')+'}'
        text = text.replace('"', '')
        c.node(metrics_id, text)

    dot.edge(source_id, parameters_id)
    dot.edge(parameters_id, metrics_id)

    return dot


def _get_user_id():
    """Get the ID of the user for the current run."""
    try:
        import pwd
        import os
        return pwd.getpwuid(os.getuid())[0]
    except ImportError:
        return _DEFAULT_USER_ID


def _get_graphviz_colour():
    colour_list = ['antiquewhite4', 'aquamarine4', 'azure4', 'bisque4',
                   'black', 'blue', 'blueviolet', 'brown', 'burlywood',
                   'cadetblue', 'chartreuse3', 'chartreuse4', 'chocolate4',
                   'coral', 'coral3', 'cornflowerblue', 'cornsilk4',
                   'crimson', 'cyan', 'darkgreen', 'darkorange1', 'deeppink1',
                   'deepskyblue1', 'dodgerblue', 'firebrick', 'forestgreen',
                   'goldenrod', 'goldenrod4', 'hotpink', 'indigo',
                   'khaki4', 'lightcoral', 'lightslateblue', 'lightsteelblue4',
                   'maroon', 'midnightblue', 'orangered4', 'palevioletred',
                   'sienna3', 'tomato', 'violetred1']
    choice = numpy.random.choice(list(range(len(colour_list))),
                                 replace=False)
    return colour_list[choice]
