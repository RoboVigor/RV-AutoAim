import math
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from torch.autograd import Variable
import sys
sys.path.append("..")
import autoaim

# Devices
if torch.cuda.is_available():
    device = torch.device('cuda')
    print('Device: GPU.')
else:
    device = torch.device('cpu')
    print('Device: CPU.')

#device = torch.device('cpu')

# Dataset
def preprocess(t,h):
    # shuffling
    r = torch.randperm(t.size(0))
    t = t[r,:]
    # GIVE ME MORE!!
    _ = t[:,:-1]
    t = torch.cat((_,t[:,-1:]),1)
    return t

def load(filename):
    header, data = autoaim.helpers.read_csv(filename)
    data = torch.Tensor(data).to(device)
    data = preprocess(data,header)
    x = data[:, :-1]
    y = data[:, -1:]
    return x, y, header

x_train, y_train, header = load('test_pair_train.csv')
x_test, y_test, _ = load('test_pair_test.csv')

train_dataset_size = x_train.size(0)
test_dataset_size = x_test.size(0)
input_size = x_train.size(1)
output_size = 3

print('====== Input ======')
print('train_dataset_size: {}'.format(train_dataset_size))
print('test_dataset_size: {}'.format(test_dataset_size))
print('input_size: {}'.format(input_size))

# Model
class Model(torch.nn.Module):

    def __init__(self):
        super(Model, self).__init__()
        self.linear = torch.nn.Linear(input_size, output_size)
        self.sigmoid = torch.nn.Sigmoid()

    def forward(self, x):
#         y_pred = self.sigmoid(self.linear(x))
        y_pred = self.linear(x)
        return y_pred

# Training loop
@autoaim.helpers.time_this
def train(learning_rate, epoch_num):
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(),lr=learning_rate)
    # Train loop
    print('====== Config ======')
    print('learning_rate: {}'.format(learning_rate))
    print('epoch_num: {}'.format(epoch_num))
    loss_list = []
    for epoch in range(epoch_num):
        # Forward pass
        y_pred = model(x_train)
        loss = criterion(y_pred, y_train.t().squeeze().long())

        # Backward and optimize
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if epoch == 0 or (epoch+1) % (epoch_num/10) == 0:
            y_pred = model(x_test)
            loss_test = criterion(y_pred, y_test.t().squeeze().long())
            print("Epoch: [{!s:6}/{!s:6}], Loss: {:.2f}, Test loss: {:.2f}"
                  .format(epoch+1, epoch_num, loss,loss_test))

        if epoch == 0 or (epoch+1) % (epoch_num/1000) == 0:
            y_pred = model(x_test)
            loss_test = criterion(y_pred, y_test.t().squeeze().long())
            loss_list += [loss_test]

    x = np.arange(0, len(loss_list), dtype=int)
    plt.plot(x, np.array(loss_list), 'ro',label='loss')
    plt.legend()
    plt.show()