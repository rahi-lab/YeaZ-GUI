"""
Source of the code: https://github.com/mattminder/yeastSegHelpers
"""
from scipy import ndimage as ndi
from skimage.feature import peak_local_max
from skimage.morphology import watershed

def segment(th, min_distance=10, topology=None):
    """
    Performs watershed segmentation on thresholded image. Seeds have to
    have minimal distance of min_distance. topology defines the watershed
    topology to be used, default is the negative distance transform. Can
    either be an array with the same size af th, or a function that will
    be applied to the distance transform.
    """
    dtr = ndi.morphology.distance_transform_edt(th)
    if topology is None:
        topology = -dtr
    elif callable(topology):
        topology = topology(dtr)

    m = peak_local_max(-topology, min_distance, indices=False)
    m_lab = ndi.label(m)[0]
    wsh = watershed(topology, m_lab, mask=th)
    return wsh
