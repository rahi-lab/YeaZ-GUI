#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 15 17:05:00 2020

@mattminder
"""

import os
import re
from skimage import io
import numpy as np


def load_image(path, ix=None):
    """Loads Image at specified path. Path can be to single image as supported
    by skimage.io, or to folder containing images supported by skimage.io.
    Ix specifies which image should be loaded, if None it loads all images."""
    
    _, ext = os.path.splitext(path)
    
    # Folder
    if ext=='':
        filelist = sorted(os.listdir(path)) 
        filelist = [f for f in filelist if 
                    re.search(r".png|.tif|.jpg|.bmp|.jpeg|.pbm|.pgm|.ppm|.pxm|.pnm|.jp2|.PNG|.TIF|.JPG|.BMP|.JPEG|.PBM|.PGM|.PPM|.PXM|.PNM|.JP2", f)]
        filelist = [os.path.join(path, f) for f in filelist]
        
        if len(filelist)==0:
            raise ValueError('Folder does not contain images')
        
        if ix is None:
            ims = [io.imread(f) for f in filelist]
            ims = np.array(ims)
            return ims
        else:
            im = io.imread(filelist[ix])
            return im
        
    # File
    else:
        try:
            im = io.imread(path)
        except ValueError:
            raise ValueError('Not an image file')
        
        # Single image
        if im.ndim == 2:
            if ix is not None:
                return im 
            else:
                return im[None,:,:]
        
        # Multistack image
        if im.ndim == 3:
            if ix is None:
                return im 
            else: 
                return im[ix,:,:]
        
