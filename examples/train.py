''' Python Implementation of a Learner '''
import os
import json
import sys
import pandas as pd
import sklearn.metrics as metrics
from scipy.stats import randint
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.externals import joblib

def run(experiment):
    ''' Main run function '''
    with open(experiment, 'r') as file:
        metadata = json.load(file)

    data = pd.read_csv(metadata['data'])
    X = data[metadata['x']]
    y = data[metadata['y']]
    testing_fraction = metadata['test']

    random_seed = metadata['seed']

    for iteration in range(0, len(random_seed)):
        print('Training iteration ' + str(iteration+1) + ' of ' + str(len(random_seed)))

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=testing_fraction,
                                                            random_state=random_seed[iteration])
        model = RandomForestClassifier(n_estimators=metadata['options']['n_estimators'])
        param_dist = {'max_depth': [2, None],
                      'max_features': randint(2, len(X.columns)),
                      'min_samples_split': randint(2, len(X.columns)),
                      'min_samples_leaf': randint(1, len(X.columns)),
                      'bootstrap': [True, False],
                      'criterion': ["gini", "entropy"]}

        n_iter_search = metadata['search']['rounds']
        random_search = RandomizedSearchCV(model, param_distributions=param_dist,
                                           n_iter=n_iter_search, cv=5,
                                           random_state=random_seed[iteration])
        random_search.fit(X_train, y_train)
        y_pred_labels = random_search.best_estimator_.predict(X_test)
        perf = performance(y_test, y_pred_labels)

        result = {'ewd': metadata['ewd'],
                  'parameters': random_search.best_params_}
        result['performance'] = perf

        output_directory = os.path.join(metadata['ewd'], metadata['results'])
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        joblib.dump(random_search.best_estimator_,
                    os.path.join(output_directory, str(random_seed[iteration])+'_model.pkl'))

        with open(os.path.join(output_directory,
                               str(random_seed[iteration])+'_results.json'), 'w') as file:
            json.dump(result, file, sort_keys=False, indent=2)



def performance(y_true, y_pred):
    ''' Helper function that creates model performance list '''
    perf = {'accuracy': metrics.accuracy_score(y_true, y_pred),
            'macroPrecision': metrics.precision_score(y_true, y_pred, average='macro'),
            'macroRecall': metrics.recall_score(y_true, y_pred, average='macro'),
            'macroF1': metrics.f1_score(y_true, y_pred, average='macro')
           }
    return perf

if __name__ == '__main__':
    run(sys.argv[1])
