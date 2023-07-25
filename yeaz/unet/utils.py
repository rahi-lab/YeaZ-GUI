
from model_pytorch import UNet
from model_tensorflow import unet
import torch
import tensorflow as tf

def weight_loading(pretrained_weights):
    # Load the weights
    tf_model = tf.keras.models.load_model(pretrained_weights)
    tf_weights = tf_model.get_weights()

    # Load the PyTorch model
    pt_model = UNet() #implemented based on the previous model (by myself)
    initial_state_dict = pt_model.state_dict()
    new_state_dict = {}
    with torch.no_grad():
        x = 0
        for i, layer in enumerate(pt_model.modules()):
            if isinstance(layer, torch.nn.Conv2d) or isinstance(layer, torch.nn.Linear):
                # extract the weights and biases from the TensorFlow weights
                weight_tf = tf_weights[x*2]
                bias_tf = tf_weights[x*2+1]

                # convert the weights and biases to PyTorch format
                layer.weight.data = torch.tensor(weight_tf.transpose(3, 2, 0, 1), dtype=torch.float)
                layer.bias.data = torch.tensor(bias_tf, dtype=torch.float)

                x = x + 1

            if isinstance(layer, torch.nn.ConvTranspose2d):
                weight_tf = tf_weights[x*2]
                bias_tf = tf_weights[x*2+1]
                
                # convert the weights and biases to PyTorch format
                layer.weight.data = torch.tensor(weight_tf.transpose(2, 3, 0, 1), dtype=torch.float)
                layer.bias.data = torch.tensor(bias_tf, dtype=torch.float)
                
                x = x + 1
    return pt_model
