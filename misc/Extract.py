#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI to select and deselect cells at extraction time.
"""

import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, 
                             QHBoxLayout, QVBoxLayout)

from PIL import Image, ImageDraw


#Import from matplotlib to use it to display the pictures and masks.
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure


class Extract(QWidget):
    
    
    def __init__(self):
        super(Extract, self).__init__()
        image, mask = _test_data()
        self.pc = PlotCanvas(image, mask)
        self.init_UI()
        self.exit_code = 0 # 0: Cancel, 1: Fluorescence, 2: Mask

    def init_UI(self):
        # Extract Buttons
        self.extr_mask = _create_button("Extract Mask", self.do_extr_mask)
        self.extr_fluo = _create_button("Extract Fluorescence", self.do_extr_fluo)
        self.done = _create_button("Cancel", self.do_cancel)
        
        extr_box = QVBoxLayout()
        extr_box.addWidget(self.extr_mask)
        extr_box.addWidget(self.extr_fluo)
        extr_box.addWidget(self.done)
        
        # Select Button
        self.sel_mult = _create_button("Select Multiple", self.do_sel_mult)
        self.sel_sngl = _create_button("Select Single", self.do_sel_sngl)
        self.desel_mult = _create_button("Deselect Multiple", self.do_desel_mult)
        self.desel_sngl = _create_button("Deselect Single", self.do_desel_sngl)
        
        sel_box = QVBoxLayout()
        sel_box.addWidget(self.sel_mult)
        sel_box.addWidget(self.sel_sngl)
        sel_box.addWidget(self.desel_mult)
        sel_box.addWidget(self.desel_sngl)
        
        # Button list
        self.buttons = [self.extr_mask,
                        self.extr_fluo,
                        self.done,
                        self.sel_mult,
                        self.sel_sngl,
                        self.desel_mult,
                        self.desel_sngl]
        
        # Buttons
        buttons = QHBoxLayout()
        buttons.addLayout(sel_box)
        buttons.addStretch(.5)
        buttons.addLayout(extr_box)
        
        # Plot Canvas
        full = QVBoxLayout()
        full.addWidget(self.pc)
        full.addStretch(.5)
        full.addLayout(buttons)

        self.setLayout(full)    
        self.setGeometry(300, 300, 600, 600)
        self.setWindowTitle('Extracting')    
        self.show()

    def do_extr_fluo(self):
        self.exit_code = 1
        self.cells = self.pc.sellist
        self.close()

    def do_cancel(self):
        self.close()
    
    def do_extr_mask(self):
        self.exit_code = 2
        self.cells = self.pc.sellist
        self.close()
                
    def do_sel_mult(self):
        """Callback for selecting multiple"""
        self.pc.storemouseclicks = []        
        def to_connect(e):
            self.pc.multiple_click(e, self.do_sel_mult_process)
        self.pc.connect_id = self.pc.mpl_connect(
                'button_press_event', 
                 to_connect)
        self.deactivate_all()
        
    def do_sel_mult_process(self):
        """Process selecting multiple"""
        cells = self.cells_in_polygon()
        self.pc.sellist = self.pc.sellist.union(cells)
        self.disconnect()
        
    def do_desel_mult(self):
        self.pc.storemouseclicks = []        
        """Callback for deselecting multiple"""
        def to_connect(e):
            self.pc.multiple_click(e, self.do_desel_mult_process)
        self.pc.connect_id = self.pc.mpl_connect(
                'button_press_event', 
                 to_connect)
        self.deactivate_all()
        
    def do_desel_mult_process(self):
        """Process deselect multiple"""
        cells = self.cells_in_polygon()
        self.pc.sellist = self.pc.sellist - cells
        self.disconnect()
        
    def cells_in_polygon(self):
        """Extracts cells inside of polygon specified by pc.storemouseclicks"""
        img = Image.new('L', (self.pc.mask.shape), 0)
        ImageDraw.Draw(img).polygon(self.pc.storemouseclicks, outline=1, fill=1)
        polygon = np.array(img).astype(bool)
        return set(np.unique(self.pc.mask[polygon]))
    
    def do_sel_sngl(self):
        """Select single cell"""
        def to_connect(e):
            self.pc.single_click(e, self.do_sel_sngl_process)
        self.pc.connect_id = self.pc.mpl_connect(
                'button_press_event', 
                 to_connect)
        self.deactivate_all()
    
    def do_sel_sngl_process(self, x, y):
        """Process selected cell"""
        if x is not None:
            cell = self.pc.mask[y,x]
            self.pc.sellist.add(cell)
        self.disconnect()
    
    def do_desel_sngl(self):
        """Deselect single cell"""
        def to_connect(e):
            self.pc.single_click(e, self.do_desel_sngl_process)
        self.pc.connect_id = self.pc.mpl_connect(
                'button_press_event', 
                 to_connect)
        self.deactivate_all()
        
    def do_desel_sngl_process(self, x, y):
        """Process deselected cell"""
        if x is not None:
            cell = self.pc.mask[y,x]
            self.pc.sellist.remove(cell)
        self.disconnect()
            
    def disconnect(self):
        """Disconnects callback, updates plots, activates buttons"""
        self.pc.update_plots()
        self.pc.mpl_disconnect(self.pc.connect_id)
        self.activate_all()
        
    def deactivate_all(self):
        for b in self.buttons:
            b.setEnabled(False)
            
    def activate_all(self):
        for b in self.buttons:
            b.setEnabled(True)
    

class PlotCanvas(FigureCanvas):
    
    
    def __init__(self, image, mask, parent=None, figsize=(5,4)):
        """this class defines the canvas. It initializes a figure, which is then
        used to plot our data using imshow.
        """
        fig = Figure()
        self.ax = fig.add_subplot(111)
        super(PlotCanvas, self).__init__(fig)
        self.setParent(parent)
        
        self.image = image
        self.mask = mask
        self.sellist = set(np.unique(mask)) # selected cells
        self.vismask = mask.copy() # mask with only selected cells
        
        self.ax_image, self.ax_mask = self.initialize_plots(image, mask, self.ax)        
        self.storemouseclicks = []
        self.connect_id = None

    def initialize_plots(self, picture, mask, ax):
        """Creates plots at initialization"""
        newcmp = _colormap(21)
        ax.axis("off")
        self.draw()
        return (ax.imshow(picture, interpolation= 'None', 
                          origin = 'upper', cmap = 'gray_r'), 
                ax.imshow((mask%10+1)*(mask != 0), origin = 'upper', 
                          interpolation = 'None', cmap = newcmp,
                          vmin=0, vmax=11))
            
    def single_click(self, event, call_after):
        """Function for single click, calls call_after afterwards with
        the clicked points (or None, None) if abort click."""
        if (event.button == 1
            and (event.xdata != None and event.ydata != None) 
            and self.ax == event.inaxes):
            x = int(event.xdata)
            y = int(event.ydata)
            call_after(x, y)
        else:
            call_after(None, None)
            
    def multiple_click(self, event, call_after):
        """Function to keep track of multiple left clicks, confirmed with 
        a right click. After right click, the function call_after is called"""        
        
        if (event.button == 1  # left click
            and (event.xdata != None and event.ydata != None) 
            and self.ax == event.inaxes):
            
            newx = int(event.xdata)
            newy = int(event.ydata)
            self.storemouseclicks.append((newx, newy))
            self.draw_click(newx, newy)
        
        elif (event.button == 3): # right click
            self.mpl_disconnect(self.connect_id)
            call_after()
        
    def draw_click(self, posx, posy):
        """
        it updates the plot once the user clicks on the plot and draws a 4x4 pixel dot
        at the coordinate of the click 
        """     
        self.vismask[posy:posy+2, posx:posx+2] = 9
        self.redraw_mask()

    def redraw_mask(self):
        """Redraw mask with current self.vismask"""
        self.ax_mask.set_data((self.vismask%10+1)*(self.vismask!=0))
        self.ax.draw_artist(self.ax_image)
        self.ax.draw_artist(self.ax_mask)
        self.update()
        self.flush_events()

    def recalculate_vismask(self):
        """Recalculates vismask with current list of cells to show"""
        tmp = self.mask.copy()
        all_cells = set(np.unique(tmp))
        to_remove = all_cells - self.sellist
        for cell in to_remove:
            tmp[tmp==cell] = 0
        self.vismask = tmp

    def update_plots(self):
        """Shows plot with currently selected cells"""
        self.recalculate_vismask()
        self.redraw_mask()

def _create_button(text, connect, tooltip=None):
    """Initializes button, connects with callback connect"""
    button = QPushButton(text)
    button.clicked.connect(connect)
    button.setMaximumWidth(150)
    
    if tooltip is not None:
        button.setToolTip(tooltip)
    
    return button

def _colormap(Ncolors=21):
    """Creates colormap for segmentation mask"""
    jet = cm.get_cmap('jet', Ncolors)
    
    cmaplist = [(0,0,0,0)]
    for i in range(jet.N):
        r,g,b,_ = jet(i)
        cmaplist.append((r,g,b,.2))
    cmap = LinearSegmentedColormap.from_list('Custom cmap', cmaplist, Ncolors)
    return cmap  
        
def _poly_to_mask(polygon, shape):
    """Converts polygon to mask"""
    img = Image.new('L', shape, 0)
    ImageDraw.Draw(img).polygon(polygon, outline=0, fill=1)
    return np.array(img).astype(int)

def _poly_to_line(polygon, shape):
    """Converts polygon to line"""
    img = Image.new('L', shape, 0)
    ImageDraw.Draw(img).polygon(polygon, outline=1, fill=0)
    return np.array(img).astype(int)

def _test_data():
    """Creates test data"""
    im = np.zeros((100,100))
    mask = np.zeros(im.shape)

    poly1 = [(20,20),(30,30),(20,40),(10,30)]
    poly2 = [(50,50),(60,60),(50,70),(40,60)]

    mask += _poly_to_mask(poly1, im.shape)
    mask += _poly_to_mask(poly2, im.shape)*2
    im += _poly_to_line(poly1, im.shape)
    im += _poly_to_line(poly2, im.shape)
    
    return im, mask
        
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Extract()
    sys.exit(app.exec_())