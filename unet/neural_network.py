
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 21 18:54:10 2019

"""
import os
from model import unet
import numpy as np
import skimage
from skimage import io
import skimage.transform as trans


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


def prediction(im):
    """
    Calculate the prediction of the label corresponding to image im
    Param:
        im: a numpy array image (numpy array), with max size 2048x2048
    Return:
        res: the predicted distribution of probability of the labels (numpy array)
    """    
#    imsize=im.shape
#    im = im[0:2048,0:2048] #crop image if too large
#    im = np.pad(im,
#                ((0, max(0,2048 - imsize[0])),(0, max(0,2048 -  imsize[1]))),
#                constant_values=0) # pad with zeros if too small
    
    # pad with zeros such that 
    (nrow, ncol) = im.shape
    padded = np.pad(im, (16-(nrow%16), 16-(ncol%16)))
    
    # WHOLE CELL PREDICTION
    model = unet(pretrained_weights = None,
                 input_size = (None,None,1))

    model.load_weights('unet/unet_weights_batchsize_25_Nepochs_100_SJR0_10.hdf5')

    results = model.predict(padded[np.newaxis,:,:,np.newaxis], batch_size=1)

    res = results[0,:,:,0]
#    res = res[0:imsize[0],0:imsize[1]] #crop if needed, e.g., im was smaller than 2048x2048
#    res = np.pad(res,
#                 ((0, max(0,imsize[0] - 2048)),
#                  (0, max(0,imsize[0] - 2048) )),
#                  constant_values=0)	# pad with zeros if too small
#    print(res)
    return res[:nrow, :ncol]

#
#def generator(im, target_size = (256,256)):
#    im2 = im.copy()
#    im2 /= 255
#    im2 = trans.resize(im2,target_size)
#    im2 = np.reshape(im2,im2.shape+(1,))
#    im2 = np.reshape(im2,(1,)+im2.shape)
#    yield im2
#
