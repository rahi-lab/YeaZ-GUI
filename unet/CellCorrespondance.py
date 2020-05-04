# -*- coding: utf-8 -*-
"""
Created on Thu Dec 12 10:03:28 2019

Cell Correspondance
"""

import numpy as np
import matplotlib.pyplot as plt


# THIS IS NOT USED ANYMORE





def cell_frame_intersection(nextmask, prevmask, flag):
    """
    This function computes the intersection between the segmented frame and
    the previous frame. It looks at all the segments in the new mask
    (= nextmask) and for each of the segments it finds the corresponding 
    coordinates. These coordinates are then plugged into the previous mask
    and in the corresponding region of the previous mask it takes the cell
    which has the most pixel values in this region (compare the pixel counts).
    And then takes the value of the value which has the biggest number
    of counts in the corresponding region and sets to the segment in the new 
    mask. 
    If the cell value given by the intersection between the frame is = 0, 
    than it means that the new segment intersects mostly with background,
    so it is assumed that a new cell is created and a new value is given
    to this cell.
    of course, it does not work for all the cells (some move, some grow) so 
    the intersection might occur with 
    """
    nwcells = np.unique(nextmask)
    nwcells = nwcells[nwcells >0]
    vals = np.empty(len(nwcells), dtype=int)
    vals[:] = -1
    coord = np.empty(len(nwcells))
    coord = list(coord)
    maxvalue = np.amax(prevmask)
    double_smaller = []
    double_bigger = []
    
    for i, cell in enumerate(nwcells):

            v, c = np.unique(prevmask[nextmask==cell], return_counts=True)
            
            valtemp = v[np.argmax(c)]
            coord[i] = nextmask == cell
            
            if valtemp != 0:
                if valtemp in vals:
                    tempind = []
                    cts = []
                    
                    for k, allval in enumerate(vals):
                            if allval == valtemp:

                                    valbool, ctmp = np.unique(coord[k], return_counts = True)

                                    cts.append(ctmp[valbool == True])
                                    tempind.append(k)
    
#                    cts = np.array(cts)
                    maxpreviouscts = int(np.amax(cts))
                    biggestcoord_index = tempind[np.argmax(cts)]
                    c = int(c[np.argmax(c)])
                        
                                        
                    if len(tempind) == 1:
                        if c > maxpreviouscts:
                                    double_smaller.append(coord[biggestcoord_index])
                                    double_bigger.append(nextmask == cell)
                        else:
                                    double_smaller.append(nextmask == cell)
                                    double_bigger.append(coord[biggestcoord_index])
                    else:
                       
                        if maxpreviouscts >= c:
                            double_smaller.append(nextmask == cell)
                        
                        else:

                            for k in range(0, len(double_bigger)):
                                if not(False in (double_bigger[k] == coord[biggestcoord_index])):
                                    double_smaller.append(double_bigger[k])
                                    double_bigger[k] = coord[biggestcoord_index]
                                    
                                    
                    
                vals[i] = valtemp
                
                
                
                
            else:
                if flag:
                    maxvalue = maxvalue + 1
                    vals[i] = maxvalue
                else:
                    vals[i] = 0
     
    out = nextmask.copy()
    for k, v in zip(nwcells, vals):
        out[k==nextmask] = v
    return out, double_bigger, double_smaller





 


def CellCorrespondance(nextmask, prevmask, returnbool):
    
    nm = nextmask.copy()
    pm = prevmask.copy()
        
    NotifyRegionMask = nextmask.copy()
    NotifyRegionMask[NotifyRegionMask > 0] = 0
    
    CorrespondanceMask, bigcluster, smallcluster = cell_frame_intersection(nm, pm, returnbool)
    
    cm = CorrespondanceMask.copy()
     
    oldcells = np.unique(prevmask)
    oldcells = oldcells[oldcells > 0]
    
    for cellval in oldcells:
        if not(cellval in CorrespondanceMask):

            NotifyRegionMask[prevmask == cellval] = 1
            

    
    for coordinates in smallcluster:        
        val = np.unique(prevmask[coordinates])
        for cellval in oldcells:
            if not(cellval in CorrespondanceMask):
                if cellval in val:
                
                    CorrespondanceMask[coordinates] = cellval
                    NotifyRegionMask[coordinates] = 1

                    
        NotifyRegionMask[coordinates] = 1


            
            


    return CorrespondanceMask, NotifyRegionMask



    
def CellCorrespondancePlusTheReturn(nextmask, prevmask):
    
    firstcorresp, notifymask = CellCorrespondance(nextmask, prevmask, True)
    
    firstmask = firstcorresp.copy()
    pm = prevmask.copy()
    fm = firstcorresp.copy()
#    pm2 = prevmask.copy()
    
    cmreturn, bigclustr, smallclustr = cell_frame_intersection(pm, firstmask, False)
    
#    cmreturn, notifymask = CellCorrespondance(pm, firstmask, False)
    oldcells = np.unique(fm)
    oldcells = oldcells[oldcells > 0]
    
    for cellval in oldcells:
        if not(cellval in cmreturn):

            notifymask[fm == cellval] = 2

    
    
    for coordinates in smallclustr:

        val = np.unique(fm[coordinates])
        for cellval in oldcells:
            if not(cellval in cmreturn):
                if cellval in val:

                    notifymask[coordinates] = 2

        notifymask[coordinates] = 2

            
            


    return fm, notifymask
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
   
        
