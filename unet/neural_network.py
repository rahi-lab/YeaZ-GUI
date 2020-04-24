
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 21 18:54:10 2019

"""
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
    path_test = './tmp/test/image/'
    create_directory_if_not_exists(path_test)

    io.imsave(path_test+'0.png',im)
    # TESTING SET
#    img_num, resized_shape, original_shape = generate_test_set(im,path_test)

    # WHOLE CELL PREDICTION
    testGene = testGenerator(path_test,
                             1,
                             target_size = (2048,2048) )

    model = unet( pretrained_weights = None,
                  input_size = (2048,2048,1) )

    model.load_weights('./unet_weights_batchsize_25_Nepochs_100_full.hdf5')

    results = model.predict_generator(testGene,
                                      1,
                                      verbose=1)

#    res = reconstruct_result(236, results[:,10:246,10:246,0], resized_shape,original_shape)
#   if the size of the image is not 2048x2048, the difference between 2048x2048
#   and the original size is cut off here. (in the prediction it is
#   artificially augmented from the original size to 2048x2048)

    index_x = 2048-len(im[:,0])
    index_y = 2048-len(im[0,:])
    #this bolean values are true if index_x(y)/2 else they are false.
    #they are initialized to false.
    flagx = False
    flagy = False

    #test if x dimension of im is not already the max size
    if index_x != 0:
        #if index_x not the 0 (im has not max size in x axis) then the
        #the difference is divided by two, index_x is the difference between
        #size of im in x axis and max size 2048
       ind_x = index_x/2
       if index_x%2 == 0:
           ind_x = int(ind_x)
           flagx = True
    else:
        #if already max size, it is set to 0
       ind_x = 0
       flagx = True

    #test if y dimension of im is not already the max size
    if index_y != 0:
        #if index_y not the 0 (im has not max size in y axis) then the
        #the difference is divided by two, index_y is the difference between
        #size of im in y axis and max size 2048
       ind_y = index_y/2
       if index_y%2 == 0:
           ind_y = int(ind_y)
           flagy = True
    else:
       ind_y = 0
       flagy = True


    if flagx and flagy:
         res = results[0,ind_x:2048-ind_x,ind_y:2048-ind_y,0]
         return res
    elif not(flagx) and flagy:
         res = results[0,int(ind_x):2048-(int(ind_x)+1),ind_y:2048-ind_y,0]
         return res
    elif flagx and not(flagy):
         res = results[0,ind_x:2048-ind_x, int(ind_y):2048-(int(ind_y)+1),0]
         return res
    else:
         res = results[0, int(ind_x):2048-(int(ind_x)+1),int(ind_y):2048-(int(ind_y)+1),0]
         return res
