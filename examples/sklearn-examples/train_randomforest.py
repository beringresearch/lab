from sklearn import datasets
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score

from lab.experiment import Experiment

if __name__ == "__main__":
    e = Experiment(dataset='iris_75')

    @e.start_run
    def train():
        iris = datasets.load_iris()
        X = iris.data
        y = iris.target

        X_train, X_test, y_train, y_test = train_test_split(X, y,
                                                            test_size=0.25,
                                                            random_state=42)
        n_estimators = 25

        e.log_features(['Sepal Length', 'Sepal Width', 'Petal Length',
                        'Petal Width'])
        clf = RandomForestClassifier(n_estimators = n_estimators)
        clf.fit(X_train, y_train)

        y_pred = clf.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average = 'macro')

        e.log_metric('accuracy_score', accuracy)
        e.log_metric('precision_score', precision)

        e.log_parameter('n_estimators', n_estimators)

        e.log_model('randomforest', clf)
