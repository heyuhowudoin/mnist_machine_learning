import numpy as np, gzip


def sigmoid(z):
	return 1.0/(1.0+np.exp(-z))

def sigmoid_prime(z):
	return sigmoid(z)*(1-sigmoid(z))

def get_images(path):
	with gzip.open(path, 'r') as f:
		magic_number = int.from_bytes(f.read(4), 'big')
		image_count = int.from_bytes(f.read(4), 'big')
		row_count = int.from_bytes(f.read(4), 'big')
		column_count = int.from_bytes(f.read(4), 'big')
		image_data = f.read()
		images = np.frombuffer(image_data, dtype=np.uint8).reshape((image_count, row_count, column_count))
		return images

def get_labels(path):
	with gzip.open(path, 'r') as f:
		magic_number = int.from_bytes(f.read(4), 'big')
		label_count = int.from_bytes(f.read(4), 'big')
		label_data = f.read()
		labels = np.frombuffer(label_data, dtype=np.uint8)
		return labels

def get_data(tr_set_size = 60000, tst_set_size = 10000):
	train_i = get_images("training_data/train-images-idx3-ubyte.gz") / 255
	labels = get_labels("training_data/train-labels-idx1-ubyte.gz")
	train_l = np.zeros((tr_set_size, 10))
	for lbl, cnt in zip(labels, range(tr_set_size)):
		train_l[cnt, lbl] += 1

	train_data = np.array([[img, lbl] for img, lbl in zip(train_i, train_l) ], dtype = object)

	test_i = get_images("training_data/t10k-images-idx3-ubyte.gz") / 255
	test_l = get_labels("training_data/t10k-labels-idx1-ubyte.gz")


	return (train_data, test_i, test_l)


class layer:
	def __init__(self, num_of_inp, num_of_nrn):
		self.biases = np.random.randn(num_of_nrn)
		self.b_adj = np.zeros(num_of_nrn)
		self.weights = np.random.randn(num_of_inp, num_of_nrn)
		self.w_adj = np.zeros((num_of_inp, num_of_nrn))
		self.values = np.zeros(num_of_nrn)
		self.activations = sigmoid(self.values)

	def forwardprop(self, input_):
		self.values = np.dot(input_, self.weights) + self.biases
		self.activations = sigmoid(self.values)


class neural_network:
	def __init__(self, n_per_l):
		self.layers = [layer(inp, nrn) for inp, nrn in zip(n_per_l, n_per_l[1:])]
		print("layers created")

	def forwardprop(self, input_):
		for layer in self.layers:
			layer.forwardprop(input_)
			input_ = layer.activations

		self.output = layer.activations

	def backwardprop(self, target):
		cost = (self.layers[-1].activations - target)
		cost_prime = cost * sigmoid_prime(self.layers[-1].values)

		self.layers[-1].b_adj += cost_prime
		shaped_cost = np.array([cost_prime]).transpose()
		shaped_activations = np.array([self.layers[-2].activations])
		self.layers[-1].w_adj += np.dot(shaped_cost, shaped_activations).transpose()

		for l in range(2, len(self.layers)):
			layer = self.layers[-l]
			# print(len(layer.biases), "b")
			# print(np.array([self.layers[-l+1].weights]), "w")
			# print(np.array(cost_prime).transpose(), "c")
			shaped_cost = np.array(cost_prime).transpose()
			shaped_weights = np.array(self.layers[-l+1].weights)
			cost_prime = np.dot(shaped_weights, shaped_cost).transpose()
			layer.b_adj += cost_prime

			shaped_cost = np.array([cost_prime]).transpose()
			shaped_activations = np.array([self.layers[-l-1].activations])
			layer.w_adj += np.dot(shaped_cost, shaped_activations).transpose()

	def train(self, lrn_rt, batch_size, epochs, ep_size, inputs):
		train_data, test_i, test_l = inputs
		mini_batches = [train_data[k:k + batch_size] for k in range(0, len(train_data), batch_size)]
		print("mini_batches shaped")

		for ep in range(epochs):
			for mini_batch in mini_batches:
				for img, lbl in mini_batch:
					self.forwardprop(np.reshape(img, (784)))
					self.backwardprop(lbl)

				for layer in self.layers:
					layer.biases = layer.biases - (layer.b_adj / batch_size) * lrn_rt
					layer.weights = layer.weights - (layer.w_adj / batch_size) * lrn_rt
					layer.b_adj = np.zeros(layer.biases.shape)
					layer.w_adj = np.zeros(layer.weights.shape)

			correct = 0
			for img, lbl in zip(test_i, test_l):
				self.forwardprop(np.reshape(img, (784)))
				if list(self.output).index(max(self.output)) == lbl:
					correct += 1

			print("Epoch", ep, ":", correct, "/", len(test_l))


net = neural_network([784, 30, 10])
print("getting data")
data = get_data()
print("data collected")
print("starting training")
net.train(0.1, 30, 30, 60000, data)
