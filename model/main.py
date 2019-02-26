import math
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from torch.autograd import Variable
import context
import autoaim


# Devices
if torch.cuda.is_available():
    device = torch.device('cuda')
    print('Device: GPU.')
else:
    device = torch.device('cpu')
    print('Device: CPU.')

# Dataset
header, data = autoaim.DataLoader('test.csv').read_csv()
data = torch.Tensor(data).to(device)
x_train = data[:, :-1]
y_train = data[:, -1:]

test_data = torch.Tensor([
    [1.2/50, pow(1.2/50, 2), 0.0, 0.905],
    [0.0186, pow(0.0186, 2), 0.844, 0.8571]
]).to(device)

# Parameter
epoch_num = 20000
input_size = x_train.size()[1]
output_size = 1

print('====== Config ======')
print('input_size: {}'.format(input_size))

# Weight (plus one for constant term)
w = torch.rand((input_size + 1, output_size),
               requires_grad=True, device=device)


def forward(x):
    constant_term = torch.ones(x.size()[0], 1, device=device)
    _x = torch.cat((x, constant_term), 1)
    return _x.mm(w)

# Loss function


def loss(x, y):
    y_pred = forward(x)
    return ((y_pred - y) * (y_pred - y)).sum() + w.sum()


# Before training
print('====== Before training ======')
print("predict :",  test_data.tolist(),
      '-> ', forward(test_data).tolist())
print("weight: ",  w.tolist())

print('====== Start training ======')
# Training loop
_l = 100000000
for epoch in range(epoch_num):
    l = loss(x_train, y_train)
    l.backward()
    w.data = w.data - 0.0001 * w.grad.data

    if epoch == 0 or (epoch+1) % (epoch_num/10) == 0:
        print("progress: {!s:4}, loss: {:.2f}".format(epoch+1, l.data))
        # print('             grad: {}'.format(w.grad))

    # Manually zero the gradients after updating weights
    w.grad.data.zero_()

    if abs(_l-l) < 0.0001:
        print("progress: {!s:4}, loss: {:.2f}".format(epoch+1, l.data))
        break
    _l = l

# After training
print('====== After training ======')
print("predict :",  test_data.tolist(),
      '-> ', forward(test_data).tolist())
print("weight: ",  w.tolist())
