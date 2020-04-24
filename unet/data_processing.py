import numpy as np

import skimage
from skimage import io
from skimage.util import img_as_ubyte
from skimage import morphology


#############
#           #
#  READING  #
#           #
#############

def read_im_tiff(path, num_frames=None):
    """
    Read a multiple page tiff images file, adapt the contrast and stock each
    frame in a np.array
    Param:
        path: path to the tiff movie
        num_frames: (integer) number of frames to read
    Return:
        images:
    """

    ims = io.imread(path)
    images = []

    if(num_frames == None):
        num_frames = ims.shape[0]

    for i in range(num_frames):
        im = skimage.exposure.equalize_adapthist(ims[i])
        images.append(np.array(im))

    return images



def read_lab_tiff(path, num_frames=None):
    """
    Read a multiple page tiff label file and stock each frame in a np.array
    Param:
        path: path to the tiff movie
        num_frames: (integer) number of frames to read
    Return:
        images: (np.array) array containing the desired frames
    """
    
    ims = io.imread(path)
    images = []

    if(num_frames == None):
        
        num_frames = ims.shape[0]

    for i in range(num_frames):
        
        images.append(np.array(ims[i]))

    return images



################################
#                              #
#  GENERAL PROCESSING METHODS  #
#                              #
################################

def pad(im, size):
    """
    Carry a mirror padding on an image to end up with a squared image dividable in multiple tiles of shape size x size pixels
    Param:
        im: (np.array) input image
        size: (integer) size of the tiles
    Return:
        out: (np.array) output image reshaped to the good dimension
    """

    # add mirror part along x-axis
    nx = im.shape[1]
    ny = im.shape[0]

    if(nx % size != 0.0):
        restx = int(size - nx % size)
        outx = np.pad(im, ((0,0), (0,restx)), 'symmetric')
    else:
        outx = im

    if(ny % size != 0.0):
        resty = int(size - ny % size)
        out = np.pad(outx, ((0,resty), (0,0)), 'symmetric')
    else:
        out = outx

    return out

def threshold(im,th = None):
    """
    Binarize an image with a threshold given by the user, or if the threshold is None, calculate the better threshold with isodata
    Param:
        im: a numpy array image (numpy array)
        th: the value of the threshold (feature to select threshold was asked by the lab)
    Return:
        bi: threshold given by the user (numpy array)
    """
    if th == None:
        th = skimage.filters.threshold_isodata(im)
    bi = im
    bi[bi > th] = 255
    bi[bi <= th] = 0
    return bi


def edge_detection(im):
    """
    Detect the edges on a label image
    Param:
        im: (np.array) input image
    Return:
        contour: (np.array) output image containing the edges of the input image
    """

    contour = np.zeros((im.shape[0], im.shape[1]))
    vals = np.unique(im)

    for i in range(0,vals.shape[0]):
        a = np.zeros((im.shape[0], im.shape[1]))
        a[im == vals[i]] = 255

        dilated = skimage.morphology.dilation(a, selem=None, out=None)
        eroded = skimage.morphology.erosion(a, selem=None, out=None)
        edge = dilated - eroded

        contour = contour + edge

    contour[contour >= 255] = 255

    return contour


def split(im, size):
    """
    split an squared image with good dimensions (output of pad()) into tiles of shape size x size pixels
    Param:
        im: (np.array) input image
        size: (integer) size of the tiles
    Return:
        ims: (list of np.array) output tiles
    """

    nx = im.shape[1]
    ny = im.shape[0]

    k_max = int(nx / size)    # number of 256 slices along x axis
    l_max = int(ny / size)    # number of 256 slices along y axis

    ims = []

    for l in range(0, l_max):
        for k in range(0, k_max):
            frame = np.zeros((size,size))

            lo_x = size * k
            hi_x = size * k + size

            lo_y = size * l
            hi_y = size * l + size

            frame = im[lo_y:hi_y, lo_x:hi_x]

            # padding of the image to avoid border artefacts due to the convolutions
            # out = np.pad(frame, ((10,10), (10,10)), 'symmetric')

            ims.append(frame)
    return ims



def split_data(im, lab, ratio, seed):
    """split the dataset based on the split ratio."""
    # set seed
    np.random.seed(seed)

    index= np.arange(len(im))
    np.random.shuffle(index)
    num = int(ratio*len(index))
    im = im[index]
    lab = lab[index]

    im_tr = im[0:num,:,:]
    lab_tr = lab[0:num,:,:]

    im_te = im[num:,:,:]
    lab_te = lab[num:,:,:]

    return im_tr, lab_tr, im_te, lab_te



####################################
#                                  #
#  TRAIN AND TEST SETS GENERATORS  #
#                                  #
####################################

def generate_test_set(im, out_im_path):
  """
  Generate the testing set from raw data
  Param:
    im: (np.array) input image
    out_im_path: path to save the testing image

  Return:
    img_num: (integer) number of image produced
    resized_shape: (tupple) shape of the padded image
    original_shape: (tupple) shape of the original image
  """
  im = skimage.exposure.equalize_adapthist(im)

  original_shape = im.shape

  #resizing the input images
  padded = pad(im, 236)
  resized_shape = padded.shape

  # splitting
  splited = split(padded, 236)

  # padding the tiles to get 256x256 tiles
  padded_split = []
  for tile in splited:
    padded_split.append(np.pad(tile, ((10,10), (10,10)), 'symmetric'))

  img_num = len(padded_split)

  #saving the ouput images
  for i in range(len(padded_split)):
      name = str(i)
      io.imsave( out_im_path + name + ".png", img_as_ubyte(padded_split[i]) )

  return img_num, resized_shape, original_shape



def generate_tr_val_set(im_col, lab_col, tr_im_path, tr_lab_path, val_im_path, val_lab_path):
    """
    Randomly generate training, validation and testing set from a given collection of images and labels with a 50/25/25 ratio
    for detection of whole cells
    Params:
        im_col: (list of string) list of images (tiff movies) to include in the sets
        lab_col: (list of string) list of labels (tiff movies) to include in the sets
        tr_im_path: path to save training images
        tr_lab_path: path to save training labels
        val_im_path: path to save validation images
        val_lab_path: path to save validation labels
    Returns:
        tr_len: (integer) number of samples in the training set
        val_len: (integer) number of samples in the validation set
    """
    # reading raw data
    ims = []
    labs = []

    for im in im_col:
        print('im', im)
        ims = ims + read_im_tiff(im)

    for lab in lab_col:
        print('label',lab)
        labs = labs + read_lab_tiff(lab)

    ims_out = []
    labs_out = []


    for i in range( len(ims) ):
      # resizing images
      im_out = pad(ims[i], 236)

      # resizing and binarizing whole cell label
      
      threshold(labs[i],0)
      lab_out = pad(labs[i], 236)

      # splitting the images
      split_im = split(im_out, 236)
      split_lab = split(lab_out, 236)

      # discarding images showing background only
      # padding the tiles
      split_im_out = []
      split_lab_out = []
      for j in range( len(split_lab) ):
        if( np.sum(split_lab[j]) > 0.1 * 255 * 256 * 256 ):
          split_im_out.append(np.pad(split_im[j], ((10,10), (10,10)), 'symmetric'))
          split_lab_out.append(np.pad(split_lab[j], ((10,10), (10,10)), 'symmetric'))

      ims_out = ims_out + split_im_out
      labs_out = labs_out + split_lab_out

    # splitting the list into multiple sets
    im_tr, lab_tr, im_val, lab_val = split_data(np.array(ims_out),
                                                         np.array(labs_out),
                                                         0.75,
                                                         1)

    tr_len = im_tr.shape[0]
    val_len = im_val.shape[0]

    #saving the images
    for i in range(tr_len):
        io.imsave(tr_im_path + str(i) + ".png", img_as_ubyte(im_tr[i,:,:]))
        io.imsave(tr_lab_path + str(i) + ".png", (lab_tr[i,:,:]))

    for j in range(val_len):
        io.imsave(val_im_path + str(j) + ".png", img_as_ubyte(im_val[j,:,:]))
        io.imsave(val_lab_path + str(j) + ".png", (lab_val[j,:,:]))

    return tr_len, val_len

def reconstruct_result(tile_size, result, resized_shape, origin_shape):
    """
    Assemble a set of tiles to reconstruct the original, unsplitted image
    Param:
      tile_size: (integer) size of the tiles for the reconstruction
      result: (np.array) result images of the network prediction
      out_result_path: path to save the results
      resized_shape: (tuple) size of the image padded for the splitting
      origin_shape: (tuple) size or the raw images
    Return:
      out: (np.array) array containing the reconstructed images
    """
    nx, ny = int(resized_shape[1] / tile_size), int(resized_shape[0] / tile_size)
    out = np.empty(resized_shape)

    i = 0
    for l in range(ny):
      for k in range(nx):

        lo_x = tile_size * k
        hi_x = tile_size * k + tile_size

        lo_y = tile_size * l
        hi_y = tile_size * l + tile_size

        out[lo_y:hi_y, lo_x:hi_x] = result[i,:,:]

        i = i+1

    return out[ 0:origin_shape[0], 0:origin_shape[1] ]
