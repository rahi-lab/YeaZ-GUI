"""
Source of the code: https://github.com/mattminder/yeastSegHelpers
"""
import numpy as np

def cell_correspondance_frame(truth, pred):
    """
    Finds for one frame the correspondance between the true and the predicted cells.
    Returns dictionary from predicted cell to true cell.
    """
    keys = np.unique(pred)
    vals = np.empty(len(keys), dtype=int)
    for i, cell in enumerate(keys):
        v, c = np.unique(truth[pred==cell], return_counts=True)
        vals[i] = v[np.argmax(c)]
    return dict(zip(keys, vals))

def split_dict(cc):
    """
    Returns dictionary of cells in predicted image, to whether they were split unnecessarily
    (includes cells that were assigned to background)
    """
    truth = list(cc.values())
    pred = list(cc.keys())

    v, c = np.unique(list(truth), return_counts=True)
    split_truth = v[c>1]
    return dict(zip(pred, np.isin(truth, split_truth)))

def fused_dict(cc, truth, pred):
    """
    Returns dictionary of cells in predicted image to whether they were fused unnecessarily.
    """
    rev_cc = cell_correspondance_frame(pred, truth)
    rev_split_dict = split_dict(rev_cc)
    out = dict()
    for p in cc:
        out[p] = rev_split_dict[cc[p]]
    return out

def nb_splits(cc):
    """
    Counts the number of unnecessary splits in the predicted image (ignores background).
    """
    v, c = np.unique(list(cc.values()), return_counts=True)
    return (c[v>0]-1).sum()

def nb_fusions(cc, truth):
    """
    Counts number of cells that were fused.
    """
    true_cells = set(np.unique(truth))
    pred_cells = set(list(cc.values()))
    return len(true_cells - pred_cells)

def nb_artefacts(cc):
    """
    Number of predicted cells that are really background.
    """
    valarr = np.array(list(cc.values()))
    keyarr = np.array(list(cc.keys()))
    return (valarr[keyarr>0]==0).sum()

def nb_false_negatives(truth, pred):
    """
    Number of cells of mask that were detected as background in the prediction.
    """
    rev_cc = cell_correspondance_frame(pred, truth)
    return nb_artefacts(rev_cc)

def over_undershoot(truth, pred, cc, look_at):
    """
    Calculates average number of pixels that were overshot by cell. Uses look_at, which
    is a dict from pred cells to whether they should be considered (allows to exclude wrongly
    fused or split cells)
    """
    overshoot = 0
    undershoot = 0
    cellcount = 0

    for p in cc:
        if not look_at[p]:
            continue
        t = cc[p]
        if t==0 or p==0: # Disregard if truth or prediction is background
            continue
        cellcount += 1
        overshoot += (pred[truth!=t]==p).sum()
        undershoot += (truth[pred!=p]==t).sum()
    return overshoot/cellcount, undershoot/cellcount

def average_pred_area(pred, cc, look_at):
    """
    Calculates average predicted area of all considered cells
    """
    area = 0
    cellcount = 0
    for p in cc:
        if not look_at[p]:
            continue
        if p==0:
            continue
        cellcount += 1
        area += (pred==p).sum()
    return area/cellcount

def average_true_area(truth, cc, look_at):
    """
    Calculates average true area of all considered cells
    """
    area = 0
    cellcount = 0
    for p in cc:
        if not look_at[p]:
            continue
        t = cc[p]
        if t==0:
            continue
        cellcount += 1
        area += (truth==t).sum()
    return area/cellcount

def n_considered_cells(cc, look_at):
    """
    Calculates the number of considered cells
    """
    count = 0
    for p in cc:
        if not look_at[p]:
            continue
        if p==0 or cc[p]==0:
            continue
        count += 1
    return count

def quality_measures(truth, pred):
    """
    Tests quality of prediction with four statistics:
    Number Fusions:     How many times are multiple true cells predicted as a single cell?
    Number Splits:      How many times is a single true cell split into multiple predicted cell?
    Av. Overshoot:      How many pixels are wrongly predicted to belong to the cell on average
    Av. Undershoot:     How many pixels are wrongly predicted to not belong to the cell on average
    Av. true area:      Average area of cells of truth that are neither split nor fused
    Av. pred area:      Average area of predicted cells that are neither split nor fused
    Nb considered cells:Number of cells that are neither split nor fused
    """
    cc = cell_correspondance_frame(truth, pred)
    res = dict()

    # Get indices of cells that are not useable for counting under- and overshooting
    is_split = split_dict(cc)
    is_fused = fused_dict(cc, truth, pred)
    look_at = dict()
    for key in is_split:
        look_at[key] = not (is_split[key] or is_fused[key])

    # Result Calculation
    res["Number Fusions"] = nb_fusions(cc, truth)
    res["Number Splits"] = nb_splits(cc)
    res["Nb False Positives"] = nb_artefacts(cc)
    res["Nb False Negatives"] = nb_false_negatives(truth, pred)
    res["Average Overshoot"], res["Average Undershoot"] = over_undershoot(truth, pred, cc, look_at)
    res["Av. True Area"] = average_true_area(truth, cc, look_at)
    res["Av. Pred Area"] = average_pred_area(pred, cc, look_at)
    res["Nb Considered Cells"] = n_considered_cells(cc, look_at)
    return res
