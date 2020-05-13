
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 21 18:54:10 2019

"""
from model import unet
import numpy as np
import skimage


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


def prediction(im):
    """
    Calculate the prediction of the label corresponding to image im
    Param:
        im: a numpy array image (numpy array)
    Return:
        res: the predicted distribution of probability of the labels (numpy array)
    """    
    # pad with zeros such that shape is divisible by 16 (4 downsampling in unet)
    (nrow, ncol) = im.shape
    row_add = 16-nrow%16
    col_add = 16-ncol%16
    padded = np.pad(im, ((0, row_add), (0, col_add)))
    
    model = unet(pretrained_weights = None,
                 input_size = (None,None,1))
    model.load_weights('unet/unet_weights_batchsize_25_Nepochs_100_SJR0_10.hdf5')

    results = model.predict(padded[np.newaxis,:,:,np.newaxis], batch_size=1)
    
    # revert padding
    res = results[0,:nrow,:nrow,0]
    return res
