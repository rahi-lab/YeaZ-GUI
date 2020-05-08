"""
Source of the code: https://github.com/mattminder/yeastSegHelpers
"""
from scipy import ndimage as ndi
from skimage.feature import peak_local_max
from skimage.morphology import watershed

# from PIL import Image
import numpy as np
from skimage import data, util, filters, color
import cv2

# get rid of this
from skimage import io


def segment(th, pred, min_distance=10, topology=None): #SJR: added pred to evaluate new borders
    """
    Performs watershed segmentation on thresholded image. Seeds have to
    have minimal distance of min_distance. topology defines the watershed
    topology to be used, default is the negative distance transform. Can
    either be an array with the same size af th, or a function that will
    be applied to the distance transform.
    """
    dtr = ndi.morphology.distance_transform_edt(th)
    if topology is None:
        print('topology is none')
        topology = -dtr
    elif callable(topology):
        topology = topology(dtr)

    m = peak_local_max(-topology, min_distance, indices=False)
    m_lab = ndi.label(m)[0]
#    print(m_lab.shape)
#    print(type(m_lab[0,0]))
#    print(type(th[0,0]))
#    print(type(topology[0,0]))
#    io.imsave("/home/sjrahi/Desktop/peaks.tif",               np.array(m_lab, np.uint32))
#    io.imsave("/home/sjrahi/Desktop/image.tif",               np.array(th, np.float32))
#    io.imsave("/home/sjrahi/Desktop/top.tif",                 np.array(topology, np.float32))
#    io.imsave("/home/sjrahi/Desktop/peaks.tif",               m_lab)
#    io.imsave("/home/sjrahi/Desktop/image.tif",               th)
#    io.imsave("/home/sjrahi/Desktop/top.tif",                 topology)
    wsh = watershed(topology, m_lab, mask=th)

#    print(m_lab.shape)
#    print(wsh.shape)
#    print(th.shape)
#    print(topology.shape)

    print(type(wsh[0,0]))
#    io.imsave("/home/sjrahi/Desktop/wsh.tif",               np.array(wsh, np.uint32))
#    io.imsave("/home/sjrahi/Desktop/wsh.tif",                 wsh)


    wshshape=wsh.shape	# size of the watershed images, could probably get the sizes from the original input images but too lazy to figure out how
    oriobjs=np.zeros((wsh.max()+1,wshshape[0],wshshape[1]))	# the masks for the original cells are saved each separately here
    dilobjs=np.zeros((wsh.max()+1,wshshape[0],wshshape[1]))	# the masks for dilated cells are saved each separately here
    objcoords=np.zeros((wsh.max()+1,4))			# coordinates of the bounding boxes for each dilated object saved here
    wshclean=np.zeros((wshshape[0],wshshape[1]))
    
    kernel = np.ones((3,3), np.uint8)	# need kernel to dilate objects
    for obj1 in range(0,wsh.max()):	# objects numbered starting with 0!! Careful!!
        oriobjs[obj1,:,:] = np.uint8(np.multiply(wsh==(obj1+1),1))		# create a mask for each object (number: obj1+1)
        dilobjs[obj1,:,:] = cv2.dilate(oriobjs[obj1,:,:], kernel, iterations=1)	# create a mask for each object (number: obj1+1) after dilation
        objallpixels=np.where(dilobjs[obj1,:,:] != 0)
        objcoords[obj1,0]=np.min(objallpixels[0])
        objcoords[obj1,1]=np.max(objallpixels[0])
        objcoords[obj1,2]=np.min(objallpixels[1])
        objcoords[obj1,3]=np.max(objallpixels[1])
    
    objcounter = 0	# will build up a new watershed mask, have to run a counter because some objects lost
    for obj1 in range(0,wsh.max()):	#careful, object numbers -1 !
        print("Processing cell ",obj1+1," of ",wsh.max()," for oversegmentation.")
        maskobj1 = dilobjs[obj1,:,:]

        if np.sum(maskobj1) > 0:		#maskobj1 can be empty because in the loop, maskobj2 can be deleted if it is joined with a (previous) maskobj1
            objcounter = objcounter + 1
            maskoriobj1 = oriobjs[obj1,:,:]

            for obj2 in range(obj1+1,wsh.max()):
                maskobj2 = dilobjs[obj2,:,:]
            
                if (np.sum(maskobj2) > 0 and	#maskobj1 and 2 can be empty because joined with maskobj2's and then maskobj2's deleted (set to zero)
                (((objcoords[obj1,0] - 2 < objcoords[obj2,0] and objcoords[obj1,1] + 2 > objcoords[obj2,0]) or		# do the bounding boxes overlap? plus/minus 2 pixels to allow for bad bounding box measurement
                  (objcoords[obj2,0] - 2 < objcoords[obj1,0] and objcoords[obj2,1] + 2 > objcoords[obj1,0])) and
                 ((objcoords[obj1,2] - 2 < objcoords[obj2,2] and objcoords[obj1,3] + 2 > objcoords[obj2,2]) or
                  (objcoords[obj2,2] - 2 < objcoords[obj1,2] and objcoords[obj2,3] + 2 > objcoords[obj1,2])))):
                    border = maskobj1 * maskobj2	#intersection of two masks constitutes a border
                    # borderarea = np.sum(border)
                    # borderpred = border * pred
                    # borderheight = np.sum(borderpred)

                    borderprednonzero = pred[np.nonzero(border)]		# all the prediction values inside the border area
                    sortborderprednonzero = sorted(borderprednonzero)		# sort the values
                    borderprednonzeroarea = len(borderprednonzero)		# how many values are there?
                    quartborderarea = round(borderprednonzeroarea/4)		# take one fourth of the values. there is some subtlety about how round() rounds but doesn't matter
                    topborderpred = sortborderprednonzero[quartborderarea:]	# take top 3/4 of the predictions
                    topborderheight = np.sum(topborderpred)			# sum over top 3/4 of the predictions
                    topborderarea = len(topborderpred)				# area of 3/4 of predictions. In principle equal to 3/4 of borderprednonzeroarea but because of strange rounding, will just measure again

                    if topborderarea > 8:	# SJR: Not only must borderarea be greater than 0 but also have a little bit of border to go on.
                        #print(obj1+1, obj2+1, topborderheight/topborderarea)
                        if topborderheight/topborderarea > 0.99 :	# SJR: We are really deep inside a cell, where the prediction is =1. Won't use: borderheight/borderarea > 0.95. Redundant.
                            #print("--")
                            #print(objcounter)
                            #wsh=np.where(wsh==obj2+1, obj1+1, wsh)
                            maskoriobj1       = np.uint8(np.multiply((maskoriobj1 > 0) | (oriobjs[obj2,:,:] > 0),1))		#have to do boolean then integer just to do an 'or'
                            dilobjs[obj1,:,:] = np.uint8(np.multiply((maskobj1    > 0) | (maskobj2          > 0),1))		#have to do boolean then integer just to do an 'or'
                            dilobjs[obj2,:,:] = np.zeros((wshshape[0],wshshape[1]))
                            objcoords[obj1,0] = min(objcoords[obj1,0],objcoords[obj2,0])
                            objcoords[obj1,1] = max(objcoords[obj1,1],objcoords[obj2,1])
                            objcoords[obj1,2] = min(objcoords[obj1,2],objcoords[obj2,2])
                            objcoords[obj1,3] = max(objcoords[obj1,3],objcoords[obj2,3])
                            print("Merged cell ",obj1+1," and ",obj2+1,".")


            wshclean = wshclean + maskoriobj1*objcounter
        #else:
         #   display(obj1+1,' no longer there.')

    return wshclean
#    return wsh

