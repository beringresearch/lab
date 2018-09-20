from sklearn import datasets

from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_squared_error
from sklearn.metrics import r2_score

from lab.sklearn import Experiment

if __name__ == "__main__":
    e = Experiment()
    
    @e.start_run
    def train():
        boston = datasets.load_boston() 
        X = boston.data
        y = boston.target

        X_train, X_test, y_train, y_test = train_test_split(X, y,
            test_size=0.24, random_state=42)
        
        model = LinearRegression()
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)

        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        rsq = r2_score(y_test, y_pred)

        e.log_metric('MAE', mae)
        e.log_metric('MSE', mse)
        e.log_metric('R2', rsq)

        e.log_model(model, 'linear_model')

