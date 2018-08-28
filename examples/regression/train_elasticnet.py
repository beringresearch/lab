import sys

from sklearn import datasets

from sklearn.linear_model import ElasticNet
from sklearn.model_selection import train_test_split

from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_squared_error
from sklearn.metrics import r2_score

from lab.sklearn import Experiment

alpha = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
l1_ratio = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5

if __name__ == "__main__":
    e = Experiment()
    
    @e.start_run
    def train():
        boston = datasets.load_boston() 
        X = boston.data
        y = boston.target

        X_train, X_test, y_train, y_test = train_test_split(X, y,
            test_size=0.24, random_state=42)
        
        model = ElasticNet(alpha=alpha, l1_ratio=l1_ratio, random_state=42)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)

        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        rsq = r2_score(y_test, y_pred)

        e.log_parameter('alpha', alpha)
        e.log_parameter('l1_ratio', l1_ratio)

        e.log_metric('MAE', mae)
        e.log_metric('MSE', mse)
        e.log_metric('R2', rsq)

        e.log_model(model, 'elastic_net')