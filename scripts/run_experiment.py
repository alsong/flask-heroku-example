import argparse
import math
import mlflow
import mlflow.keras
from tensorflow.keras.callbacks import Callback

from album_art_classifier.build_model import build_model
from album_art_classifier.train_model import train_model
from album_art_classifier.evaluate_model import evaluate_model


class MlFlowCallback(Callback):
	def __init__(self, test_dir=None):
		self.best_val_loss = math.inf
		self.test_dir = test_dir

	def on_train_begin(self, logs={}):
		mlflow.log_params(self.params)

	def on_epoch_end(self, epoch, logs={}):
		mlflow.log_metrics({
			'train_acc': logs['acc'],
			'train_loss': logs['loss'],
			'val_acc': logs['val_acc'],
			'val_loss': logs['val_loss']
		}, step=epoch)
		mlflow.keras.log_model(self.model, 'model-epoch-{}.h5'.format(epoch + 1))

		if logs['val_loss'] < self.best_val_loss:
			self.best_val_loss = logs['val_loss']

			mlflow.keras.log_model(
				self.model,
				'model-epoch-{}-best.h5'.format(epoch + 1)
			)

			test_loss, test_acc = evaluate_model(self.model, test_dir=self.test_dir)

			mlflow.log_metrics({
				'test_loss': test_loss,
				'test_acc': test_acc,
			}, step=epoch)


def run_experiment(
	exp_name,
	train_dir='data/train',
	val_dir='data/validate',
	test_dir='data/test',
	model_path=None,
	epochs=10,
	batch_size=16
):
	experiment_id = mlflow.set_experiment(exp_name)
	with mlflow.start_run(experiment_id=experiment_id):
		model = build_model()
		train_model(
			model,
			model_path=model_path,
			epochs=epochs,
			batch_size=batch_size,
			train_dir=train_dir,
			val_dir=val_dir,
			callbacks=[MlFlowCallback(test_dir=test_dir)]
		)


if __name__ == '__main__':
	parser = argparse.ArgumentParser()

	parser.add_argument('name')
	parser.add_argument('--train_dir', default='data/train')
	parser.add_argument('--val_dir', default='data/validate')
	parser.add_argument('--test_dir', default='data/test')
	parser.add_argument('--epochs', type=int, default=10)
	parser.add_argument('--batch_size', type=int, default=32)
	parser.add_argument('--model_path', default=None)

	args = parser.parse_args()
	kwargs = vars(args)
	name = kwargs.pop('name')

	run_experiment(name, **kwargs)
