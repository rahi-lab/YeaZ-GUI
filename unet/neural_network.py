
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 21 18:54:10 2019

"""
import os

from model import *
from data import *
#from quality_measures import *
from segment import *
from data_processing import *

import numpy as np
import skimage
from skimage import io


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
    imsize=im.shape
    im = im[0:2048,0:2048] #crop image if too large
    im = np.pad(im,
                ((0, max(0,2048 - imsize[0])),(0, max(0,2048 -  imsize[1]))),
                constant_values=0) # pad with zeros if too small

    path_test = './tmp/test/image/'
    create_directory_if_not_exists(path_test)

#    io.imsave(path_test+'0.png',im)
    # TESTING SET
#    img_num, resized_shape, original_shape = generate_test_set(im,path_test)

    # WHOLE CELL PREDICTION
    testGene = testGenerator(path_test,
                             1,
                             target_size = (2048,2048) )

    model = unet(pretrained_weights = None,
                 input_size = (2048,2048,1))

#    model.load_weights('unet/unet_weights_batchsize_25_Nepochs_100_full.hdf5')
    model.load_weights('unet/unet_weights_batchsize_25_Nepochs_100_SJR0_10.hdf5')

    results = model.predict_generator(testGene,
                                      1,
                                      verbose=1)

    res = results[0,:,:,0]
    res = res[0:imsize[0],0:imsize[1]] #crop if needed, e.g., im was smaller than 2048x2048
    res = np.pad(res,
                 ((0, max(0,imsize[0] - 2048)),
                  (0, max(0,imsize[0] - 2048) )),
                  constant_values=0)	# pad with zeros if too small

    return res

