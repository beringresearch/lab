.. _dlexperiments:

Managing Deep Learning Experiments
==================================

Deep Learning experiment lifecycle generates a rich set of data artifacts, e.g., expansive datasets, complex model architectures, varied hyperparameters, learned weights, and training logs. To produce an effective model, a researcher often has to iterate over multiple scripts, making it challenging to reproduce complex experiments.

Lab functionality offers a clean and standardised interface for managing the many moving parts of a Deep Learning experiment.

MNIST Example
~~~~~~~~~~~~~~~~

Consider the following lab training script. Let's set up our hyperparameters and training, validation, testing sets:

.. code-block:: python

	import keras
	from keras.datasets import mnist
	from keras.models import Sequential
	from keras.layers import Dense, Dropout
	from keras.optimizers import RMSprop
	from keras.callbacks import TensorBoard

	import tempfile

	from sklearn.metrics import accuracy_score, precision_score

	from lab.experiment import Experiment

	BATCH_SIZE = 128
	EPOCHS = 20
	CHECKPOINT_PATH = 'tf/weights'
	num_classes = 10
	

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


Set up a simple model and train:

.. code-block:: python

	e = Experiment()


	@e.start_run
	def train():

	    # Create a temporary directory for tensorboard logs
	    output_dir = tempfile.mkdtemp()
	    print("Writing TensorBoard events locally to %s\n" % output_dir)
	    tensorboard = TensorBoard(log_dir=output_dir)

	    # During Experiment execution, tensorboard can be viewed through:
	    # tensorboard --logdir=[output_dir]

	    model.fit(x_train, y_train,
	              batch_size=BATCH_SIZE,
	              epochs=EPOCHS,
	              verbose=1,
	              validation_data=(x_test, y_test),
	              callbacks=[tensorboard])

	    model.save_weights(CHECKPOINT_PATH)

	    y_prob = model.predict(x_test)
	    y_classes = y_prob.argmax(axis=-1)
	    actual = y_test.argmax(axis=-1)

	    accuracy = accuracy_score(y_true=actual, y_pred=y_classes)
	    precision = precision_score(y_true=actual, y_pred=y_classes,
	                                average='macro')

	    # Log tensorboard
	    e.log_artifacts('tensorboard', output_dir)
	    e.log_artifacts('weights', CHECKPOINT_PATH)

	    # Log all metrics
	    e.log_metric('accuracy_score', accuracy)
	    e.log_metric('precision_score', precision)

	    # Log parameters
	    e.log_parameter('batch_size', BATCH_SIZE)
	    e.log_parameter('epochs', EPOCHS)

When training on distributed systems with Horovod, `model.fit` element can be abstracted into a file, say `horovod-train.py` and called directly from the `train()` method:

.. code-block:: python

	import subprocess

	args = ['-np', str(8), # 8 GPUs
		'-H', 'localhost:8', 'python',
		'horovod-train.py',
		'--checkpoint', CHECKPOINT_PATH,
		'--batch-size', BATCH,
		'--epochs', EPOCHS]

Note that you need to eable your Horovod script to accept some basic model hyperparameters that you wish to log downstream.