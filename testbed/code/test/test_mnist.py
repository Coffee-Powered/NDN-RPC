#from mnist import MNIST
from keras.src.datasets import mnist

print(1)
mnist_data = mnist.load_data()
print(2)
(train_x, train_y), (test_x, test_y) = mnist_data
print(3)



# Path to MNIST training data
#path_to_training_data: str = "/home/vagrant/python-mnist/bin/mnist_get_data.sh"

#mndata = MNIST(path_to_training_data)
#images, labels = mndata.load_training()

#mndata.gz = True            # Use gzipped files
