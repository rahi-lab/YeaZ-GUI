
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 21 18:54:10 2019

"""
import os
import sys
from .model_pytorch import UNet
# from model_tensorflow import unet
import numpy as np
import skimage
from skimage import io
import skimage.transform as trans
import torch

import importlib.resources as resources
# Access weight file
path_weights = resources.files('yeaz.unet.weights')

def create_directory_if_not_exists(path):
    """
    Create in the file system a new directory if it doesn't exist yet.
    Param:
        path: the path of the new directory
    """
    if not os.path.exists(path):
        os.makedirs(path)


def threshold(im,th = None):
    """
    Binarize an image with a threshold given by the user, or if the threshold is None, calculate the better threshold with isodata
    Param:
        im: a numpy array image (numpy array)
        th: the value of the threshold (feature to select threshold was asked by the lab)
    Return:
        bi: threshold given by the user (numpy array)
    """
    im2 = im.copy()
    if th == None:
        th = skimage.filters.threshold_isodata(im2)
    bi = im2
    bi[bi > th] = 255
    bi[bi <= th] = 0
    return bi

import gc
def report_gpu():
    gc.collect()
    torch.cuda.empty_cache()
    print('Memory allocated: ', torch.cuda.memory_allocated())

def prediction(im, mic_type, pretrained_weights=None, model_type='pytorch', device=None):
    """
    Calculate the prediction of the label corresponding to image im
    Param:
        im: a numpy array image (numpy array), with max size 2048x2048
    Return:
        res: the predicted distribution of probability of the labels (numpy array)
    """        
    # pad with zeros such that is divisible by 16
    (nrow, ncol) = im.shape
    row_add = 16-nrow%16
    col_add = 16-ncol%16
    padded = np.pad(im, ((0, row_add), (0, col_add)))
    
    if pretrained_weights is None:
        if mic_type == 'pc':
            pretrained_weights = str(path_weights) + '/' + 'weights_budding_PhC_multilab_0_1'
        elif mic_type == 'bf':
            pretrained_weights = str(path_weights) + '/' + 'weights_budding_BF_multilab_0_1'
        elif mic_type == 'fission':
            pretrained_weights = str(path_weights) + '/' + 'weights_fission_multilab_0_2'
        if model_type == 'tensorflow':
            pretrained_weights = pretrained_weights + '.hdf5'
    
    if not os.path.exists(pretrained_weights):
        raise ValueError('Path does not exist')

    # WHOLE CELL PREDICTION

    if model_type == 'tensorflow':
        tf_model = unet(pretrained_weights = pretrained_weights,
                    input_size = (None,None,1))
        input = padded[np.newaxis,:,:,np.newaxis]
        tf_results = tf_model.predict(input, batch_size=1)
        tf_res = tf_results[0,:,:,0]
        
        return tf_res

    elif model_type == 'pytorch':
        # Load saved weights in pytorch model and run the pytorch model
        model = UNet()
        model.load_state_dict(torch.load(pretrained_weights))
        
        if torch.cuda.is_available() and device == 'cuda':
            device = torch.device('cuda')
            model = model.to(device)
            padded = torch.from_numpy(padded).to(device)
            # print('device: ', device)
        else:
            device = torch.device('cpu')
            padded = torch.from_numpy(padded)
            # print('device: ', device)
        model.eval()
        with torch.no_grad():
            # Convert input tensor to PyTorch tensor
            input_tensor = padded.unsqueeze(0).unsqueeze(0).float()
            # Pass input through the model
            output_tensor = model.forward(input_tensor)
            # Convert output tensor to NumPy array
            output_array = output_tensor.cpu().detach().numpy()
        pt_res = output_array[0, 0, :, :]
        
        # empty cache
        if (device == 'cuda') and (torch.cuda.is_available()):
            report_gpu()
        
        return pt_res[:nrow, :ncol]
    
    
    else:
        raise ValueError('model_type is not valid. should be either "pytorch" or "tensorflow".')
