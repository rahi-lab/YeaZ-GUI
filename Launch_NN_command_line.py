# Run:
#
# python Launch_NN_command_line.py -i DIRECTORY/IMAGE_FILE -m OUTPUT_MASK_FILE --path_to_weights PATH_TO_HDF5_FILE --fov N --range_of_frames n1 n2 --min_seed_dist 5 --threshold 0.5
# 
# or:
#
# python Launch_NN_command_line.py -i DIRECTORY/IMAGE_FILE -m OUTPUT_MASK_FILE --image_type pc_OR_bf               --fov N --range_of_frames n1 n2 --min_seed_dist 5 --threshold 0.5

import time
import tqdm

import sys
sys.path.append("./unet")
sys.path.append("./disk")

#Import all the other python files
#this file handles the interaction with the disk, so loading/saving images
#and masks and it also runs the neural network.


from segment import segment
import Reader as nd
import argparse
import skimage
import neural_network as nn

import torch

def LaunchPrediction(im, mic_type, pretrained_weights=None, device='cpu'):
    """It launches the neural neutwork on the current image and creates 
    an hdf file with the prediction for the time T and corresponding FOV. 
    """
    im = skimage.exposure.equalize_adapthist(im)
    im = im*1.0;	
    pred = nn.prediction(im, mic_type, pretrained_weights, device=device)
    return pred



def ThresholdPred(thvalue, pred):
    """Thresholds prediction with value"""
    if thvalue == None:
        thresholdedmask = nn.threshold(pred)
    else:
        thresholdedmask = nn.threshold(pred, thvalue)
    return thresholdedmask

def LaunchInstanceSegmentation(reader, image_type, fov_indices=[0], time_value1=0, time_value2=0, thr_val=None, min_seed_dist=5, path_to_weights=None, device='cpu'):
    if (device == 'cuda') and torch.cuda.is_available():
        f_device = 'cuda'
    else:
        f_device = 'cpu' 
    # cannot have both path_to_weights and image_type supplied
    if (image_type is not None) and (path_to_weights is not None):
        print("image_type and path_to_weights cannot be both supplied.")
        return
    

    # check if correct imaging value
    if (image_type not in ['bf', 'pc']) and (path_to_weights is None):
        print("Wrong imaging type value ('{}')!".format(image_type),
              "imaging type must be either 'bf' or 'pc'")
        return

    # check range_of_frames constraint
    if time_value1 > time_value2 :
        print("Error", 'Invalid Time Constraints')
        return
    
    # displays that the neural network is running
    print('Running the neural network on {} ...'.format(f_device))
    
    for fov_ind in tqdm.tqdm(fov_indices, desc='FOV', position=0):

        #iterates over the time indices in the range
        for t in tqdm.tqdm(range(time_value1, time_value2+1), desc='Time', position=1, leave=False):         
            # print('--------- Segmenting field of view:',fov_ind,'Time point:',t)

            #calls the neural network for time t and selected fov
            im = reader.LoadOneImage(t, fov_ind)

            try:
                pred = LaunchPrediction(im, image_type, pretrained_weights=path_to_weights, device=f_device)
            except ValueError:
                print('Error! ',
                      'The neural network weight files could not '
                      'be found. \nMake sure to download them from '
                      'the link in the readme and put them into '
                      'the folder unet, or specify a path to a custom weights file with -w argument.')
                return

            thresh = ThresholdPred(thr_val, pred)
            seg = segment(thresh, pred, min_seed_dist)
            reader.SaveMask(t, fov_ind, seg)
            print('--------- Finished segmenting.')
            
            # apply tracker if wanted and if not at first time
            temp_mask = reader.CellCorrespondence(t, fov_ind)
            reader.SaveMask(t, fov_ind, temp_mask)

def main(args):

    if '.h5' in args.mask_path:
        args.mask_path = args.mask_path.replace('.h5','')

    reader = nd.Reader("", args.mask_path+'.h5', args.image_path)

    LaunchInstanceSegmentation(reader, args.image_type, args.fov,
                               args.range_of_frames[0],  args.range_of_frames[1], 
                               args.threshold, args.min_seed_dist, 
                               args.path_to_weights, device=args.device)

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--image_path', type=str, help="Specify the path to a single image or to a folder of images", required=True)
    parser.add_argument('-m', '--mask_path', type=str, help="Specify where to save predicted masks", required=True)
    parser.add_argument('--image_type', type=str, help="Specify the imaging type, possible types are 'bf', 'pc', and 'fission'. Supersedes path_to_weights.")
    parser.add_argument('--path_to_weights', default=None, type=str, help="Specify weights path.")
    parser.add_argument('--fov', default=[0], nargs='+', type=int, help="Specify field of view index (can specify more than one with space between them).")
    parser.add_argument('--range_of_frames', nargs=2, default=[0,0], type=int, help="Specify start and end in range of frames. (e.g. 0 10)")
    parser.add_argument('--threshold', default=None, type=float, help="Specify threshold value.")
    parser.add_argument('--min_seed_dist', default=5, type=int, help="Specify minimum distance between seeds.")
    parser.add_argument('--device', default='cpu', type=str, help="Specify device to run on (cpu or cuda).")
    args = parser.parse_args()
    main(args)
