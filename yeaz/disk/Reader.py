#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 15:00:29 2019

This file handles all interactions with the hdf and image files, such as 
loading or saving a particular image.
"""
from nd2reader import ND2Reader
import numpy as np
import re
import h5py
import os.path
import skimage
import skimage.io

from ..unet import hungarian as hu
import logging
import os
logging.basicConfig(
    format='%(asctime)s %(levelname)s %(funcName)s: %(message)s',
    level=os.environ.get("LOGLEVEL", "WARNING")
)
log = logging.getLogger(__name__)


class Reader:
    
    
    def __init__(self, hdfpathname, newhdfname, nd2pathname):
        """
        Initializes the data corresponding to the sizes of the pictures,
        the number of different fields of views(Npos) taken in the experiment.
        And it also sets the number of time frames per field of view.
        """
        # Identify filetype of image file
        _, self.extension = os.path.splitext(nd2pathname)
        self.isnd2 = self.extension == '.nd2'
        self.isfolder = self.extension == ''
        self.issingle = self.extension in ['.tif','.tiff',
                                            '.jpg','.jpeg','.png','.bmp',
                                           '.pbm','.pgm','.ppm','.pxm','.pnm','.jp2',
                                           '.TIF','.TIFF',
                                            '.JPG','.JPEG','.PNG','.BMP',
                                           '.PBM','.PGM','.PPM','.PXM','.PNM','.JP2']
        
        self.nd2path = nd2pathname # path name is nd2path for legacy reasons
        self.hdfpath = hdfpathname
        self.newhdfpath = newhdfname
        
        if self.isnd2:
            with ND2Reader(self.nd2path) as images:
                self.sizex = images.sizes['x']
                self.sizey = images.sizes['y']
                self.sizet = images.sizes['t']
                try:
                    self.sizec = images.sizes['c']
                except KeyError:
                    self.sizec = 1
                try:
                    self.Npos  = images.sizes['v']
                except KeyError:
                    self.Npos  = 1
                self.channel_names = images.metadata['channels']
                
        elif self.issingle:
#            with pytiff.Tiff(self.nd2path) as handle:
#                self.sizey, self.sizex = handle.shape #SJR: changed by me
#                self.sizec = 1
#                self.sizet = handle.number_of_pages
#                self.Npos = 1
#                self.channel_names = ['Channel1']
            im = skimage.io.imread(self.nd2path)

            if im.ndim==3:
                # num pages should be smaller than x or y dimension, very unlikely not to be the case
                if im.shape[2] < im.shape[0] and im.shape[2] < im.shape[1]:  
                    im = np.moveaxis(im, -1, 0) # move last axis to first
                self.sizet, self.sizey, self.sizex = im.shape
            else:
                self.sizey, self.sizex = im.shape
                self.sizet = 1
                
            self.Npos = 1
            self.channel_names = ['Channel1']
                
        elif self.isfolder:
            filelist = sorted(os.listdir(self.nd2path))  
            # filter filelist for supported image files
            filelist = [f for f in filelist if re.search(r".png|.tif|.jpg|.bmp|.jpeg|.pbm|.pgm|.ppm|.pxm|.pnm|.jp2"
                                                         "|.PNG|.TIF|.JPG|.BMP|.JPEG|.PBM|.PGM|.PPM|.PXM|.PNM|.JP2", f)]          
            for f in filelist:
                if f.startswith('.'):
                    filelist.remove(f)
            self.sizey = 0
            self.sizex = 0
            self.sizec = 1
            self.Npos = 1
            self.sizet = len(filelist)
            
            for f in filelist:
                im = skimage.io.imread(os.path.join(self.nd2path , f))
                if im.ndim==3:
                    self.sizec = max(self.sizec, im.shape[0])
                    self.sizey = max(self.sizey, im.shape[1]) #SJR: changed by me
                    self.sizex = max(self.sizex, im.shape[2]) #SJR: changed by me
                else:
                    self.sizey = max(self.sizey, im.shape[0]) #SJR: changed by me
                    self.sizex = max(self.sizex, im.shape[1]) #SJR: changed by me

            self.channel_names = [f'Channel{i}' for i in range(1,self.sizec+1)]

        #create the labels which index the masks with respect to time and 
        #fov indices in the hdf5 file
        self.fovlabels = []
        self.tlabels = []        
        self.InitLabels()
        
        self.default_channel = 0
        self.name = self.hdfpath
                            
        # create an new hfd5 file if no one existing already
        self.Inithdf()

        
    def InitLabels(self):
        """Create two lists containing all the possible fields of view and time
        labels, in order to access the arrays in the hdf5 file.
        """
        for i in range(0, self.Npos):
            self.fovlabels.append('FOV' + str(i))
        
        for j in range(0, self.sizet):
            self.tlabels.append('T'+ str(j))
    
    
    def Inithdf(self):
        """If the file already exists then it is loaded else 
        a new hdf5 file is created and for every fields of view
        a new group is created in the createhdf method
        """
        newFileExists = os.path.isfile(self.newhdfpath)
        if not self.hdfpath and not newFileExists:            
            return self.Createhdf()
             
        else:
            if not self.hdfpath:
                self.hdfpath = self.newhdfpath
            filenamewithpath, extension = os.path.splitext(self.hdfpath)
                
            # If mask file is a tiff file
            if (extension == '.tiff' or extension == '.tif' or 
               extension == '.TIFF' or extension == '.TIF'):
                im = skimage.io.imread(self.hdfpath)
                imdims = im.shape
                
                # num pages should be smaller than x or y dimension, very unlikely not to be the case
                if len(imdims) == 3 and imdims[2] < imdims[0] and imdims[2] < imdims[1]:  
                    im = np.moveaxis(im, -1, 0) # move last axis to first

                with h5py.File(filenamewithpath + '.h5', 'w') as hf:
                    hf.create_group('FOV0')  
        
                    if im.ndim==2:
                        hf.create_dataset('/FOV0/T0', data = im, compression = 'gzip')
                    elif im.ndim==3:
                        nim = im.shape[0]
                        for i in range(nim):
                            hf.create_dataset('/FOV0/T{}'.format(i), 
                                              data = im[i,:,:], compression = 'gzip')

                self.hdfpath = filenamewithpath + '.h5'
            
            
    def Createhdf(self):
        """In this method, for each field of view one group is created. And 
        in each one of these group, there will be for each time frame a 
        corresponding dataset equivalent to a 2d array containing the 
        corresponding masks data (segmented/thresholded/predicted).
        """
                    
        self.hdfpath = self.newhdfpath
        
        hf = h5py.File(self.hdfpath, 'w')
        for i in range(0, self.Npos):
            grpname = self.fovlabels[i]
            hf.create_group(grpname)
        hf.close()


    def LoadMask(self, currentT, currentFOV):
        """this method is called when one mask should be loaded from the file 
        on the disk to the user's buffer. If there is no mask corresponding
        in the file, it creates the mask corresponding to the given time and 
        field of view index and returns an array filled with zeros.
        """
        
        file = h5py.File(self.hdfpath,'r+')
        if self.TestTimeExist(currentT,currentFOV,file):
            mask = np.array(file['/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT])], dtype = np.uint16)
            log.debug('load mask')
            file.close()
            
            return mask
        
        else:
            zeroarray = np.zeros([self.sizey, self.sizex],dtype = np.uint16)
            file.create_dataset('/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT]), 
                                data = zeroarray, compression = 'gzip')
            log.debug('create dataset with zeroarray')
            file.close()
            return zeroarray
            
            
    def TestTimeExist(self, currentT, currentFOV, file=None):
        """This method tests if the array which is requested by LoadMask
        already exists or not in the hdf file.
        
        If file is None, then it opens the h5py File. Otherwise allows to pass
        an already open file. 
        """
        def closefile(f):
            if file is None:
                f.close()
                
        def openfile(file):
            if file is None:
                return h5py.File(self.hdfpath, 'r+')
            else:
                return file
                            
        if currentT <= len(self.tlabels) - 1 and currentT >= 0:
            f = openfile(file)
            for t in f['/{}'.format(self.fovlabels[currentFOV])].keys():
                # currentT is a number
                # self.tlabels is some string that indexes the time point? E.g., T0?
                if t == self.tlabels[currentT]:
                    closefile(f)
                    return True
            closefile(f)
            return False
        else:
            return False

            
    def SaveMask(self, currentT, currentFOV, mask):
        """This function is called when the user wants to save the mask in the
        hdf5 file on the disk. It overwrites the existing array with the new 
        one given in argument. 
        If it is a new mask, there should already
        be an existing null array which has been created by the LoadMask method
        when the new array has been loaded/created in the main before calling
        this save method.
        """
        
        file = h5py.File(self.hdfpath, 'r+')
        
        if self.TestTimeExist(currentT,currentFOV,file):
            dataset= file['/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT])]
            dataset[:] = mask
            log.debug('save mask for FOV {} and frame {} to file'.format(self.fovlabels[currentFOV], self.tlabels[currentT]))
            file.close()
            
        else:
            file.create_dataset('/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT]), data = mask, compression = 'gzip')
            log.debug('create dateset and save mask to file')
            file.close()
        
        
    def TestIndexRange(self,currentT, currentfov):
        """this method receives the time and the fov index and checks
        if it is present in the images data.
        """
        
        if currentT < (self.sizet-1) and currentfov < self.Npos:
            return True
        if currentT == self.sizet - 1 and currentfov < self.Npos:
            return False


    def LoadOneImage(self,currentT, currentfov):
        """This method returns from the nd2 file, the picture requested by the 
        main program as an array. It fixes the fov index and iterates over the 
        time index.
        """
        if not (currentT < self.sizet and currentfov < self.Npos):
            return None
        
        if self.isnd2:
            with ND2Reader(self.nd2path) as images:
                try:
                    images.default_coords['v'] = currentfov
                except ValueError:
                    pass
                try:
                    images.default_coords['c'] = self.default_channel
                except ValueError:
                    pass
                images.iter_axes = 't'
                im = images[currentT]
                outputarray = np.array(im, dtype = np.uint16)
                return outputarray

                
        elif self.issingle:
            full = skimage.io.imread(self.nd2path)
            if full.ndim==2:
                im = full
            elif full.ndim==3:
                # num pages should be smaller than x or y dimension, very unlikely not to be the case
                if full.shape[2] < full.shape[0] and full.shape[2] < full.shape[1]:  
                    full = np.moveaxis(full, -1, 0) # move last axis to first
                im = full[currentT]

            outputarray = np.array(im, dtype = np.uint16)
            return outputarray

                                
        elif self.isfolder:
            filelist = sorted(os.listdir(self.nd2path))
            # filter filelist for supported image files
            filelist = [f for f in filelist if re.search(r".png|.tif|.jpg|.bmp|.jpeg|.pbm|.pgm|.ppm|.pxm|.pnm|.jp2"
                                                         "|.PNG|.TIF|.JPG|.BMP|.JPEG|.PBM|.PGM|.PPM|.PXM|.PNM|.JP2", f)]
            for f in filelist:
                if f.startswith('.'):
                    filelist.remove(f)
            
            im = skimage.io.imread(os.path.join(self.nd2path , filelist[currentT]))
            if im.ndim==2:
                im = np.pad(im,( (0, self.sizey - im.shape[0]) , (0, self.sizex -  im.shape[1] ) ),constant_values=0) # pad with zeros so all images in the same folder have same size
                outputarray = np.array(im, dtype = np.uint16)
            elif im.ndim ==3:
                im = np.pad(im,( (0, self.sizec - im.shape[0]) , (0, self.sizey - im.shape[1]) , (0, self.sizex -  im.shape[2] ) ),constant_values=0)
                # number of channels should be smaller than x and y
                if im.shape[2] < im.shape[0] and im.shape[2] < im.shape[1]:  
                    im = np.moveaxis(im, -1, 0) # move last axis to first
                im = im[self.default_channel]
                outputarray = np.array(im, dtype = np.uint16)
            else:
                outputarray = np.zeros([self.sizey, self.sizex],dtype = np.uint16)
                print("Error: image has wrong number of dimensions")
            return outputarray              

    
    def LoadImageChannel(self,currentT, currentFOV, ch):
        """Loads image at specified time, FOV and channel. Only for nd2 files"""
        if self.isnd2:
            with ND2Reader(self.nd2path) as images:
                try:
                    images.default_coords['v'] = currentFOV
                except ValueError:
                    pass
                try:
                    images.iter_axes = 'c'
                except ValueError:
                    pass
                images.default_coords['t'] = currentT
                im = images[ch]
                return np.array(im)
        
        elif self.issingle:
            return self.LoadOneImage(currentT, currentFOV)
                
        elif self.isfolder:
            return self.LoadOneImage(currentT, currentFOV)


    def CellCorrespondence(self, currentT, currentFOV):
        """Performs tracking, handles loading of the images. If the image to 
        track has no precedent, returns unaltered mask. If no mask exists
        for the current timeframe, returns zero array."""
        filemasks = h5py.File(self.hdfpath, 'r+')
        log.debug('Reader.CellCorrespondence')
        
        if self.TestTimeExist(currentT-1, currentFOV, filemasks):
            prevmask = np.array(filemasks['/{}/{}'.format(self.fovlabels[currentFOV], 
                                                          self.tlabels[currentT-1])])
            # A mask exists for both time frames
            if self.TestTimeExist(currentT, currentFOV, filemasks):
                nextmask = np.array(filemasks['/{}/{}'.format(self.fovlabels[currentFOV],
                                                              self.tlabels[currentT])])             
                newmask = hu.correspondence(prevmask, nextmask)
                out = newmask
                log.debug('make new mask')
            # No mask exists for the current timeframe, return empty array
            else:
                null = np.zeros([self.sizey, self.sizex])
                log.warn('No mask exists in FOV {} for the current timeframe {}, return empty array'.format(self.fovlabels[currentFOV],self.tlabels[currentT-1]))
                out = null
        
        else:
            # Current mask exists, but no previous - returns current mask unchanged
            if self.TestTimeExist(currentT, currentFOV, filemasks):
                nextmask = np.array(filemasks['/{}/{}'.format(self.fovlabels[currentFOV],
                                                              self.tlabels[currentT])]) 
                out = nextmask
                log.warn('NCurrent mask exists, but no previous - returns current mask unchanged. FOV {} and Time {}'.format(self.fovlabels[currentFOV],self.tlabels[currentT-1]))
            # Neither current nor previous mask exists - return empty array
            else:
                log.warn('Neither current nor previous mask exists - return empty array. FOV {} and Time {}'.format(self.fovlabels[currentFOV],self.tlabels[currentT-1]))
                null = np.zeros([self.sizey, self.sizex])
                out = null
                    
        filemasks.close()
        return out
                
                
                
        
