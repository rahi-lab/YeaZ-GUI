#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 15:00:29 2019

This program reads out the images from the nd2 file and creates or 
reads the hdf file containing the segmentation.
"""
from nd2reader import ND2Reader
#import matplotlib.pyplot as plt
import numpy as np

import h5py
import os.path
import skimage
import skimage.io
#import segment as seg
import neural_network as nn
import pytiff


import hungarian as hu
# import CellCorrespondance as cc
# import matplotlib.pyplot as plt



class Reader:
    
    def __init__(self, hdfpathname, newhdfname, nd2pathname):

        
#        Initializes the data corresponding to the sizes of the pictures,
#        the number of different fields of views(Npos) taken in the experiment.
#        And it also sets the number of time frames per field of view.
        
        # Identify filetype of image file
        _, self.extension = os.path.splitext(nd2pathname)
        self.isnd2 = self.extension == '.nd2'
        self.istiff = self.extension == '.tif' or self.extension == '.tiff'
        self.isfolder = self.extension == ''
        
        
        self.nd2path = nd2pathname # path name is nd2path for legacy reasons
        self.hdfpath = hdfpathname
        self.newhdfname = newhdfname
        
        if self.isnd2:
            with ND2Reader(self.nd2path) as images:
                self.sizex = images.sizes['x']
                self.sizey = images.sizes['y']
                self.sizec = images.sizes['c']
                self.sizet = images.sizes['t']
                print("Debug: self.sizet",self.sizet)
                try:
                    self.Npos  = images.sizes['v']
                except KeyError:
                    self.Npos  = 1
                self.channel_names = images.metadata['channels']
                
        elif self.istiff:
            with pytiff.Tiff(self.nd2path) as handle:
                self.sizey, self.sizex = handle.shape #SJR: changed by me
                self.sizec = 1
                self.sizet = handle.number_of_pages
                print("Debug: handle.number_of_pages",handle.number_of_pages)
                self.Npos = 1
                self.channel_names = ['Channel1']
                
        elif self.isfolder:
            
            filelist = sorted(os.listdir(self.nd2path))

            print(filelist)
            
            for f in filelist:
                if f.startswith('.'):
                    filelist.remove(f)
            
            im = skimage.io.imread(self.nd2path + '/' + filelist[0])
            self.sizey, self.sizex = im.shape #SJR: changed by me
            self.sizec = 1
            self.Npos = 1
            self.sizet = len(filelist)
            print("Debug: self.sizet",self.sizet)
            self.channel_names = ['Channel1']
                            
        #create the labels which index the masks with respect to time and 
        #fov indices in the hdf5 file
        self.fovlabels = []
        self.tlabels = []        
        self.InitLabels()
        
        self.default_channel = 0
        
        self.name = self.hdfpath
        
        self.predictname = ''
        self.thresholdname = ''
        self.segmentname = ''
        
#        self.channelwindow = chch.CustomDialog(self)
#        
#        if self.channelwindow.exec_():
#
#             self.default_channel = self.channelwindow.button_channel.currentIndex()
             
            
#        create an new hfd5 file if no one existing already
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
        
        if not self.hdfpath:
            return self.Createhdf()
        else:
            
            filenamewithpath, extension = os.path.splitext(self.hdfpath)
            
            if extension == ".h5":
                temp = self.hdfpath[:-3]
            
                self.thresholdname = temp + '_thresholded' + '.h5'
                self.segmentname = temp + '_segmented' + '.h5'
                self.predictname = temp + '_predicted' + '.h5'
            #SJR: Mask is a tiff file
            elif extension == '.tiff' or extension == '.tif':
                #SJR: Careful, self.hdfpath is a tif file
                im = skimage.io.imread(self.hdfpath)
                print('Inithdf',im.shape)
                imdims = im.shape
                if len(imdims) == 3 and imdims[2] < imdims[0] and imdims[2] < imdims[1]:  # num pages should be smaller than x or y dimension, very unlikely not to be the case
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

                #SJR addition:
                self.thresholdname = filenamewithpath + '_thresholded' + '.h5'
                hf = h5py.File(self.thresholdname,'w')
                hf.create_group('FOV0')
                hf.close()
    
                self.segmentname = filenamewithpath + '_segmented' + '.h5'
                hf = h5py.File(self.segmentname,'w')
                hf.create_group('FOV0')
                hf.close()
    
                self.predictname = filenamewithpath + '_predicted' + '.h5'
                hf = h5py.File(self.predictname,'w')
                hf.create_group('FOV0')
                hf.close()

                self.hdfpath = filenamewithpath + '.h5'




            
            
    def Createhdf(self):
        
        """In this method, for each field of view one group is created. And 
        in each one of these group, there will be for each time frame a 
        corresponding dataset equivalent to a 2d array containing the 
        corresponding masks data (segmented/thresholded/predicted).
        """
#        print('createhdf')
        
        self.hdfpath = ''
        templist = self.nd2path.split('/')
        for k in range(0, len(templist)-1):
            self.hdfpath = self.hdfpath+templist[k]+'/'
        
        self.hdfpath = self.hdfpath + self.newhdfname + '.h5'
        
        hf = h5py.File(self.hdfpath, 'w')
        
        for i in range(0, self.Npos):
            
            grpname = self.fovlabels[i]
            hf.create_group(grpname)
            
        hf.close()
        

        
        
        for k in range(0, len(templist)-1):
            self.thresholdname = self.thresholdname+templist[k]+'/'
        self.thresholdname = self.thresholdname + self.newhdfname + '_thresholded' + '.h5'
        
        hf = h5py.File(self.thresholdname,'w')
        
        for i in range(0, self.Npos):
            
            grpname = self.fovlabels[i]
            hf.create_group(grpname)
            
        hf.close()
        
        for k in range(0, len(templist)-1):
            self.segmentname = self.segmentname+templist[k]+'/'
        self.segmentname = self.segmentname + self.newhdfname + '_segmented' + '.h5'
        
        hf = h5py.File(self.segmentname,'w')
        
        for i in range(0, self.Npos):
            
            grpname = self.fovlabels[i]
            hf.create_group(grpname)
            
        hf.close()

        for k in range(0, len(templist)-1):
            self.predictname = self.predictname+templist[k]+'/'
        self.predictname = self.predictname + self.newhdfname + '_predicted' + '.h5'
        
        hf = h5py.File(self.predictname,'w')
     
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
            file.close()
            
            return mask
        
        else:
            
#            change with Matthias code!
            
            zeroarray = np.zeros([self.sizey, self.sizex],dtype = np.uint16)
            file.create_dataset('/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT]), data = zeroarray, compression = 'gzip')
            file.close()
            return zeroarray
            
            
    def TestTimeExist(self,currentT, currentFOV, file):
        """This method tests if the array which is requested by LoadMask
        already exists or not in the hdf file.
        """
        
        for t in file['/{}'.format(self.fovlabels[currentFOV])].keys():
            if t == self.tlabels[currentT]:
                return True
        
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
            file.close()
            
        else:
            
            file.create_dataset('/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT]), data = mask, compression = 'gzip')
            file.close()
        
        
    def SaveThresholdMask(self, currentT, currentFOV, mask):
        """This function is called when the user wants to save the mask in the
        hdf5 file on the disk. It overwrites the existing array with the new 
        one given in argument. 
        If it is a new mask, there should already
        be an existing null array which has been created by the LoadMask method
        when the new array has been loaded/created in the main before calling
        this save method.
        """
        
        file = h5py.File(self.thresholdname, 'r+')
        
        if self.TestTimeExist(currentT,currentFOV,file):
            dataset = file['/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT])]
            dataset[:] = mask
            file.close()
        else:
            file.create_dataset('/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT]), data = mask, compression = 'gzip')
            file.close()
        
    def SaveSegMask(self, currentT, currentFOV, mask):
        """This function is called when the user wants to save the mask in the
        hdf5 file on the disk. It overwrites the existing array with the new 
        one given in argument. 
        If it is a new mask, there should already
        be an existing null array which has been created by the LoadMask method
        when the new array has been loaded/created in the main before calling
        this save method.
        """
        
        file = h5py.File(self.segmentname, 'r+')
        
        if self.TestTimeExist(currentT,currentFOV,file):

            dataset = file['/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT])]
            dataset[:] = mask
            file.close()
        else:
            file.create_dataset('/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT]), data = mask, compression = 'gzip')
            file.close()
    


    def TestIndexRange(self,currentT, currentfov):
        """this method receives the time and the fov index and checks
        if it is present in the images data.
        """
        
        if currentT < (self.sizet-1) and currentfov < self.Npos:
            return True
        if currentT == self.sizet - 1 and currentfov < self.Npos:
            return False
#    
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
                images.default_coords['c'] = self.default_channel
                print('Debug in InteractionDisk_temp',currentfov)
                print('Debug in InteractionDisk_temp',self.default_channel)
                images.iter_axes = 't'
                im = images[currentT]
                
        elif self.istiff:
            with pytiff.Tiff(self.nd2path) as handle:
                handle.set_page(currentT)
                im = handle[:]
                print('Debug in InteractionDisk_temp',im.shape)
#                print('Debug in InteractionDisk_temp',im[0,0],np.amin(im),np.amax(im))
                                
        elif self.isfolder:
            filelist = sorted(os.listdir(self.nd2path))
            for f in filelist:
                if f.startswith('.'):
                    filelist.remove(f)
            im = skimage.io.imread(self.nd2path + '/' + filelist[currentT])
            
        # be careful here, the output is converted to 16, not sure it's a good idea.
        outputarray = np.array(im, dtype = np.uint16)
        print("Time point", currentT, ". Image properties: ", np.mean(outputarray), " (mean), ", np.std(outputarray), " (std), ", np.median(outputarray), " (median).")
        return outputarray

            
    def LoadSeg(self, currentT, currentFOV):

        file = h5py.File(self.segmentname, 'r+')
        
        if self.TestTimeExist(currentT,currentFOV,file):
            mask = np.array(file['/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT])], dtype = np.uint16)
            file.close()
            return mask
            
        else:

            zeroarray = np.zeros([self.sizey, self.sizex],dtype = np.uint16)
            file.create_dataset('/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT]), data = zeroarray, compression = 'gzip', compression_opts = 7)
            file.close()
            return zeroarray
        
    
        
    def LoadThreshold(self, currentT, currentFOV):
        
        
        file = h5py.File(self.thresholdname, 'r+')
        
        if self.TestTimeExist(currentT,currentFOV,file):

            mask = np.array(file['/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT])], dtype = np.uint16)
            file.close()
            
            return mask
        
        
        else:

            zeroarray = np.zeros([self.sizey, self.sizex],dtype = np.uint16)
            file.create_dataset('/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT]), data = zeroarray, compression = 'gzip', compression_opts = 7)

            file.close()
            return zeroarray
     
    def Segment(self, segparamvalue, currentT, currentFOV):
        print(segparamvalue)

#        Check if thresholded version exists
        filethr = h5py.File(self.thresholdname, 'r+')
        fileprediction = h5py.File(self.predictname,'r+')	# SJR: added to read out the prediction as well

#        if self.TestTimeExist(currentT, currentFOV, filethr):
        if self.TestTimeExist(currentT, currentFOV, filethr) and self.TestTimeExist(currentT, currentFOV, fileprediction):	# SJR: added to read out the prediction as well

            tmpthrmask = np.array(filethr['/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT])])
            pred = np.array(fileprediction['/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT])])	# SJR: added to read out the prediction as well
            fileprediction.close()	# SJR: added to read out the prediction as well

#            segmentedmask = nn.segment(tmpthrmask, segparamvalue)
            segmentedmask = nn.segment(tmpthrmask, pred, segparamvalue)	# SJR: added to read out the prediction as well
            filethr.close()

            return segmentedmask

        else:

            filethr.close()
            return np.zeros([self.sizey,self.sizex], dtype = np.uint16)

        
        
    def ThresholdPred(self, thvalue, currentT, currentFOV):
        print(thvalue)
        
        fileprediction = h5py.File(self.predictname,'r+')
        if self.TestTimeExist(currentT, currentFOV, fileprediction):
            
            pred = np.array(fileprediction['/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT])])
            fileprediction.close()
            if thvalue == None:
                thresholdedmask = nn.threshold(pred)
            else:
                thresholdedmask = nn.threshold(pred,thvalue)
        
            return thresholdedmask
        else:
            fileprediction.close()
            return np.zeros([self.sizey, self.sizex], dtype = np.uint16)
        
#    def LaunchPrediction(self, currentT, currentFOV):
        
    
    def TestPredExisting(self, currentT, currentFOV):
        
        file = h5py.File(self.predictname, 'r+')
        if self.TestTimeExist(currentT, currentFOV, file):
            file.close()
            return True
        else:
            file.close()
            return False
        
        
        
        
        
    def LaunchPrediction(self, currentT, currentFOV):
        
        """It launches the neural neutwork on the current image and creates 
        an hdf file with the prediction for the time T and corresponding FOV. 
        """

        file = h5py.File(self.predictname, 'r+')
        
        
        im = self.LoadOneImage(currentT, currentFOV)
        im = skimage.exposure.equalize_adapthist(im)    # I added this recently because this is what is done before training as well!

        im = im*1.0;	# SJR: for some reason has to be float64
        pred = nn.prediction(im)
        file.create_dataset('/{}/{}'.format(self.fovlabels[currentFOV], 
                                    self.tlabels[currentT]), data = pred, compression = 'gzip', 
                                    compression_opts = 7)
        file.close()
    
#        if self.isnd2:
#            with ND2Reader(self.nd2path) as images:
#                images.default_coords['v'] = currentFOV
#                images.default_coords['c'] = self.default_channel
#                images.iter_axes = 't'
#                temp = images[currentT]
#                temp = np.array(temp, dtype = np.uint16)
#                pred = nn.prediction(temp)
#                file.create_dataset('/{}/{}'.format(self.fovlabels[currentFOV], 
#                                    self.tlabels[currentT]), data = pred, compression = 'gzip', 
#                                    compression_opts = 7)
#        
#        elif self.istiff:
#            None
        




    def CellCorrespondance(self, currentT, currentFOV):
        print('in cell Correspondance')
        filemasks = h5py.File(self.hdfpath, 'r+')
        fileseg = h5py.File(self.segmentname,'r+')
        if self.TestTimeExist(currentT-1, currentFOV, filemasks):
            
            if self.TestTimeExist(currentT, currentFOV, fileseg):
                print('inside cellcorerspoindacefunction')
                prevmask = np.array(filemasks['/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT-1])])
                nextmask = np.array(fileseg['/{}/{}'.format(self.fovlabels[currentFOV], self.tlabels[currentT])])             
                # newmask = cc.CellCorrespondancePlusTheReturn(nextmask, prevmask)
                newmask = hu.correspondance(prevmask, nextmask)
                filemasks.close()
                fileseg.close()
                return newmask
            
            else:
                filemasks.close()
                fileseg.close()
                null = np.zeros([self.sizey, self.sizex])
                
                return null
        else:
            
            filemasks.close()
            fileseg.close()
            null = np.zeros([self.sizey, self.sizex])
            return null
                    
    def LoadImageChannel(self,currentT, currentFOV, ch):
        if self.isnd2:
            with ND2Reader(self.nd2path) as images:
                try:
                    images.default_coords['v'] = currentFOV
                except ValueError:
                    pass
                images.default_coords['t'] = currentT
                images.iter_axes = 'c'
                im = images[ch]
                return np.array(im)
        
        elif self.istiff:
            return self.LoadOneImage(currentT, currentFOV)
                
        elif self.isfolder:
            return self.LoadOneImage(currentT, currentFOV)
                
                
                
        
