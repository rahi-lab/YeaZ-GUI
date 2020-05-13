from scipy import ndimage as ndi
from skimage.feature import peak_local_max
from skimage.morphology import watershed, dilation

import numpy as np
# import cv2


def segment(th, pred, min_distance=10, topology=None): 
    """
    Performs watershed segmentation on thresholded image. Seeds have to
    have minimal distance of min_distance. topology defines the watershed
    topology to be used, default is the negative distance transform. Can
    either be an array with the same size af th, or a function that will
    be applied to the distance transform.
    
    After watershed, the borders found by watershed will be evaluated in terms
    of their predicted value. If the borders are highly predicted to be cells,
    the two cells are merged. 
    """
    dtr = ndi.morphology.distance_transform_edt(th)
    if topology is None:
        print('topology is none')
        topology = -dtr
    elif callable(topology):
        topology = topology(dtr)

    m = peak_local_max(-topology, min_distance, indices=False)
    m_lab = ndi.label(m)[0]
    wsh = watershed(topology, m_lab, mask=th)
    return cell_merge(wsh, pred)
    

def cell_merge(wsh, pred):
    """
    Procedure that merges cells if the border between them is predicted to be
    cell pixels.
    """
    wshshape=wsh.shape
    
    # masks for the original cells
    objs = np.zeros((wsh.max()+1,wshshape[0],wshshape[1]))	
    
    # masks for dilated cells
    dil_objs = np.zeros((wsh.max()+1,wshshape[0],wshshape[1]))
    
    # bounding box coordinates	
    obj_coords = np.zeros((wsh.max()+1,4))
    
    # cleaned watershed, output of function	
    wshclean = np.zeros((wshshape[0],wshshape[1]))
    
    # kernel to dilate objects
    kernel = np.ones((3,3), dtype=bool)	
    
    for obj1 in range(wsh.max()):
        # create masks and dilated masks for obj
        objs[obj1,:,:] = wsh==(obj1+1)	
        dil_objs[obj1,:,:] = dilation(objs[obj1,:,:], kernel)	
        
        # bounding box
        obj_coords[obj1,:] = get_bounding_box(dil_objs[obj1,:,:])
#        objallpixels = np.where(dilobjs[obj1,:,:] != 0)
#        objcoords[obj1,0]=np.min(objallpixels[0])
#        objcoords[obj1,1]=np.max(objallpixels[0])
#        objcoords[obj1,2]=np.min(objallpixels[1])
#        objcoords[obj1,3]=np.max(objallpixels[1])
    
    objcounter = 0	# will build up a new watershed mask, have to run a counter because some objects lost
    
    for obj1 in range(wsh.max()):	
        print("Processing cell ",obj1+1," of ",wsh.max()," for oversegmentation.")
        dil1 = dil_objs[obj1,:,:]

        if np.sum(dil1) > 0:		#dil1 can be empty because in the loop, maskobj2 can be deleted if it is joined with a (previous) maskobj1
            objcounter = objcounter + 1
            orig1 = objs[obj1,:,:]

            for obj2 in range(obj1+1,wsh.max()):
                dil2 = dil_objs[obj2,:,:]
            
                if (do_box_overlap(obj_coords[obj1,:], obj_coords[obj2,:])
                    and np.sum(dil2) > 0):
                    border = dil1 * dil2	
                    
                    border_pred = pred[border]
                    
                    # Border is too small to be considered
                    if len(border_pred) < 32:
                        continue
                    
                    # Sum of top 25% of predicted border values
                    q75 = np.quantile(border_pred, .75)
                    top_border_pred = border_pred[border_pred > q75]
                    top_border_height = top_border_pred.sum()
                    top_border_area = len(top_border_pred)
                    
#                    borderprednonzero = pred[np.nonzero(border)]		# all the prediction values inside the border area
#                    sortborderprednonzero = sorted(borderprednonzero)		# sort the values
#                    borderprednonzeroarea = len(borderprednonzero)		# how many values are there?
#                    quartborderarea = round(borderprednonzeroarea/4)		# take one fourth of the values. there is some subtlety about how round() rounds but doesn't matter
#                    topborderpred = sortborderprednonzero[quartborderarea:]	# take top 3/4 of the predictions
#                    topborderheight = np.sum(topborderpred)			# sum over top 3/4 of the predictions
#                    topborderarea = len(topborderpred)				# area of 3/4 of predictions. In principle equal to 3/4 of borderprednonzeroarea but because of strange rounding, will just measure again

                    # merge cells
                    if top_border_height / top_border_area > .99:
                        orig1 = np.logical_or(orig1, objs[obj2,:,:])
                        dil_objs[obj1,:,:] = np.logical_or(dil1, dil2)
                        dil_objs[obj2,:,:] = np.zeros((wshshape[0], wshshape[1]))
                        obj_coords[obj1,:] = get_bounding_box(dil_objs[obj1,:,:])
                        print("Merged cell ",obj1+1," and ",obj2+1,".")
                        
                        
#                    if topborderarea > 8:	# SJR: Not only must borderarea be greater than 0 but also have a little bit of border to go on.
#                        #print(obj1+1, obj2+1, topborderheight/topborderarea)
#                        if topborderheight/topborderarea > 0.99 :	# SJR: We are really deep inside a cell, where the prediction is =1. Won't use: borderheight/borderarea > 0.95. Redundant.
#                            #print("--")
#                            #print(objcounter)
#                            #wsh=np.where(wsh==obj2+1, obj1+1, wsh)
#                            maskoriobj1       = np.uint8(np.multiply((maskoriobj1 > 0) | (oriobjs[obj2,:,:] > 0),1))		#have to do boolean then integer just to do an 'or'
#                            dilobjs[obj1,:,:] = np.uint8(np.multiply((maskobj1    > 0) | (maskobj2          > 0),1))		#have to do boolean then integer just to do an 'or'
#                            dilobjs[obj2,:,:] = np.zeros((wshshape[0],wshshape[1]))
#                            objcoords[obj1,0] = min(objcoords[obj1,0],objcoords[obj2,0])
#                            objcoords[obj1,1] = max(objcoords[obj1,1],objcoords[obj2,1])
#                            objcoords[obj1,2] = min(objcoords[obj1,2],objcoords[obj2,2])
#                            objcoords[obj1,3] = max(objcoords[obj1,3],objcoords[obj2,3])
#                            print("Merged cell ",obj1+1," and ",obj2+1,".")

            wshclean = wshclean + orig1*objcounter
            
    return wshclean


def do_box_overlap(coord1, coord2):
    """Checks if boxes, determined by their coordinates, overlap. Safety
    margin of 2 pixels"""
    return (
    (coord1[0] - 2 < coord2[0] and coord1[1] + 2 > coord2[0]
        or coord2[0] - 2 < coord1[0] and coord2[1] + 2 > coord1[0]) 
    and (coord1[2] - 2 < coord2[2] and coord1[3] + 2 > coord2[2]
        or coord2[2] - 2 < coord1[2] and coord2[3] + 2 > coord1[2]))

    
def get_bounding_box(im):
    """Returns bounding box of object in boolean image"""
    coords = np.where(im)
    
    return np.array([np.min(coords[0]), np.max(coords[0]), 
                     np.min(coords[1]), np.max(coords[1])])
