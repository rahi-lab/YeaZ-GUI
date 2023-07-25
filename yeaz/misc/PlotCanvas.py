#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This file handles the PlotCanvas of the GUI - aka the area where the graphics 
are shown. 
"""
import numpy as np
from skimage import morphology as morph
from skimage import draw
import logging
import os
logging.basicConfig(
    format='%(asctime)s %(levelname)s %(funcName)s: %(message)s',
    level=os.environ.get("LOGLEVEL", "WARNING")
)
log = logging.getLogger(__name__)


# Import everything for the Graphical User Interface from the PyQt6 library.
from PyQt6.QtWidgets import QSizePolicy

#Import from matplotlib to use it to display the pictures and masks.
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

import matplotlib.pyplot as plt

from matplotlib import cm
from matplotlib.colors import ListedColormap
#from matplotlib.path import Path

from scipy import ndimage

from PIL import Image, ImageDraw



class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None):
        """this class defines the canvas. It initializes a figure, which is then
        used to plot our data using imshow.
        """
        # define three subplots corresponding to the previous, current and next
        # time index.
        fig, (self.ax2, self.ax, self.ax3) = plt.subplots(1,3, sharex = True, sharey = True)
        
        fig.subplots_adjust(bottom=0, top=1, left=0, right=1, wspace = 0.05, hspace = 0.05)
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
        self.parent = parent
        
        # this is some mambo jambo.
        FigureCanvas.setSizePolicy(self, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        FigureCanvas.updateGeometry(self)
        
        # the self.currpicture attribute takes the original data and will then 
        # contain the updates drawn by the user.
        self.currpicture = parent.currentframe
        self.prevpicture = parent.previousframe
        self.nextpicture = parent.nextframe
        self.plotmask = parent.mask_curr
        self.prevplotmask = parent.mask_previous
        self.nextplotmask = parent.mask_next
        self.tempmask = self.plotmask.copy()
        self.tempplotmask = self.plotmask.copy()
        
        # this line is just here to not attribute a zero value to the plot
        # because if so, then it does not update the plot and it stays blank.
        self.prevpicture = self.currpicture.copy()
        
        # Initialize Plots
        self.currplot, self.currmask = self.plot(self.currpicture, self.plotmask, self.ax)
        
        self.previousplot, self.previousmask = self.plot(self.prevpicture, self.prevplotmask, self.ax2)
        self.prevpicture = np.zeros([parent.reader.sizey, parent.reader.sizex], dtype = np.uint16)
        self.prevplotmask = np.zeros([parent.reader.sizey, parent.reader.sizex], dtype =np.uint16)
        
        self.nextplot, self.nextmask = self.plot(self.nextpicture, self.nextplotmask, self.ax3)
        self.previousplot.set_data(self.prevpicture)
        self.previousmask.set_data((self.prevplotmask%10+1)*(self.prevplotmask != 0))

        self.ax2.draw_artist(self.previousplot)
        self.ax2.draw_artist(self.previousmask)
        self.update()
        self.flush_events()
        
        # Set title labels
        self.titlecurr = self.ax.set_title('Time index {}'.format(parent.Tindex))
        self.titleprev = self.ax2.set_title('No frame {}'.format(''))
        self.titlenext = self.ax3.set_title('Next time index {}'.format(parent.Tindex+1))
        
        # these variables are just set to test the states of the buttons
        # (button turned on or  off, etc..) of the buttons in the methods 
        # used in this class.
        self.button_showval_check = parent.button_showval
        self.button_newcell_check = parent.button_newcell
        self.button_add_region_check = parent.button_add_region
        self.button_drawmouse_check = parent.button_drawmouse
        self.button_eraser_check = parent.button_eraser
        self.button_hidemask_check = parent.button_hidemask
        
        # It will plot for the first time and return the imshow function
        self.currmask.set_clim(0, 10)
        self.previousmask.set_clim(0,10)
        self.nextmask.set_clim(0,10)
        
        # This attribute is a list which stores all the clicks of the mouse.
        self.storemouseclicks = []
        
        # This attribute is used to store the square where the mouse has been
        # in order than to draw lines (Paintbrush function)
        self.storebrushclicks = [False,False]
        
        # self.cellval is the variable which sets the value to the pixel
        # whenever something is drawn.
        self.cellval = 0
        
        # These are lists storing all the annotations which are used to
        # show the values of the cells on the plots.
        self.ann_list = []
        self.ann_list_prev = []
        self.ann_list_next = []

        
    def ExchangeCellValue(self, val1, val2):
        """Swaps the values of the cell between two clusters each representing
        one cell. This method is called after the user has entered 
        values in the ExchangeCellValues window.
        """
        if (val1 in self.plotmask) and (val2 in self.plotmask):
            indices = np.where(self.plotmask == val1)
            self.plotmask[self.plotmask == val2] = val1
            for i in range(0,len(indices[0])):
                self.plotmask[indices[0][i], indices[1][i]] = val2
            self.updatedata()
        else:
            raise ValueError('Cell value does not exist.') 
        
        
    def ReleaseClick(self, event):
        """This method is called from the brush button when the mouse is 
        released such that the last coordinate saved when something is drawn
        is set to zero. Because otherwise, if the user starts drawing somewhere
        else, than a straight line is draw between the last point of the
        previous mouse drawing/dragging and the new one which then starts.
        """
        if self.ax == event.inaxes:
            self.storebrushclicks = [False, False]
            self.ShowCellNumbers(type = 'current')

        
    def OneClick(self, event, radius=3):
        """This method is called when the Brush button is activated. And
        sets the value of self.cellval if the click is a right click, or draws
        a square if the click is a left click. (so if the user does just left
        click but does not drag, there will be only a square which is drawn )
        """
        selem = morph.disk(radius-1)
        
        # Right click selects cell
        if (event.button == 3 
            and (event.xdata != None and event.ydata != None) 
            and (not self.button_eraser_check.isChecked()) 
            and self.ax == event.inaxes):
            tempx = int(event.xdata)
            tempy = int(event.ydata)
            self.cellval = self.plotmask[tempy, tempx]
            self.storebrushclicks = [False, False]
            
        # Left click draws square
        elif (event.button == 1 and 
              (event.xdata != None and event.ydata != None) 
              and self.ax == event.inaxes):
            tempx = int(event.xdata)
            tempy = int(event.ydata)
            
            to_change = np.zeros(self.plotmask.shape, dtype=bool)
            to_change[tempy, tempx] = True
            to_change = morph.dilation(to_change, selem)
            
            self.plotmask[to_change] = self.cellval
            self.storebrushclicks = [tempx,tempy]
            self.updatedata()
            
        else:
            return
        
        
    def multiple_click(self, event, call_after, radius=3):
        """Function to keep track of multiple left clicks, confirmed with 
        a right click. After right click, the function call_after is called"""        
        
        if (event.button == 1  # left click
            and (event.xdata != None and event.ydata != None) 
            and self.ax == event.inaxes):
            
            newx = int(event.xdata)
            newy = int(event.ydata)
            self.storemouseclicks.append((newx, newy))
            
            self.updateplot(newx, newy, False)
        
        elif (event.button == 3): # right click
            call_after()

            
    
    def PaintBrush(self, event, radius=3):
        """PantBrush is the method to paint using a "brush" and it is based
        on the mouse event in matplotlib "motion notify event". However it can 
        not record every pixel that the mouse has hovered over (it is too fast).
        So, in order to not only draw points (happens when the mouse is dragged
        too quickly), these points are interpolated here with lines.
        """
        selem = morph.disk(radius-1)
        if (event.button == 1 
            and (event.xdata != None and event.ydata != None) 
            and self.ax == event.inaxes):
            newx = int(event.xdata)
            newy = int(event.ydata)
            # when a new cell value is set, there is no point to interpolate, to
            # draw a line between the points. 
            if self.storebrushclicks[0] == False :
                self.storebrushclicks = [newx,newy]
                
            else:
                oldx, oldy = self.storebrushclicks
                
                rr, cc, _ = draw.line_aa(newy, newx, oldy, oldx)
                to_change = np.zeros(self.plotmask.shape, dtype=bool)
                to_change[rr,cc] = True
                to_change = morph.dilation(to_change, selem)
                self.plotmask[to_change] = self.cellval
                
            self.storebrushclicks = [newx, newy]
            self.updatedata()
            
            
    def MouseClick(self,event):
        """This function is called whenever the add region or the new cell
        buttons are active and the user clicks on the plot. For each 
        click on the plot, it records the coordinate of the click and stores
        it. When the user deactivate the new cell or add region button, 
        all the coordinates are given to the DrawRegion function (if they 
        do not all lie on the same line) and out of the coordinates, it makes
        a polygon. And then draws inside of this polygon by setting the pixels
        to the self.cellval value.
        """
        # button == 1 corresponds to the left click. 
        if (event.button == 1 
            and (event.xdata != None and event.ydata != None) 
            and self.ax == event.inaxes):
            
            # extract the coordinate of the click inside of the matplotlib figure
            # and then takes the integer part
            newx = int(event.xdata)
            newy = int(event.ydata)
            
            # stores the coordinates of the click
            self.storemouseclicks.append((newx, newy))
            
            # draws in the figure a small square (4x4 pixels) to
            # visualize where the user has clicked
            self.updateplot(newx, newy)
                

    def DefineColormap(self, Ncolors):
        """Define a new colormap by assigning 10 values of the jet colormap
            such that there are only colors for the values 0-10 and the values >10
            will be treated with a modulo operation (updatedata function)
        """
        jet = cm.get_cmap('jet', Ncolors)
        colors = []
        for i in range(0,Ncolors):
            if i==0 : 
                # set background transparency to 0
                temp = list(jet(i))
                temp[3]= 0.0
                colors.append(tuple(temp))
                
            else:
                colors.append(jet(i))
                
        colormap = ListedColormap(colors)
        return colormap
           
    
    def plot(self, picture, mask, ax):
        """this function is called for the first time when all the subplots
        are drawn.
        """
        # Define a new colormap with 20 colors.
        newcmp = self.DefineColormap(21)
        ax.axis("off")

        self.draw()
        return (ax.imshow(picture, interpolation= 'None', 
                        origin = 'lower', cmap = 'gray_r'), 
                ax.imshow((mask%10+1)*(mask != 0), origin = 'lower', 
                        interpolation = 'None', alpha = 0.2, cmap = newcmp))
   
    
    def UpdatePlots(self, type = "all"):
        """
        Updates plots, handles mask and cell numbers.
        """
        
        # Plot images
        log.debug('call UpdatePlot')
        self.currplot.set_data(self.currpicture)
        self.currplot.set_clim(np.amin(self.currpicture), np.amax(self.currpicture))
        self.ax.draw_artist(self.currplot)
        
        self.previousplot.set_data(self.prevpicture)
        self.previousplot.set_clim(np.amin(self.prevpicture), np.amax(self.prevpicture))
        self.ax2.draw_artist(self.previousplot)
            
        self.nextplot.set_data(self.nextpicture)
        self.nextplot.set_clim(np.amin(self.nextpicture), np.amax(self.nextpicture))
        self.ax3.draw_artist(self.nextplot)
        
        # Plot masks
        if not self.button_hidemask_check.isChecked():
            self.currmask.set_data((self.plotmask%10+1)*(self.plotmask!=0))
            self.previousmask.set_data((self.prevplotmask%10+1)*(self.prevplotmask != 0))
            self.nextmask.set_data((self.nextplotmask % 10 +1 )*(self.nextplotmask != 0))
            
        else:
            self.currmask.set_data(np.zeros(self.plotmask.shape))
            self.previousmask.set_data(np.zeros(self.plotmask.shape))
            self.nextmask.set_data(np.zeros(self.plotmask.shape))
        
        self.ShowCellNumbers(type=type)
        self.draw()
        self.update()
        self.flush_events()
                
        
    def updatedata(self, flag=True):
        """
        In order to just display the cells so regions with value > 0
        and also to assign to each of the cell values one color,
        the modulo 10 of the value is take and we add 1, to distinguish
        the values of 10,20,30,... from the background (although the bckgrnd
        gets with the addition the value 1) and the result of the 
        modulo is multiplied with a matrix containing a False value for the 
        background coordinates, setting the background to 0 again.
        """
        if flag:
            self.currmask.set_data((self.plotmask%10+1)*(self.plotmask!=0))
        else:
            self.currmask.set_data((self.tempmask%10+1)*(self.tempmask!=0))
        log.debug('updatedata with flag {}'.format(flag))
        # show the updates by redrawing the array using draw_artist, it is faster 
        # to use as it only redraws the array itself, and not everything else.
        self.ax.draw_artist(self.currplot)
        self.ax.draw_artist(self.currmask)
        self.ShowCellNumbers(type='current' if flag else 'None')
        self.update()
        # self.flush_events()
              
        
    def HideMask(self):
        self.UpdatePlots()
        
                 
    def _getCellCenters(self, plotmask):
        """Get approximate locations for cell centers"""
        log.debug('start')
        vals = np.unique(plotmask).astype(int)
        vals = np.delete(vals, np.where(vals == 0))
        centers = np.array(ndimage.measurements.center_of_mass(plotmask, labels=plotmask, index=vals))
        xtemp = np.round(centers[:, 1]).astype(int)
        ytemp = np.round(centers[:, 0]).astype(int)
        log.debug('finish')
        return vals, xtemp, ytemp

    def OnShowCellID(self):
        """This function is only called when we activate the show cell IDs checkbox."""
        self.UpdatePlots(type='all')

    def ShowCellNumbers(self, type='all'):
        """
        Checks whether to show cell numbers, and does so if button is 
        checked
        This function can apply to current frame or to all frames
        """
        log.debug("show cell numbers called with type {}".format(type))
        if self.button_showval_check.isChecked():
            if(type == 'current'):
                self.ShowCellNumbersCurr()
            elif(type == 'all'):
                self.ShowCellNumbersCurr()
                self.ShowCellNumbersNext()
                self.ShowCellNumbersPrev()
            self.draw()
        else:
            self.clearAnnLists()
        
    
    def ShowCellNumbersCurr(self):
        """This function is called to display the cell values and computes the cebter of each cell and
        gives the coordinate where the number will be 
        displayed. The number to be displayed is just given by the value
        in the mask of the cell.
        This function is just used for the current time subplot.
        """         
        
        for i,a in enumerate(self.ann_list):
            a.remove()
        self.ann_list[:] = []
        # check if the mask is not empty
        if np.sum(self.plotmask)==0 :
            return
            
        vals, xtemp, ytemp = self._getCellCenters(self.plotmask)
        if xtemp.any():
            for i in range(0,len(xtemp)):
                ann = self.ax.annotate(str(int(vals[i])), (xtemp[i], ytemp[i]),
                                        ha='center', va='center')
                self.ann_list.append(ann)
    #  self.draw()
                     
             
    def ShowCellNumbersPrev(self):
        """This function is called to display the cell values and computes the cebter of each cell and
        gives the coordinate where the number will be 
        displayed. The number to be displayed is just given by the value
        in the mask of the cell.
        This function is just used for the previous time subplot and check if it is the first frame or not.
        """
        
        for i,a in enumerate(self.ann_list_prev):
            a.remove()
        self.ann_list_prev[:] = []
        
        if(self.parent.Tindex != 0):
            if np.sum(self.prevplotmask)==0 :
                return
            
            vals, xtemp, ytemp = self._getCellCenters(self.prevplotmask)
            if xtemp.any():
                for i in range(0,len(xtemp)):
                    ann = self.ax2.annotate(str(vals[i]), (xtemp[i], ytemp[i]),
                                            ha='center', va='center')
                    self.ann_list_prev.append(ann)
        #  self.draw()
        else:
            self.ann_list_prev = []
             
             
    def ShowCellNumbersNext(self):
        """This function is called to display the cell values and computes the cebter of each cell and
        gives the coordinate where the number will be 
        displayed. The number to be displayed is just given by the value
        in the mask of the cell.
        This function is just used for the next time subplot and check if it is the first frame or not.
        """
        for i,a in enumerate(self.ann_list_next):
            a.remove()
        self.ann_list_next[:] = []
        if(self.parent.Tindex != self.parent.reader.sizet-1):
            if np.sum(self.nextplotmask)==0 :
                return           
            vals, xtemp, ytemp = self._getCellCenters(self.nextplotmask)
                
            if xtemp.any():
                for i in range(0,len(xtemp)):
                    ann = self.ax3.annotate(str(vals[i]), (xtemp[i], ytemp[i]),
                                        ha='center', va='center')
                    self.ann_list_next.append(ann)
        #  self.draw()
        else: 
            self.ann_list_next = []
        
        
    def clearAnnLists(self):
        for ann in self.ann_list:
            ann.remove()
        self.ann_list = []
        for ann in self.ann_list_prev:
            ann.remove()
        self.ann_list_prev = []
        for ann in self.ann_list_next:
            ann.remove()
        self.ann_list_next = []
        
        
    def updateplot(self, posx, posy, first_is_cell=True):
        """
        it updates the plot once the user clicks on the plot and draws a 4x4 pixel dot
        at the coordinate of the click 
        """        
        if first_is_cell:
            # remove the first coordinate as it should only coorespond 
            # to the value that the user wants to attribute to the drawn region   
            xtemp, ytemp = self.storemouseclicks[0]
    
            # here we initialize the value attributed to the pixels.
            # it means that the first click selects the value that will be attributed to
            # the pixels inside the polygon (drawn by the following mouse clicks of the user)
            self.cellval = self.plotmask[ytemp, xtemp]
            
        else:
            self.cellval=1
          
        # drawing the 2x2 square ot of the mouse click
        if ((self.button_newcell_check.isChecked() or self.button_drawmouse_check.isChecked()) 
            and self.cellval == 0):
            self.tempmask[posy:posy+2, posx:posx+2] = 9
        else:
            self.tempmask[posy:posy+2,posx:posx+2] = self.cellval

        # plot the mouseclick
        self.updatedata(False)
          

    def DrawRegion(self, flag):
        """
        this method is used to draw either a new cell (flag = true) or to add a region to 
        an existing cell (flag = false). The flag will just be used to set the
        value of pixels (= self.cellval) in the drawn region. 
        If flag = true, then the value will be the maximal value plus 1. Such 
        that it attributes a new value to the new cell.
        If flag = false, then it will use the value of the first click to set
        the value of the pixels in the new added region. 
        """
        # here the values that have been changed to mark the mouse clicks are 
        # restored such that they don't appear when the region/new cell is 
        # drawn.        
        if flag:
            # if new cell is added, it sets the value of the drawn pixels to a new value
            # corresponding to the new cell
            self.cellval = np.amax(self.plotmask) + 1
            
        else:
            # The first value is taken out as it is just used to set the value
            # to the new region.
            self.storemouseclicks.pop(0)
        
        if len(self.storemouseclicks) <= 2:
            # if only two points or less have been click, it cannot make a area
            # so it justs discards these values and returns. 
            self.storemouseclicks = list(self.storemouseclicks)
            self.storemouseclicks.clear()
            self.updatedata(True)
            return
        
        else:
            # Draw polygon, fill it with cell values
            nx, ny = self.plotmask.shape
            img = Image.new('L', (ny, nx), 0)
            ImageDraw.Draw(img).polygon(self.storemouseclicks, outline=1, fill=1)
            polygon = np.array(img).astype(bool)
            self.plotmask[polygon] = self.cellval
            self.updatedata()
            
        # empty the lists ready for the next region to be drawn.
        self.storemouseclicks = []
        