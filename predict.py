# -*- coding: utf-8 -*-
"""
Created on Sun Jul 17 17:00:11 2021
Author: stojk

"""
import sys
sys.path.append("./unet")
sys.path.append("./disk")

#Import all the other python files
#this file handles the interaction with the disk, so loading/saving images
#and masks and it also runs the neural network.

import Reader as nd
import argparse
from GUI_main import App
import skimage
import neural_network as nn
from segment import segment


def LaunchInstanceSegmentation(reader, imaging_type, fov_indices=[0], time_value1=0, time_value2=0, thr_val=None, seg_val=10, weights_path=None):
    """
    """

    # check if correct imaging value
    if imaging_type not in ['bf', 'pc']:
        print("Wrong imaging type value ('{}')!".format(imaging_type),
              "imaging type must be either 'bf' or 'pc'")
        return
    is_pc = imaging_type == 'pc'

    # check timepoints constraint
    if time_value1 > time_value2 :
        print("Error", 'Invalid Time Constraints')
        return
    
    # displays that the neural network is running
    print('Running the neural network...')
    
    for fov_ind in fov_indices:

        #iterates over the time indices in the range
        for t in range(time_value1, time_value2+1):         
            print('--------- Segmenting field of view:',fov_ind,'Time point:',t)

            #calls the neural network for time t and selected fov
            im = reader.LoadOneImage(t, fov_ind)

            try:
                pred = App.LaunchPrediction(im, is_pc, pretrained_weights=weights_path)
            except ValueError:
                print('Error! ',
                      'The neural network weight files could not '
                      'be found. \nMake sure to download them from '
                      'the link in the readme and put them into '
                      'the folder unet, or specify a path to a custom weights file with -w argument.')
                return

            thresh = App.ThresholdPred(thr_val, pred)
            seg = segment(thresh, pred, seg_val)
            reader.SaveMask(t, fov_ind, seg)
            print('--------- Finished segmenting.')
            
            # apply tracker if wanted and if not at first time
            temp_mask = reader.CellCorrespondence(t, fov_ind)
            reader.SaveMask(t, fov_ind, temp_mask)

def main(args):

    if '.h5' in args.mask_path:
        args.mask_path = args.mask_path.replace('.h5','')

    reader = nd.Reader("", args.mask_path, args.image_path)

    LaunchInstanceSegmentation(reader, args.imaging_type, args.fovs,
                               args.timepoints[0],  args.timepoints[1], args.threshold, args.segmentation, args.weights_path)

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--image_path', type=str, help="Specify the single image path or images folder path", required=True)
    parser.add_argument('-m', '--mask_path', type=str, help="Specify where to save predicted masks", required=True)
    parser.add_argument('-t', '--imaging_type', type=str, help="Specify the imaging type, possible 'bf' and 'pc'")
    parser.add_argument('-w', '--weights_path', default=None, type=str, help="Specify weights path")
    parser.add_argument('--fovs', default=[0], nargs='+', type=int, help="Specify fovs")
    parser.add_argument('--timepoints', nargs=2, default=[0,0], type=int, help="Specify start and end timepoints")
    parser.add_argument('--threshold', default=None, type=float, help="Specify threshold value")
    parser.add_argument('--segmentation', default=10, type=float, help="Specify segmentation value")
    args = parser.parse_args()
    main(args)
