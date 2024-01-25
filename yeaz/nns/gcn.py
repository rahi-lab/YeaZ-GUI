import tqdm
import json
from pathlib import Path
import h5py
import numpy as np
from bread.algo import tracking
from bread.data import SegmentationFile, Features, Segmentation
import logging


import importlib.resources as resources
# Access weight file
path_weights = resources.files('yeaz.nns.weights')


log = logging.getLogger(__name__)


def start_tracking(reader, fov_ind, time_value1, time_value2):
    seg = SegmentationFile.from_h5(reader.hdfpath).get_segmentation(f'FOV{fov_ind}')
    feat = Features(seg, nn_threshold=12)
    
    model_path = path_weights / 'results_fourier_10_and_f10_locality_False/_100KB_/2023-12-19_12:47:30'
    print('model_path: ' , str(model_path))
    with open(model_path / 'hyperparams.json') as file:
        hparams = json.load(file)

    # first initialize the model
    GCNTracker = tracking.AssignmentClassifier(
        tracking.GNNTracker,
        module__num_node_attr=hparams['num_node_attr'],
        module__num_edge_attr=hparams['num_edge_attr'],
        module__dropout_rate=hparams['dropout_rate'],
        module__encoder_hidden_channels=hparams['encoder_hidden_channels'],
        module__encoder_num_layers=hparams['encoder_num_layers'],
        module__conv_hidden_channels=hparams['conv_hidden_channels'],
        module__conv_num_layers=hparams['conv_num_layers'],
        module__num_classes=1,
    ).initialize()
    GCNTracker.load_params(model_path / 'params.pt')
    GCNTracker.module_.train(False)
    for t in tqdm.tqdm(range(time_value1, time_value2+1), desc='Tracking frames with GCN', leave=True):   
        # apply tracker if wanted and if not at first time
        try:
            temp_mask = CellCorrespondenceGCN(reader, GCNTracker, feat, t, fov_ind)
            feat.replace_frame_in_segmentation(t, temp_mask)
            reader.SaveMask(t, fov_ind, temp_mask)
        except e:
            print(e)
            break
    
    
def CellCorrespondenceGCN(reader,GCNTracker, feat, currentT, currentFOV):
    
    filemasks = h5py.File(reader.hdfpath, 'r+')
    
    if reader.TestTimeExist(currentT-1, currentFOV, filemasks):
        prevmask = np.array(filemasks['/{}/{}'.format(reader.fovlabels[currentFOV], 
                                                        reader.tlabels[currentT-1])])
        # A mask exists for both time frames
        if reader.TestTimeExist(currentT, currentFOV, filemasks):
            
            nextmask = np.array(filemasks['/{}/{}'.format(reader.fovlabels[currentFOV],
                                                            reader.tlabels[currentT])])    
            

            
            # run gcn
            cell_features = [
                'fourier',
                10,
                False,
                [
                    'area',
                    'r_equiv',
                    'r_maj',
                    'r_min',
                    'angel',
                    'ecc',
                    'maj_x',
                    'maj_y',
                    'min_x',
                    'min_y',
                ]
            ]
            
            edge_features = [
                "cmtocm_x",
                "cmtocm_y",
                "cmtocm_len",
                "cmtocm_angle",
                "contour_dist",
            ]
            # Make graphs
            
            ga = tracking.build_assgraph(
                tracking.build_cellgraph(
                    feat,
                    currentT-1,
                    cell_features=cell_features,
                    edge_features=edge_features,
                ),
                tracking.build_cellgraph(
                    feat,
                    currentT,
                    cell_features=cell_features,
                    edge_features=edge_features,
                ),
                include_target_feature=True)
                
            gat, *_ = tracking.to_data(ga)
            
            # prediction of trakcing

            assignments_dict = GCNTracker.predict_assignment(gat, assignment_method='modified_hungarian', return_dict=True)
            
            # make the output mask using this assignment
            out = nextmask.copy()
            newcell = np.max(prevmask) + 1
            for key, val in assignments_dict.items():
                # If new cell
                if val == -1:
                    val = newcell
                    newcell += 1
                
                out[nextmask==key] = val
                
        # No mask exists for the current timeframe, return empty array
        else:
            null = np.zeros([reader.sizey, reader.sizex])
            log.warn('No mask exists in FOV {} for the current timeframe {}, return empty array'.format(reader.fovlabels[currentFOV],reader.tlabels[currentT-1]))
            out = null
    
    else:
        # Current mask exists, but no previous - returns current mask unchanged
        if reader.TestTimeExist(currentT, currentFOV, filemasks):
            nextmask = np.array(filemasks['/{}/{}'.format(reader.fovlabels[currentFOV],
                                                            reader.tlabels[currentT])]) 
            out = nextmask
            log.warn('NCurrent mask exists, but no previous - returns current mask unchanged. FOV {} and Time {}'.format(reader.fovlabels[currentFOV],reader.tlabels[currentT-1]))
        # Neither current nor previous mask exists - return empty array
        else:
            log.warn('Neither current nor previous mask exists - return empty array. FOV {} and Time {}'.format(reader.fovlabels[currentFOV],reader.tlabels[currentT-1]))
            null = np.zeros([reader.sizey, reader.sizex])
            out = null
                
    filemasks.close()
    return out
