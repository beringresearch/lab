import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.optimizers import RMSprop

from sklearn.metrics import accuracy_score, precision_score

from lab.keras import Experiment

batch_size = 128
num_classes = 10
epochs = 1

# the data, split between train and test sets
(x_train, y_train), (x_test, y_test) = mnist.load_data()

x_train = x_train.reshape(60000, 784)
x_test = x_test.reshape(10000, 784)
x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255
print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')

# convert class vectors to binary class matrices
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

model = Sequential()
model.add(Dense(512, activation='relu', input_shape=(784,)))
model.add(Dropout(0.2))
model.add(Dense(512, activation='relu'))
model.add(Dropout(0.2))
model.add(Dense(num_classes, activation='softmax'))

model.compile(loss='categorical_crossentropy',
              optimizer=RMSprop(),
              metrics=['accuracy'])

e = Experiment()
@e.start_run
def train():
    model.fit(x_train, y_train,
                    batch_size=batch_size,
                    epochs=epochs,
                    verbose=1,
                    validation_data=(x_test, y_test))

    y_prob = model.predict(x_test)
    y_classes = y_prob.argmax(axis=-1)
    actual = y_test.argmax(axis=-1)

    accuracy = accuracy_score(y_true = actual, y_pred = y_classes)
    precision = precision_score(y_true = actual, y_pred = y_classes, average = 'macro')

    # Log all metrics
    e.log_metric('accuracy_score', accuracy)
    e.log_metric('precision_score', precision)

    # Log parameters
    e.log_parameter('batch_size', batch_size)

    # Save model
    e.log_model(model, 'mnist-mlp')